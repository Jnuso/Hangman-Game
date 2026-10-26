# Browser verification

`check.js` is a Playwright CLI `run-code` function, not a Playwright Test suite.
It drives the real page and API, asserting 43 gameplay, recovery, input, and
responsive-layout conditions. `fixture_server.py` supplies controlled words for
repeatable win/loss checks: easy `apple`, medium `guitar`, hard `rhythm`. These
fixtures are only for QA; normal play uses the project's real word lists.

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
device, screen-reader, or cross-browser certification. Request timeout handling
is implemented but its full 15-second elapsed-time path is not separately tested.
