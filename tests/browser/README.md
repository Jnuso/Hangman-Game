# Browser verification

`check.js` is a Playwright CLI `run-code` function, not a Playwright Test suite.
It drives the real page and API, asserting 43 gameplay, recovery, input, and
responsive-layout conditions. `fixture_server.py` supplies controlled words for
repeatable win/loss checks: easy `apple`, medium `guitar`, hard `rhythm`. These
fixtures are only for QA; normal play uses the project's real word lists.

`edge_cases.js` adds **22 scenarios** for malformed responses, keyboard/input
boundaries, failed sync, remote completion, timeout, and late-response recovery.
Both suites clean up listeners/routes so they can run sequentially in one page.

## Reproduce

Start Docker Desktop, build the dependency image using the command in
`TESTING.md`, and run this from the repository root (PowerShell):

```powershell
docker run --rm --name hangman-browser-qa --publish 127.0.0.1:5055:5000 --mount "type=bind,source=$($PWD.Path),target=/app,readonly" hangman-phase3-tests python tests/browser/fixture_server.py --host 0.0.0.0 --port 5000
```

In another terminal from the repository root, with Node/npm installed:

```powershell
New-Item -ItemType Directory -Path output/playwright -Force | Out-Null
npx --yes --package @playwright/cli playwright-cli -s=hangman-qa open http://127.0.0.1:5055 --headed
npx --yes --package @playwright/cli playwright-cli -s=hangman-qa --raw run-code --filename tests/browser/check.js
npx --yes --package @playwright/cli playwright-cli -s=hangman-qa --raw run-code --filename tests/browser/edge_cases.js
npx --yes --package @playwright/cli playwright-cli -s=hangman-qa close
```

The CLI needs a supported installed browser. The verified run used Google Chrome
on Windows with the Flask fixture server running in Linux Docker. Browser tool
setup can need permission to launch Chrome outside a restricted sandbox.

Stop the fixture server with Ctrl+C when done. Alternatively, for native local
execution, `.\.venv\Scripts\python.exe tests/browser/fixture_server.py` listens on
loopback port 5055; that native-server variation has not been verified here.

## What the run verifies

- Initial disabled controls; all three difficulties; both click and keyboard input.
- Correct repeated-letter reveal, incorrect guesses, drawing and lives updates.
- Duplicate/invalid keys ignored, complete wins/losses, restart without reload.
- Controls disabled during a held request, preventing overlapping actions.
- A guess accepted by the server whose response is intentionally dropped; Sync
  retrieves current state without repeating the guess.
- Simulated missing-game and failed-new-game responses with usable recovery.
- Select-control key input does not accidentally submit a guess; Enter activates
  New game.
- 375px and 320px layouts have no horizontal overflow; mobile buttons have usable
  height; reduced-motion mode remains usable.
- Successful API responses omit `word` while playing; no page JavaScript runtime
  errors occur.

Network errors and a 404 are deliberately injected, so corresponding browser
resource-error console entries are expected. They are distinct from JavaScript
runtime errors. The run returns JSON assertion results and saves desktop/mobile
screenshots under ignored `output/playwright/`.

This is Chromium desktop automation with resized viewports, not physical mobile
device, screen-reader, or cross-browser certification. Timeout scenarios advance
the real application timer by 15,001 milliseconds using Playwright's virtual
clock; they do not depend on a 15-second wall-clock sleep. The CLI scripts must
remain function expressions without a trailing semicolon, as required by run-code.
The timer approach follows the [official Playwright Clock documentation](https://playwright.dev/docs/clock).

## Edge-suite coverage

- Null/empty/malformed success state preserves the previous game and shows an error.
- Incorrect game IDs and terminal responses without answers cannot replace state.
- A malformed response after an accepted guess is reconciled by GET, not a retry.
- Creation endpoint 404 preserves an existing game; guess/sync 404 resets it.
- HTML gateway errors retain usable recovery controls and HTTP status handling.
- Error-message markup renders literally rather than creating HTML or executing.
- Failed sync stays retryable and keeps guessing disabled; restart remains usable.
- Another client's completed game becomes a terminal UI state after synchronization.
- Composition, modified/repeated/default-prevented keys, editable focus, and
  non-element event targets cannot trigger unintended guesses or runtime errors.
- A timed-out accepted guess can recover by sync or New game; late responses
  cannot overwrite the recovered state.

The edge suite returns a JSON summary on success and throws a detailed failure
report when a scenario fails. Inspect CLI output as well as process status:
tool-level errors can be reported in the CLI output independently of shell status.
