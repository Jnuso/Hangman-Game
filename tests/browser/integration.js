async (page) => {
  const passed = [];
  const failures = [];
  const errors = [];
  let responsesChecked = 0;
  const onError = (error) => errors.push(error.message);
  page.on("pageerror", onError);
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const idle = (tab = page) => tab.waitForFunction(() => !document.querySelector("#new-game").disabled);
  const base = "http://127.0.0.1:5055";

  async function action(tab, suffix, click) {
    const response = tab.waitForResponse((r) => r.request().method() === "POST" && r.url().endsWith(suffix));
    await click();
    const result = await response;
    check(result.ok(), `Request failed: ${result.status()}`);
    const state = await result.json();
    await idle(tab);
    return state;
  }
  async function start(level = "easy", tab = page) {
    await tab.locator("#difficulty").selectOption(level);
    return action(tab, "/api/games", () => tab.locator("#new-game").click());
  }
  async function guess(letter, tab = page, physical = false) {
    return action(tab, "/guess", () => physical
      ? tab.keyboard.press(letter.toUpperCase())
      : tab.locator(`[data-letter="${letter}"]`).click());
  }
  async function assertDisplay(state, tab = page) {
    responsesChecked++;
    // One DOM snapshot avoids thousands of cross-process locator round trips.
    const view = await tab.evaluate(() => {
      const text = (id) => document.getElementById(id).textContent;
      return {
        word: document.getElementById("word").getAttribute("aria-label"),
        remaining: text("remaining"), difficulty: text("difficulty-badge"),
        drawing: document.getElementById("hangman").getAttribute("aria-label"),
        parts: document.querySelectorAll("[data-part]:not([hidden])").length,
        history: text("guessed"), incorrect: text("incorrect"), message: text("message-detail"),
        buttons: [...document.querySelectorAll("[data-letter]")].map((button) => ({
          letter: button.dataset.letter, disabled: button.disabled,
          correct: button.classList.contains("correct"),
          incorrect: button.classList.contains("incorrect"),
        })),
      };
    });
    const expectedLabel = "Word: " + state.pattern.split(" ").map((letter) => letter === "_" ? "blank" : letter.toUpperCase()).join(", ");
    check(view.word === expectedLabel, "Displayed pattern differs from API");
    check(view.remaining === String(state.remaining_guesses), "Displayed lives differ from API");
    check(view.difficulty === state.difficulty.toUpperCase(), "Difficulty differs from API");
    check(view.parts === state.incorrect_letters.length, "Drawing differs from API");
    check(view.drawing === `Hangman drawing: ${state.incorrect_letters.length} of 6 incorrect guesses`, "Drawing label differs from API");
    const history = state.guessed_letters.length ? state.guessed_letters.join(" · ").toUpperCase() : "None yet — a clean slate.";
    const wrong = state.incorrect_letters.length ? state.incorrect_letters.join(" · ").toUpperCase() : "None yet.";
    check(view.history === history, "History differs from API");
    check(view.incorrect === wrong, "Miss list differs from API");
    check(view.buttons.length === 26, "Alphabet keyboard is incomplete");
    for (const letter of "abcdefghijklmnopqrstuvwxyz") {
      const button = view.buttons.find((item) => item.letter === letter);
      check(Boolean(button), `Missing letter button ${letter}`);
      const used = state.guessed_letters.includes(letter);
      const wrong = state.incorrect_letters.includes(letter);
      check(button.disabled === (state.status !== "playing" || used), `Wrong disabled state for ${letter}`);
      check(button.correct === (used && !wrong), `Wrong correct class for ${letter}`);
      check(button.incorrect === wrong, `Wrong incorrect class for ${letter}`);
    }
    const fetched = await tab.request.get(`${base}/api/games/${state.game_id}`);
    check(fetched.status() === 200, "GET state failed after rendered action");
    check(JSON.stringify(await fetched.json()) === JSON.stringify(state), "Persisted API state differs from response");
    if (state.status === "playing") {
      check(!Object.hasOwn(state,"word"), "Playing API state exposes answer");
    } else {
      check(view.message.includes(state.word.toUpperCase()), "Terminal answer not displayed");
    }
  }
  async function scenario(name, work) {
    await page.unrouteAll({behavior:"ignoreErrors"});
    await page.goto(base);
    const errorCount = errors.length;
    try {
      await work();
      check(errors.length === errorCount, "Page runtime error");
      passed.push(name);
    } catch (error) { failures.push({name,error:error.message}); }
  }
  try {
    for (const [level, word] of [["easy","apple"],["medium","guitar"],["hard","rhythm"]]) {
      await scenario(`${level}: full win matches API after every action`, async () => {
        let state = await start(level);
        await assertDisplay(state);
        for (const [index,letter] of [...new Set(word)].entries()) {
          state = await guess(letter,page,index%2===1);
          await assertDisplay(state);
        }
        check(state.status === "won", "Expected winning outcome");
        const previousId=state.game_id;
        state=await start(level);
        check(state.game_id!==previousId,"Restart reused old game ID");
        await assertDisplay(state);
      });
      await scenario(`${level}: full loss matches API after every action`, async () => {
        let state=await start(level);
        await assertDisplay(state);
        const misses=[..."abcdefghijklmnopqrstuvwxyz"].filter((letter)=>!word.includes(letter)).slice(0,6);
        for(const letter of misses){state=await guess(letter);await assertDisplay(state);}
        check(state.status==="lost","Expected losing outcome");
        await assertDisplay(await start(level));
      });
    }
    await scenario("Two tabs keep separate games and displays", async () => {
      const first=await start();
      const other=await page.context().newPage();
      const otherErrors=[];
      const onOtherError=(error)=>otherErrors.push(error.message);
      other.on("pageerror",onOtherError);
      try {
        await other.goto(base);
        const second=await start("hard",other);
        check(first.game_id!==second.game_id,"Tabs share a game ID");
        await assertDisplay(await guess("z"));
        await assertDisplay(second,other);
        await assertDisplay(await guess("r",other),other);
        check(await page.locator("#remaining").textContent()==="5","Other tab changed first game's lives");
        check(otherErrors.length===0,"Second tab runtime error");
      } finally {other.off("pageerror",onOtherError);await other.close();}
    });
    await scenario("Reload resets the page but preserves server game", async () => {
      const first=await start();
      const changed=await guess("p");
      await page.reload();
      check(await page.locator(".letter-button:disabled").count()===26,"Reload retained active local controls");
      check(await page.locator("#word").getAttribute("aria-label")==="No game started","Reload state does not match documented behavior");
      const response=await page.request.get(`${base}/api/games/${first.game_id}`);
      check(JSON.stringify(await response.json())===JSON.stringify(changed),"Reload modified server state");
      const fresh=await start();
      check(fresh.game_id!==first.game_id,"New game reused prior ID after reload");
      await assertDisplay(fresh);
    });
    await scenario("Real browser offline and reconnect preserves game", async () => {
      const state=await start();
      try {
        await page.context().setOffline(true);
        await page.locator('[data-letter="z"]').click();
        await idle();
        check(await page.locator("#sync-game").isVisible(),"Offline guess has no recovery");
        check(await page.locator(".letter-button:disabled").count()===26,"Offline uncertain state allows guesses");
      } finally {await page.context().setOffline(false);}
      await page.locator("#sync-game").click();await idle();
      await assertDisplay(state);
      await assertDisplay(await guess("z"));
    });
  } finally {
    await page.context().setOffline(false);
    await page.unrouteAll({behavior:"ignoreErrors"});
    page.off("pageerror",onError);
  }
  const result={passed:passed.length,scenarios:passed,responsesChecked,failures,runtimeErrors:errors};
  if(failures.length)throw new Error(JSON.stringify(result));
  return result;
}
