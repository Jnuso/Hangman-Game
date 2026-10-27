# Phase 5 — Manual testing

The automated integration checks are complete. Checked manual items reflect the
user's confirmed testing or review of their supplied screenshots. Remaining items
must be completed by observing the application, not inferred from automated
results. Record actual results and any screenshots for the report/demo.

Order requested by the user: finish offline recovery, server-restart recovery,
and the manual Docker setup check first; write the request/response explanation
at the end of Phase 5. All checks and the user's explanation are now complete;
the approved final explanation is recorded below.

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
- [x] Explain in your own words: input handler sends HTTP, Flask locates the game
  and calls the engine, Flask returns public JSON, JavaScript validates and renders.

## Setup and recovery review

- [x] Manually verify a clean dependency installation and startup in Docker using
  the documented Docker instructions, and record the actual result. The clean
  build, dependency check, container startup, and browser guesses at all three
  difficulties are verified from the user's output and screenshots.
- [x] In DevTools Offline, attempt a guess, restore Online, then Sync
  game. Verify the page recovers without consuming an extra life through a retry.
- [x] Stop and restart the local server; confirm the old game ID returns 404,
  the page prompts for a new game, and New game returns 201 with fresh state.

## Record your observations

- Date/browser/device: 2026-10-26; Google Chrome on Windows; local server at `127.0.0.1:5000` and the Linux Docker instance at `127.0.0.1:5056`, as shown in the user's screenshots and output.
- Cases completed: Gameplay and usability (all seven checks), confirmed by the user on 2026-10-26; Developer Tools network inspection and response/page comparison, manual Offline/Online/Sync recovery, server-restart recovery, and clean Docker installation/startup with all three difficulties, verified from supplied screenshots and output.
- Problems observed and reproduction steps:
- Evidence saved: creation [payload](evidence/manual-testing/2026-10-26/create-payload.png), [headers](evidence/manual-testing/2026-10-26/create-headers.png), and [response](evidence/manual-testing/2026-10-26/create-response.png); guess [payload](evidence/manual-testing/2026-10-26/guess-payload.png), [headers](evidence/manual-testing/2026-10-26/guess-headers.png), and [response with page update](evidence/manual-testing/2026-10-26/guess-response.png).
- Request/response explanation: Drafted by the user, revised with technical feedback, and approved by the user for commit/push on 2026-10-26; the final version appears below.

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

### Observed offline recovery

On 2026-10-26 (local date), the user selected Offline in Chrome DevTools and
clicked O. The [failed request and error page](evidence/manual-testing/2026-10-26/offline-error.png)
and [payload](evidence/manual-testing/2026-10-26/offline-payload.png) show the
attempted `{"letter":"o"}`, disabled guessing, and the Sync game control.
The game retained four lives, guessed letters `e, d, n`, misses `e, n`, and the
pattern `_ _ _ _ d`.

After the user restored No throttling and clicked Sync game, the
[headers](evidence/manual-testing/2026-10-26/sync-headers.png) show GET for the same
game returning 200 OK. Its [preview](evidence/manual-testing/2026-10-26/sync-preview.png)
and [full JSON response](evidence/manual-testing/2026-10-26/sync-response.png)
match the original pattern, history, misses, and four remaining guesses; status
remains `playing`, `word` is absent, and `o` was not recorded. The page matches the
response, the Sync control is hidden, and unused letter controls are enabled.
The Network list shows one recovery GET after the failed guess, with no repeated
guess POST. This verifies failure before server acceptance followed by recovery;
the separate accepted-guess/lost-response scenario has automated coverage.

### Observed server-restart recovery

On 2026-10-26 (local date), the user supplied the results of the guided server
restart check. A guess for F using the previous game's ID returned
[404 Not Found](evidence/manual-testing/2026-10-26/restart-old-game-headers.png).
The [request payload](evidence/manual-testing/2026-10-26/restart-old-game-payload.png)
shows `{"letter":"f"}` and the
[JSON error](evidence/manual-testing/2026-10-26/restart-old-game-response.png)
contains `code: "not_found"` with the instruction to start a new game. The page
shows "This game is no longer available", clears the old word and history, and
disables guessing.

The user then clicked New game. Its
[headers](evidence/manual-testing/2026-10-26/restart-new-game-headers.png) show
POST `/api/games` returning 201 Created; the
[payload](evidence/manual-testing/2026-10-26/restart-new-game-payload.png) selects
easy. The [response](evidence/manual-testing/2026-10-26/restart-new-game-response.png)
contains a different game ID, an all-masked four-letter word, six lives, empty
guess/miss histories, and `status: "playing"`, with no `word` field. The page
matches the fresh state, displays the start message, and enables letter controls.
This records recovery to a new game after the old in-memory game became unavailable.

