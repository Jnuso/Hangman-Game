# Phase 5 — Manual testing

The automated integration checks are complete. Checked manual items reflect the
user's confirmed testing or review of their supplied screenshots. Remaining items
must be completed by observing the application, not inferred from automated
results. Record actual results and any screenshots for the report/demo.

## Start normal gameplay

From the Hangman-Game repository root:

```powershell
.\.venv\Scripts\python.exe server.py
```

Open `http://127.0.0.1:5000` in Chrome. This uses normal random word lists.
The fixed-word server under `tests/browser/` is only for repeatable QA.

## Gameplay and usability

- [x] Start games at Easy, Medium, and Hard; confirm the badge and word display.
- [x] Use both letter buttons and the physical keyboard; inspect the displayed
  word, tried letters, misses, drawing, and remaining chances after each action.
- [x] Complete a win and a loss. Confirm the answer and terminal message, then
  start another game without reloading.
- [x] Use Tab/Shift+Tab and Enter/Space to reach and activate controls. Confirm
  visible focus and that choosing a difficulty does not guess a letter.
- [x] Check a narrow window and your normal screen size for clipping, difficult
  text, and overlapping controls. Automated resizing does not replace this review.
- [x] Start different games in two tabs; confirm their displays remain separate.
- [x] Refresh a page. Expected current behavior: local controls reset; the old
  server game is not deleted, but the page does not automatically restore it.

## Chrome Developer Tools — Required evidence

- [x] Open Developer Tools (F12), select Network, and filter to Fetch/XHR.
- [x] Click New game and inspect `POST /api/games`: JSON difficulty request,
  201 response, generated game ID, and active state without a `word` field.
- [x] Guess a letter and inspect `POST /api/games/{id}/guess`: JSON `letter`
  request, 200 response, updated pattern/history/lives/status.
- [x] While the game is still playing, confirm the JSON response omits the answer.
- [x] Compare the returned state with the page update. Save a representative
  screenshot or note for the report and demonstration.
- [ ] Explain in your own words: input handler sends HTTP, Flask locates the game
  and calls the engine, Flask returns public JSON, JavaScript validates and renders.

## Setup and recovery review

- [ ] Manually verify a clean dependency installation and startup in Docker using
  the documented Docker instructions, and record the actual result. Deferred until
  later at the user's request. Existing automated Docker evidence does not complete
  this manual check or claim a fresh native Windows installation.
- [ ] If testing Offline in DevTools, attempt a guess, restore Online, then Sync
  game. Verify the page recovers without consuming an extra life through a retry.
- [ ] Stop the local server with Ctrl+C when finished. Note that restarting it
  discards active games; the page should offer a new game when its ID is missing.

## Record your observations

- Date/browser/device: 2026-10-26; Google Chrome on Windows; local server at `127.0.0.1:5000`, as shown in the user's screenshots.
- Cases completed: Gameplay and usability (all seven checks), confirmed by the user on 2026-10-26; Developer Tools network inspection and response/page comparison, verified from supplied screenshots.
- Problems observed and reproduction steps:
- Evidence saved: creation [payload](evidence/manual-testing/2026-10-26/create-payload.png), [headers](evidence/manual-testing/2026-10-26/create-headers.png), and [response](evidence/manual-testing/2026-10-26/create-response.png); guess [payload](evidence/manual-testing/2026-10-26/guess-payload.png), [headers](evidence/manual-testing/2026-10-26/guess-headers.png), and [response with page update](evidence/manual-testing/2026-10-26/guess-response.png).
- Request/response explanation: Pending the user's own explanation.

### Observed Developer Tools results

The creation request sent `{"difficulty":"easy"}` to `POST /api/games` and
returned 201 Created. Its response contained a generated game ID, a four-letter
masked pattern, empty guess history, six remaining guesses, and `status: "playing"`.
The response omitted `word`.

The next request sent `{"letter":"a"}` to that game's guess endpoint and returned
200 OK. The response recorded `a` in both guessed and incorrect letters, kept the
four-letter pattern masked, reduced remaining guesses to five, and remained
`playing` without a `word` field. The page matched: A appeared in the history and
misses, its button was marked used, five chances remained, and the first figure
part was drawn. A 200 response means the guess was processed successfully;
the incorrect-letter list identifies this guess as a miss.

Phase 5 remains incomplete until the required manual review and evidence are done.
