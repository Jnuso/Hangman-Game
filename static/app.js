/* Presentation and input only. All game decisions come from the Flask API. */
"use strict";

(() => {
  const byId = (id) => document.getElementById(id);
  const difficulty = byId("difficulty");
  const newGame = byId("new-game");
  const syncButton = byId("sync-game");
  const keyboard = byId("keyboard");
  let game = null;
  let busy = false;
  let needsSync = false;

  for (const letter of "abcdefghijklmnopqrstuvwxyz") {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "letter-button";
    button.textContent = letter.toUpperCase();
    button.dataset.letter = letter;
    button.setAttribute("aria-label", `Guess ${letter.toUpperCase()}`);
    button.addEventListener("click", () => guess(letter));
    keyboard.append(button);
  }

  function message(title, detail, kind = "") {
    byId("message").className = `message ${kind}`;
    byId("message-title").textContent = title;
    byId("message-detail").textContent = detail;
  }

  function render() {
    const playing = game?.status === "playing";
    newGame.disabled = busy;
    difficulty.disabled = busy;
    syncButton.hidden = !needsSync;
    syncButton.disabled = busy;
    byId("keyboard").setAttribute("aria-busy", String(busy));
    for (const button of keyboard.children) {
      const letter = button.dataset.letter;
      const used = game?.guessed_letters.includes(letter) ?? false;
      const wrong = game?.incorrect_letters.includes(letter) ?? false;
      button.disabled = busy || needsSync || !playing || used;
      button.classList.toggle("correct", used && !wrong);
      button.classList.toggle("incorrect", wrong);
      button.setAttribute(
        "aria-label",
        `${letter.toUpperCase()}${used ? (wrong ? ", incorrect" : ", correct") : ", not guessed"}`,
      );
    }
    const remaining = game?.remaining_guesses ?? 6;
    const misses = game?.incorrect_letters.length ?? 0;
    byId("remaining").textContent = remaining;
    byId("chance-label").textContent =
      remaining === 1 ? "chance remaining" : "chances remaining";
    byId("difficulty-badge").textContent = game
      ? game.difficulty.toUpperCase()
      : "READY TO PLAY";
    byId("hangman").setAttribute(
      "aria-label",
      `Hangman drawing: ${misses} of 6 incorrect guesses`,
    );
    document.querySelectorAll("[data-part]").forEach((part) => {
      part.toggleAttribute("hidden", Number(part.dataset.part) > misses);
    });
    [...byId("lives").children].forEach((life, index) =>
      life.classList.toggle("used", index >= remaining),
    );
    byId("guessed").textContent = game?.guessed_letters.length
      ? game.guessed_letters.join(" · ").toUpperCase()
      : "None yet — a clean slate.";
    byId("incorrect").textContent = game?.incorrect_letters.length
      ? game.incorrect_letters.join(" · ").toUpperCase()
      : "None yet.";
    const word = byId("word");
    let wordDescription = "No game started";
    word.replaceChildren();
    if (!game) {
      const placeholder = document.createElement("span");
      placeholder.className = "word-placeholder";
      placeholder.textContent = "Your next word awaits.";
      word.append(placeholder);
      byId("word-length").textContent = "Waiting for a word";
    } else {
      const letters = game.pattern.split(" ");
      for (const letter of letters) {
        const slot = document.createElement("span");
        slot.className = `letter-slot${letter === "_" ? " blank" : ""}`;
        slot.textContent = letter === "_" ? "_" : letter.toUpperCase();
        word.append(slot);
      }
      wordDescription =
        `Word: ${letters.map((letter) => (letter === "_" ? "blank" : letter.toUpperCase())).join(", ")}`;
      byId("word-length").textContent = `${letters.length} letters`;
    }
    // Keep a real text alternative outside the hidden visual slots. Avoid
    // announcing unchanged patterns when busy/recovery controls are rendered.
    const description = byId("word-description");
    if (description.textContent !== wordDescription) {
      description.textContent = wordDescription;
    }
  }

  function showGameMessage() {
    if (game.status === "won") {
      message(
        "You found it. Nicely done!",
        `The word was ${game.word.toUpperCase()}. Ready for another?`,
        "won",
      );
    } else if (game.status === "lost") {
      message(
        "Out of chances. There's always another word.",
        `The word was ${game.word.toUpperCase()}. Start a new game to try again.`,
        "lost",
      );
    } else {
      message(
        "A little closer with every letter.",
        `${game.remaining_guesses} ${game.remaining_guesses === 1 ? "chance" : "chances"} left. Pick a letter below or type A–Z.`,
      );
    }
  }

  function validateState(data, expectedId) {
    // Validate the response envelope before replacing usable state. Game rules
    // still belong to Flask; these checks protect the renderer's assumptions.
    const letters = (value) =>
      Array.isArray(value) &&
      value.every(
        (letter) => typeof letter === "string" && /^[a-z]$/.test(letter),
      );
    const valid =
      data !== null &&
      typeof data === "object" &&
      !Array.isArray(data) &&
      typeof data.game_id === "string" &&
      /^[a-f0-9]{32}$/.test(data.game_id) &&
      (expectedId === undefined || data.game_id === expectedId) &&
      ["easy", "medium", "hard"].includes(data.difficulty) &&
      typeof data.pattern === "string" &&
      /^[a-z_](?: [a-z_])*$/.test(data.pattern) &&
      letters(data.guessed_letters) &&
      letters(data.incorrect_letters) &&
      Number.isInteger(data.remaining_guesses) &&
      data.remaining_guesses >= 0 &&
      data.remaining_guesses <= 6 &&
      ["playing", "won", "lost"].includes(data.status) &&
      (data.status === "playing"
        ? !Object.hasOwn(data, "word")
        : typeof data.word === "string" && /^[a-z]+$/.test(data.word));
    if (!valid) {
      const error = new Error(
        "The server returned an unexpected game response. Try again.",
      );
      error.kind = "invalid_response";
      throw error;
    }
    return data;
  }

  async function request(path, body, expectedId) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(path, {
        method: body === undefined ? "GET" : "POST",
        headers:
          body === undefined ? {} : { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
        cache: "no-store",
      });
      let data;
      try {
        data = await response.json();
      } catch (error) {
        if (response.ok) {
          if (error.name === "AbortError") throw error;
          data = null;
        }
      }
      if (!response.ok) {
        const error = new Error(
          typeof data?.error?.message === "string"
            ? data.error.message
            : "The request could not be completed.",
        );
        error.status = response.status;
        throw error;
      }
      return validateState(data, expectedId);
    } finally {
      clearTimeout(timeout);
    }
  }

  function showRequestError(error, isGuess) {
    if (isGuess && error.status === 404 && game) {
      game = null;
      needsSync = false;
      message(
        "This game is no longer available.",
        "The server may have restarted. Start a new game to keep playing.",
        "error",
      );
    } else {
      if (isGuess && game) needsSync = true;
      const detail =
        error.name === "AbortError"
          ? "The request timed out. Check your connection and try again."
          : error.status || error.kind === "invalid_response"
            ? error.message
            : "Check your connection and try again.";
      message(
        isGuess ? "Let's check where we left off." : "Couldn't reach the game.",
        isGuess
          ? `${detail} Sync the game before guessing again, or start a new one.`
          : detail,
        "error",
      );
    }
  }

  async function startGame() {
    if (busy) return;
    busy = true;
    message("Finding your next word…", "Just a moment.");
    render();
    try {
      game = await request("/api/games", { difficulty: difficulty.value });
      needsSync = false;
      message(
        "A fresh word. A fresh start.",
        "Pick a letter below or use your keyboard. You've got six chances.",
      );
    } catch (error) {
      showRequestError(error, false);
    } finally {
      busy = false;
      render();
    }
  }

  async function guess(letter) {
    if (
      busy ||
      needsSync ||
      !game ||
      game.status !== "playing" ||
      game.guessed_letters.includes(letter)
    )
      return;
    busy = true;
    message(`Trying ${letter.toUpperCase()}…`, "Checking your letter.");
    render();
    try {
      game = await request(
        `/api/games/${game.game_id}/guess`,
        { letter },
        game.game_id,
      );
      showGameMessage();
    } catch (error) {
      showRequestError(error, true);
    } finally {
      busy = false;
      render();
    }
  }

  async function syncGame() {
    if (busy || !game) return;
    busy = true;
    message("Checking your game…", "Getting the latest state from the server.");
    render();
    try {
      game = await request(
        `/api/games/${game.game_id}`,
        undefined,
        game.game_id,
      );
      needsSync = false;
      showGameMessage();
    } catch (error) {
      showRequestError(error, true);
    } finally {
      busy = false;
      render();
    }
  }

  newGame.addEventListener("click", startGame);
  syncButton.addEventListener("click", syncGame);
  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (
      event.repeat ||
      event.isComposing ||
      event.defaultPrevented ||
      event.ctrlKey ||
      event.metaKey ||
      event.altKey ||
      !(target instanceof Element) ||
      target.isContentEditable ||
      target.closest("input,select,textarea")
    )
      return;
    if (/^[a-z]$/i.test(event.key)) {
      event.preventDefault();
      guess(event.key.toLowerCase());
    }
  });
  render();
})();