### Manual Docker setup — Verified

The user supplied [PowerShell build output](evidence/manual-testing/2026-10-26/docker-clean-build.txt)
for `docker build --pull --no-cache -f Dockerfile.test -t hangman-manual-check .`.
Docker Desktop's Linux engine completed all nine build steps in 13.8 seconds.
The output shows the Python 3.14 base image being resolved, the requirements
installation running, and the image exported as `hangman-manual-check:latest`.

The user's [dependency-check and startup output](evidence/manual-testing/2026-10-26/docker-check-and-startup.txt)
records `docker run --rm hangman-manual-check python -m pip check` returning
"No broken requirements found." The next command starts Flask's normal `server`
app with debug off, the project mounted read-only at `/app`, and host port 5056
mapped to container port 5000 on localhost.

The [server log screenshot](evidence/manual-testing/2026-10-26/docker-server-log.png)
shows 200 responses for the page and CSS/JavaScript, followed by three new-game
201 responses and a successful 200 guess for each game. The browser screenshots
show [Easy](evidence/manual-testing/2026-10-26/docker-easy.png),
[Medium](evidence/manual-testing/2026-10-26/docker-medium.png), and
[Hard](evidence/manual-testing/2026-10-26/docker-hard.png) games at
`127.0.0.1:5056` after guessing A. Matching letters are revealed, A is marked used,
six lives remain, and there are no misses; Hard reveals both A occurrences.

This verifies clean Linux-container dependency installation, dependency
consistency, normal-app startup, asset delivery, and a browser guess at every
difficulty. Source files came from the existing working tree through the bind
mount. Container log timestamps use UTC on October 27; the user's local test
date is October 26. The development-server notice is expected for this local
check; production hosting remains Phase 6 work.

### Request/response explanation and observations — Approved final version

The user drafted these answers, reviewed the technical feedback, and approved
this revised version for commit/push on 2026-10-26.

1. **How the browser sends a guess**

   When a user clicks a letter or types one on the keyboard, JavaScript creates an object containing that letter, such as `{"letter":"a"}`. It uses `JSON.stringify()` to convert the object into JSON text. The browser then sends an HTTP **POST** request to `/api/games/<game_id>/guess`, with the JSON as the request body. The game ID identifies which game the guess belongs to.

2. **How Flask processes the request**

   Flask uses the HTTP method and URL to select the appropriate route. It finds the stored game using the game ID and uses `request.get_json()` to parse the JSON payload into a Python dictionary. Flask checks the request’s structure, then passes the letter to the game engine through `game.guess()`. The engine validates that the input is a single supported letter, has not already been guessed, and belongs to a game that is still active. It then records an accepted guess and determines its result. A valid guess can still be an incorrect letter and consume a chance.

3. **What the server returns**

   The server returns JSON containing the game ID, difficulty, current pattern, guessed letters, incorrect letters, remaining guesses, and game status. The pattern is a space-separated string, such as `"a _ _ _ a"`. If a correct letter appears multiple times in the word, every occurrence is revealed. The browser receives this public state while the hidden answer remains on the server during active gameplay. After either a win or a loss, the response includes the complete word so the page can display it.

4. **How JavaScript updates the page**

   JavaScript receives the response and uses `response.json()` to convert the JSON into usable JavaScript data. It validates the response’s expected structure before replacing its current public game snapshot. It then calls `render()` to update the displayed pattern, remaining chances, guess history, drawing, and keyboard buttons. Existing buttons change color and become disabled when used. JavaScript also displays messages based on the returned game status. The Python engine remains responsible for deciding the results.

5. **What the manual tests demonstrated**

   I used Chrome Developer Tools to inspect outgoing request payloads and incoming JSON responses. Creating a game returned **201 Created**, while successfully processed guesses returned **200 OK**. I compared the responses with the page to confirm that the displayed game state matched.

   During the offline test, I observed a failed POST request and the application’s recovery message. After restoring the connection, **Sync game** sent a GET request to retrieve the existing game’s current state. It did not resend the failed guess. The returned state confirmed that this particular failed guess had not been recorded or consumed a chance. Synchronization matters because some network failures can occur after the server accepts a guess but before the browser receives its response.

   Restarting the server created a new application instance with an empty in-memory game dictionary. The previous game ID therefore returned **404 Not Found**. Creating another game returned **201 Created** with a new ID and fresh state.

   Finally, the Docker check demonstrated successful dependency installation, a passing `pip check`, application startup inside the container, and browser gameplay at all three difficulty levels. Together, these checks verified that the application could run and process guesses in the container environment.

All Phase 5 local testing and the user's approved end-of-phase explanation are
complete. Public deployment remains Phase 6 work.
