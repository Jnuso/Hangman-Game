# Phase 5 — Manual testing still to perform

The automated integration checks are complete. The items below are deliberately
unchecked and must be completed by observing the application, not inferred from
automated results. Record actual results and any screenshots for the report/demo.

## Start normal gameplay

From the Hangman-Game repository root:

```powershell
.\.venv\Scripts\python.exe server.py
```

Open `http://127.0.0.1:5000` in Chrome. This uses normal random word lists.
The fixed-word server under `tests/browser/` is only for repeatable QA.

## Gameplay and usability

- [ ] Start games at Easy, Medium, and Hard; confirm the badge and word display.
- [ ] Use both letter buttons and the physical keyboard; inspect the displayed
  word, tried letters, misses, drawing, and remaining chances after each action.
- [ ] Complete a win and a loss. Confirm the answer and terminal message, then
  start another game without reloading.
- [ ] Use Tab/Shift+Tab and Enter/Space to reach and activate controls. Confirm
  visible focus and that choosing a difficulty does not guess a letter.
- [ ] Check a narrow window and your normal screen size for clipping, difficult
  text, and overlapping controls. Automated resizing does not replace this review.
- [ ] Start different games in two tabs; confirm their displays remain separate.
- [ ] Refresh a page. Expected current behavior: local controls reset; the old
  server game is not deleted, but the page does not automatically restore it.

## Chrome Developer Tools — Required evidence

- [ ] Open Developer Tools (F12), select Network, and filter to Fetch/XHR.
- [ ] Click New game and inspect `POST /api/games`: JSON difficulty request,
  201 response, generated game ID, and active state without a `word` field.
- [ ] Guess a letter and inspect `POST /api/games/{id}/guess`: JSON `letter`
  request, 200 response, updated pattern/history/lives/status.
- [ ] While the game is still playing, confirm the JSON response omits the answer.
- [ ] Compare the returned state with the page update. Save a representative
  screenshot or note for the report and demonstration.
- [ ] Explain in your own words: input handler sends HTTP, Flask locates the game
  and calls the engine, Flask returns public JSON, JavaScript validates and renders.

## Setup and recovery review

- [ ] Review the README setup steps in a fresh environment and record the actual
  installation/startup result. Clean Docker startup has automated evidence;
  a fresh native Windows setup is not claimed by those tests.
- [ ] If testing Offline in DevTools, attempt a guess, restore Online, then Sync
  game. Verify the page recovers without consuming an extra life through a retry.
- [ ] Stop the local server with Ctrl+C when finished. Note that restarting it
  discards active games; the page should offer a new game when its ID is missing.

## Record your observations

- Date/browser/device:
- Cases completed:
- Problems observed and reproduction steps:
- Evidence saved:
- Request/response explanation:

Phase 5 remains incomplete until the required manual review and evidence are done.
