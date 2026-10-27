async (page) => {
  const passed = [];
  const failures = [];
  const runtimeErrors = [];
  const onError = (error) => runtimeErrors.push(error.message);
  page.on("pageerror", onError);
  const idle = () =>
    page.waitForFunction(() => !document.querySelector("#new-game").disabled);
  const check = (condition, message) => {
    if (!condition) throw new Error(message);
  };
  const start = async () => {
    const response = page.waitForResponse(
      (r) => r.request().method() === "POST" && r.url().endsWith("/api/games"),
    );
    await page.locator("#new-game").click();
    const data = await (await response).json();
    await idle();
    return data;
  };
  const snapshot = () =>
    page.evaluate(() => ({
      word: document.querySelector("#word-description").textContent,
      lives: document.querySelector("#remaining").textContent,
      history: document.querySelector("#guessed").textContent,
    }));
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const scenario = async (name, action) => {
    await page.unrouteAll({ behavior: "ignoreErrors" });
    await page.goto("http://127.0.0.1:5055");
    const beforeErrors = runtimeErrors.length;
    try {
      await action();
      check(
        runtimeErrors.length === beforeErrors,
        "Page JavaScript runtime error",
      );
      passed.push(name);
    } catch (error) {
      failures.push({ name, error: error.message });
    }
  };
  try {
    for (const payload of [null, {}]) {
      await scenario(
        `Malformed creation response ${JSON.stringify(payload)} preserves current game`,
        async () => {
          await start();
          const before = await snapshot();
          await page.route("**/api/games", (route) =>
            route.fulfill({
              status: 201,
              contentType: "application/json",
              body: JSON.stringify(payload),
            }),
          );
          await page.locator("#new-game").click();
          await idle();
          check(
            same(await snapshot(), before),
            "Previous game was replaced by invalid data",
          );
          check(
            await page
              .locator("#message")
              .evaluate((el) => el.classList.contains("error")),
            "Invalid response not reported",
          );
        },
      );
    }
    await scenario(
      "Creation endpoint 404 preserves existing game",
      async () => {
        await start();
        const before = await snapshot();
        await page.route("**/api/games", (route) =>
          route.fulfill({
            status: 404,
            contentType: "application/json",
            body: JSON.stringify({
              error: { message: "Endpoint unavailable." },
            }),
          }),
        );
        await page.locator("#new-game").click();
        await idle();
        check(
          same(await snapshot(), before),
          "Endpoint 404 incorrectly discarded existing game",
        );
        check(
          await page.locator('[data-letter="a"]').isEnabled(),
          "Existing game cannot continue",
        );
      },
    );
    await scenario(
      "Input-method composition key does not submit a guess",
      async () => {
        await start();
        let submissions = 0;
        const count = (request) => {
          if (request.url().endsWith("/guess")) submissions++;
        };
        page.on("request", count);
        try {
          await page
            .locator("body")
            .dispatchEvent("keydown", {
              key: "a",
              isComposing: true,
              bubbles: true,
            });
          await idle();
          check(submissions === 0, "Composition keystroke submitted a guess");
        } finally {
          page.off("request", count);
        }
      },
    );
    await scenario(
      "Document-targeted keyboard event does not crash",
      async () => {
        await start();
        await page.evaluate(() =>
          document.dispatchEvent(
            new KeyboardEvent("keydown", { key: "a", bubbles: true }),
          ),
        );
        await idle();
      },
    );

    for (const [field, value] of [
      ["guessed_letters", null],
      ["incorrect_letters", {}],
      ["pattern", null],
      ["remaining_guesses", "6"],
      ["status", "unexpected"],
      ["word", "apple"],
    ]) {
      await scenario(
        `Malformed ${field} in success response is rejected`,
        async () => {
          const state = await start();
          const before = await snapshot();
          const malformed = { ...state, [field]: value };
          await page.route("**/api/games", (route) =>
            route.fulfill({
              status: 201,
              contentType: "application/json",
              body: JSON.stringify(malformed),
            }),
          );
          await page.locator("#new-game").click();
          await idle();
          check(
            same(await snapshot(), before),
            "Invalid response replaced usable state",
          );
          check(
            (await page.locator("#message-detail").textContent()).includes(
              "unexpected",
            ),
            "Invalid response not explained",
          );
        },
      );
    }
    await scenario(
      "Malformed accepted-guess response recovers through sync",
      async () => {
        await start();
        const before = await snapshot();
        const handler = async (route) => {
          const response = await route.fetch();
          const state = await response.json();
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ ...state, pattern: null }),
          });
        };
        await page.route("**/api/games/*/guess", handler);
        await page.locator('[data-letter="z"]').click();
        await idle();
        check(
          same(await snapshot(), before),
          "Malformed response changed visible state",
        );
        check(
          await page.locator("#sync-game").isVisible(),
          "Uncertain accepted guess lacks sync",
        );
        await page.unroute("**/api/games/*/guess", handler);
        await page.locator("#sync-game").click();
        await idle();
        check(
          (await page.locator("#remaining").textContent()) === "5",
          "Sync lost accepted server guess",
        );
      },
    );
    await scenario(
      "Terminal response without an answer cannot crash rendering",
      async () => {
        const state = await start();
        const before = await snapshot();
        await page.route("**/api/games", (route) =>
          route.fulfill({
            status: 201,
            contentType: "application/json",
            body: JSON.stringify({
              ...state,
              status: "won",
              pattern: "a p p l e",
            }),
          }),
        );
        await page.locator("#new-game").click();
        await idle();
        check(
          same(await snapshot(), before),
          "Incomplete terminal state replaced current game",
        );
        check(
          await page
            .locator("#message")
            .evaluate((el) => el.classList.contains("error")),
          "Missing answer not reported",
        );
      },
    );
    await scenario(
      "Response from a different game cannot switch active game",
      async () => {
        const state = await start();
        const handler = async (route) => {
          const response = await route.fetch();
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              ...(await response.json()),
              game_id: "a".repeat(32),
            }),
          });
        };
        await page.route("**/api/games/*/guess", handler);
        await page.locator('[data-letter="z"]').click();
        await idle();
        check(
          await page.locator("#sync-game").isVisible(),
          "Mismatched game ID accepted",
        );
        await page.unroute("**/api/games/*/guess", handler);
        const responsePromise = page.waitForResponse(
          (r) =>
            r.request().method() === "GET" && r.url().endsWith(state.game_id),
        );
        await page.locator("#sync-game").click();
        await responsePromise;
        await idle();
        check(
          (await page.locator("#remaining").textContent()) === "5",
          "Sync did not retain original game ID",
        );
      },
    );
    await scenario(
      "HTML error responses retain recovery controls",
      async () => {
        await start();
        await page.route("**/api/games/*/guess", (route) =>
          route.fulfill({
            status: 502,
            contentType: "text/html",
            body: "<h1>Gateway unavailable</h1>",
          }),
        );
        await page.locator('[data-letter="z"]').click();
        await idle();
        check(
          await page.locator("#sync-game").isVisible(),
          "HTML gateway error lost sync",
        );
        check(
          (await page.locator(".letter-button:disabled").count()) === 26,
          "Uncertain guess allows more input",
        );
        check(
          await page.locator("#new-game").isEnabled(),
          "Gateway error blocks restarting",
        );
      },
    );
    await scenario("Error message markup is displayed as text", async () => {
      await start();
      const markup = '<img src=x onerror="window.edgeInjected=true">';
      await page.route("**/api/games/*/guess", (route) =>
        route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ error: { message: markup } }),
        }),
      );
      await page.locator('[data-letter="z"]').click();
      await idle();
      check(
        (await page.locator("#message-detail").textContent()).includes(markup),
        "Error message was not rendered literally",
      );
      check(
        (await page.locator("#message img").count()) === 0,
        "Error message created HTML",
      );
      check(
        await page.evaluate(() => window.edgeInjected !== true),
        "Error markup executed",
      );
    });
    await scenario(
      "Sync failure can be retried and missing sync game can restart",
      async () => {
        await start();
        const abort = (route) => route.abort("failed");
        await page.route("**/api/games/*/guess", abort);
        await page.locator('[data-letter="z"]').click();
        await idle();
        await page.unroute("**/api/games/*/guess", abort);
        const failure = (route) =>
          route.fulfill({
            status: 503,
            contentType: "application/json",
            body: JSON.stringify({ error: { message: "Unavailable" } }),
          });
        await page.route("**/api/games/*", failure);
        await page.locator("#sync-game").click();
        await idle();
        check(
          await page.locator("#sync-game").isEnabled(),
          "Failed sync cannot be retried",
        );
        check(
          (await page.locator(".letter-button:disabled").count()) === 26,
          "Failed sync unlocks uncertain guesses",
        );
        await page.unroute("**/api/games/*", failure);
        const missing = (route) =>
          route.fulfill({
            status: 404,
            contentType: "text/html",
            body: "Not found",
          });
        await page.route("**/api/games/*", missing);
        await page.locator("#sync-game").click();
        await idle();
        check(
          (await page.locator("#message-title").textContent()).includes(
            "no longer available",
          ),
          "HTML 404 did not clear missing game",
        );
        check(
          await page.locator("#sync-game").isHidden(),
          "Missing game still offers sync",
        );
        await page.unroute("**/api/games/*", missing);
        await start();
        check(
          await page.locator('[data-letter="a"]').isEnabled(),
          "Cannot restart after failed sync",
        );
      },
    );
    await scenario(
      "Game completed by another client is recovered through sync",
      async () => {
        const state = await start();
        for (const letter of "aple") {
          const response = await page.request.post(
            `http://127.0.0.1:5055/api/games/${state.game_id}/guess`,
            { data: { letter } },
          );
          check(
            response.status() === 200,
            "Other client could not finish game",
          );
        }
        await page.locator('[data-letter="z"]').click();
        await idle();
        check(
          await page.locator("#sync-game").isVisible(),
          "Finished-game conflict not recoverable",
        );
        await page.locator("#sync-game").click();
        await idle();
        check(
          (await page.locator("#message-title").textContent()).includes(
            "You found it",
          ),
          "Sync missed remote win",
        );
        check(
          (await page.locator(".letter-button:disabled").count()) === 26,
          "Synced terminal game allows guesses",
        );
      },
    );
    await scenario(
      "Modified repeated and already-handled keys do not guess",
      async () => {
        await start();
        let count = 0;
        const listener = (r) => {
          if (r.url().endsWith("/guess")) count++;
        };
        page.on("request", listener);
        try {
          for (const extra of [
            { ctrlKey: true },
            { altKey: true },
            { metaKey: true },
            { repeat: true },
          ]) {
            await page
              .locator("body")
              .dispatchEvent("keydown", { key: "a", bubbles: true, ...extra });
          }
          await page.evaluate(() => {
            const event = new KeyboardEvent("keydown", {
              key: "a",
              bubbles: true,
              cancelable: true,
            });
            event.preventDefault();
            document.body.dispatchEvent(event);
          });
          await idle();
          check(count === 0, "Ignored keyboard event submitted a guess");
        } finally {
          page.off("request", listener);
        }
      },
    );
    await scenario(
      "Input and contenteditable focus do not trigger guesses",
      async () => {
        await start();
        let count = 0;
        const listener = (r) => {
          if (r.url().endsWith("/guess")) count++;
        };
        page.on("request", listener);
        try {
          await page.evaluate(() => {
            const input = document.createElement("input");
            input.id = "edge-input";
            const editor = document.createElement("div");
            editor.id = "edge-editor";
            editor.contentEditable = "true";
            document.body.append(input, editor);
          });
          await page.locator("#edge-input").focus();
          await page.keyboard.type("a");
          await page.locator("#edge-editor").focus();
          await page.keyboard.type("p");
          await idle();
          check(count === 0, "Text entry submitted a game guess");
        } finally {
          page.off("request", listener);
        }
      },
    );
    for (const recovery of ["sync", "new game"]) {
      await scenario(
        `15-second timeout followed by ${recovery} ignores late response`,
        async () => {
          await page.clock.install();
          await page.reload();
          await start();
          let release, accepted, complete;
          const gate = new Promise((r) => {
            release = r;
          });
          const seen = new Promise((r) => {
            accepted = r;
          });
          const finished = new Promise((r) => {
            complete = r;
          });
          const handler = async (route) => {
            try {
              const response = await route.fetch();
              accepted();
              await gate;
              try {
                await route.fulfill({ response });
              } catch {
                /* The client has aborted. */
              }
            } finally {
              complete();
            }
          };
          await page.route("**/api/games/*/guess", handler);
          try {
            await page.locator('[data-letter="z"]').click();
            await seen;
            await page.clock.fastForward(15001);
            await idle();
            check(
              (await page.locator("#message-detail").textContent()).includes(
                "timed out",
              ),
              "Timeout not surfaced",
            );
            check(
              await page.locator("#sync-game").isVisible(),
              "Timeout lacks sync recovery",
            );
            check(
              (await page.locator(".letter-button:disabled").count()) === 26,
              "Timeout allows uncertain guesses",
            );
            if (recovery === "sync") {
              await page.locator("#sync-game").click();
              await idle();
              check(
                (await page.locator("#remaining").textContent()) === "5",
                "Timeout sync missed accepted guess",
              );
            } else {
              await start();
            }
            const before = await snapshot();
            release();
            await finished;
            await idle();
            check(
              same(await snapshot(), before),
              "Late response overwrote recovered state",
            );
            if (recovery === "new game")
              check(
                before.lives === "6",
                "New game was contaminated by old guess",
              );
          } finally {
            release();
            await finished;
            await page.unroute("**/api/games/*/guess", handler);
          }
        },
      );
    }
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
    page.off("pageerror", onError);
  }
  const result = {
    passed: passed.length,
    scenarios: passed,
    failures,
    runtimeErrors,
  };
  if (failures.length) throw new Error(JSON.stringify(result));
  return result;
}
