async (page) => {
  // Chromium's actual accessibility tree catches hidden/missing text alternatives,
  // rather than accepting the presence of an aria-label as sufficient.
  const checks = [];
  const runtimeErrors = [];
  const trees = [];
  const onError = (error) => runtimeErrors.push(error.message);
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const idle = () => page.waitForFunction(() => !document.querySelector("#new-game").disabled);
  const label = (state) => "Word: " + state.pattern.split(" ")
    .map((letter) => letter === "_" ? "blank" : letter.toUpperCase()).join(", ");
  page.on("pageerror", onError);
  await page.goto("http://127.0.0.1:5055");
  const client = await page.context().newCDPSession(page);
  let description;

  async function action(suffix, perform) {
    const pending = page.waitForResponse((response) =>
      response.request().method() === "POST" && response.url().endsWith(suffix));
    await perform();
    const response = await pending;
    check(response.ok(), "Expected successful API action");
    const state = await response.json();
    await idle();
    return state;
  }
  async function start(level = "easy") {
    await page.locator("#difficulty").selectOption(level);
    return action("/api/games", () => page.locator("#new-game").click());
  }
  const guess = (letter) => action("/guess", () => page.locator(`[data-letter="${letter}"]`).click());

  async function inspect(expected, scenario, answer) {
    const dom = await page.locator("#word-description").evaluate((element) => ({
      text: element.textContent,
      hiddenAncestor: Boolean(element.closest('[hidden], [aria-hidden="true"]')),
      display: getComputedStyle(element).display,
      visibility: getComputedStyle(element).visibility,
      width: element.getBoundingClientRect().width,
      height: element.getBoundingClientRect().height,
    }));
    check(dom.text === expected, scenario + ": incorrect pattern text");
    check(!dom.hiddenAncestor && dom.display !== "none" && dom.visibility === "visible",
      scenario + ": text alternative is hidden from accessibility");
    check(dom.width <= 1 && dom.height <= 1, scenario + ": text alternative changes visual layout");
    check(await page.evaluate((original) => original === document.getElementById("word-description"), description),
      scenario + ": live region was replaced instead of updated");
    check(await page.locator("#word").getAttribute("aria-label") === null,
      scenario + ": generic visual container has a prohibited accessible name");
    const {root} = await client.send("DOM.getDocument");
    const {nodeId} = await client.send("DOM.querySelector", {nodeId:root.nodeId, selector:"#word-description"});
    const {node} = await client.send("DOM.describeNode", {nodeId});
    const {nodes} = await client.send("Accessibility.getFullAXTree");
    const region = nodes.find((entry) => entry.backendDOMNodeId === node.backendNodeId);
    check(region && !region.ignored, scenario + ": text alternative missing from accessibility tree");
    check(nodes.some((entry) => !entry.ignored && entry.role?.value === "StaticText" && entry.name?.value === expected),
      scenario + ": pattern is not exposed as real accessible text");
    check(region.properties?.some((property) => property.name === "live" && property.value.value === "polite"),
      scenario + ": pattern is not a polite live region");
    check(region.properties?.some((property) => property.name === "atomic" && property.value.value === true),
      scenario + ": pattern changes are not atomic");
    const visual = await client.send("DOM.querySelector", {nodeId:root.nodeId, selector:"#word"});
    const visualTree = await client.send("Accessibility.getPartialAXTree", {nodeId:visual.nodeId});
    check(visualTree.nodes[0].ignored, scenario + ": visual slots duplicate accessible text");
    if (answer) {
      check(nodes.some((entry) => !entry.ignored && entry.role?.value === "StaticText" &&
        entry.name?.value.includes("The word was " + answer)), scenario + ": terminal answer not accessible");
    }
    trees.push({scenario,text:expected,role:region.role.value,properties:region.properties,
      visualIgnored:visualTree.nodes[0].ignored});
    checks.push(scenario);
  }

  try {
    description = await page.locator("#word-description").elementHandle();
    check(description, "Missing accessible word description");
    await client.send("Accessibility.enable");
    await inspect("No game started", "Initial state has real accessible text");
    let state = await start();
    await inspect(label(state), "New game exposes all blanks");
    state = await guess("p");
    check(state.pattern === "_ p p _ _", "Repeated-letter fixture mismatch");
    await inspect(label(state), "Repeated correct letters are readable");

    await page.locator("#word-description").evaluate((element) => {
      window.patternTextChanges = 0;
      window.patternObserver = new MutationObserver(() => window.patternTextChanges++);
      window.patternObserver.observe(element, {childList:true,characterData:true,subtree:true});
    });
    state = await guess("z");
    check(await page.evaluate(() => window.patternTextChanges) === 0,
      "Busy/incorrect-guess renders reannounce an unchanged pattern");
    await page.evaluate(() => {
      window.patternObserver.disconnect();
      delete window.patternObserver;
      delete window.patternTextChanges;
    });
    await inspect(label(state), "Incorrect guess preserves text without redundant announcements");

    for (const letter of "ale") state = await guess(letter);
    check(state.status === "won", "Expected fixture win");
    await inspect(label(state), "Winning pattern and answer are accessible", "APPLE");
    state = await start("medium");
    check(state.pattern.split(" ").length === 6, "Medium fixture length mismatch");
    await inspect(label(state), "New game resets a completed pattern and word length");
    state = await start();
    for (const letter of "bcdfgh") state = await guess(letter);
    check(state.status === "lost", "Expected fixture loss");
    await inspect(label(state), "Losing pattern and answer are accessible", "APPLE");

    await start();
    const lostResponse = async (route) => { await route.fetch(); await route.abort("failed"); };
    await page.route("**/api/games/*/guess", lostResponse);
    await page.locator('[data-letter="p"]').click();
    await idle();
    check(await page.locator("#word-description").textContent() === "Word: blank, blank, blank, blank, blank",
      "Unconfirmed guess changed the accessible pattern before sync");
    await page.unroute("**/api/games/*/guess", lostResponse);
    const synced = page.waitForResponse((response) => response.request().method() === "GET" &&
      response.url().includes("/api/games/"));
    await page.locator("#sync-game").click();
    state = await (await synced).json();
    await idle();
    check(state.pattern === "_ p p _ _", "Sync did not retrieve the accepted repeated-letter guess");
    await inspect(label(state), "Sync updates the accessible pattern from server state");

    const missing = async (route) => route.fulfill({status:404,contentType:"application/json",
      body:JSON.stringify({error:{code:"not_found",message:"Game not found."}})});
    await page.route("**/api/games/*/guess", missing);
    await page.locator('[data-letter="z"]').click();
    await idle();
    await page.unroute("**/api/games/*/guess", missing);
    await inspect("No game started", "Missing game clears the previous accessible pattern");
    state = await start();
    await inspect(label(state), "New game after recovery exposes fresh blanks");
    check(runtimeErrors.length === 0, "Browser JavaScript runtime errors");
    return {passed:checks.length,checks,trees,runtimeErrors};
  } finally {
    await page.evaluate(() => {
      window.patternObserver?.disconnect();
      delete window.patternObserver;
      delete window.patternTextChanges;
    });
    await page.unrouteAll({behavior:"ignoreErrors"});
    page.off("pageerror", onError);
    await description?.dispose();
    await client.detach();
  }
}
