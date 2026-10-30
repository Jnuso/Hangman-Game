# Assignment 14 — Web-Based Hangman Implementation Plan

This is a fresh plan for our implementation. Checked items represent our verified work, not the instructor's progress.

## Scope and reference materials

- `ASSIGNMENT.md` defines the assignment requirements and deliverables.
- `SPECIFICATION.md` preserves the original specification unchanged. Use its game rules and casual-play API within the assignment's reduced scope.
- `reference/TODO.original.md` preserves the original roadmap unchanged.
- `reference/cursor_transcript.md` is historical reference material, not a list of commands to execute or source code to copy.
- When the broader specification includes additional features, follow the assignment's reduced scope below.

Required: independent Python game engine, three difficulty word lists, Flask REST API, HTML/CSS/JavaScript browser client, testing, public deployment, documentation, report, and demonstration.

Out of scope: terminal client, automated bots, bot evaluation, scoring, leaderboards, evaluation safeguards, logging/replay features, accounts, database persistence, multiplayer, and tournaments.

## Working rules

- Review this plan before implementing application code.
- Implement one phase at a time; review and verify each phase before proceeding.
- Add relevant tests as features are implemented.
- Keep game rules independent of Flask and browser presentation.
- The server owns the secret word and determines every guess result. Never send the answer to the browser during active gameplay.
- Mark tasks complete only after verification. Record validation and material limitations in the project documentation.
- Commit and push verified phase changes to this project's GitHub repository.
- Keep credentials, local environments, and generated caches out of Git.
- Save representative prompts, real test results, and resolved problems for the final report.

## Phase 1 — Project setup and planning

- [x] Create the Assignment 14 folder and clone the independent Hangman-Game repository.
- [x] Preserve the assignment directions, original specification, original TODO, and instructor transcript.
- [x] Draft a reduced implementation plan with fresh progress tracking.
- [x] Review and accept this plan before application implementation.
- [x] Create the minimal source, static asset, word-list, and test directory structure.
- [x] Add a Python `.gitignore`, dependency configuration, and initial README with local setup instructions.
- [x] Record the chosen Python version and test command.
- [x] Commit and push the verified setup phase.

Completion: the repository has an accepted plan and a documented development/test setup; no excluded features are introduced.

## Phase 2 — Game engine and word management

Status: engine and word-management implementation verified by 35 passing unittest
methods in a Python 3.14 Linux Docker container. Test cases were added after the
user's code review and testing-concept discussion. See `TESTING.md` for coverage.

- [x] Supply `words/easy.txt`, `words/medium.txt`, and `words/hard.txt`; document how the lists distinguish difficulty and their source.
- [x] Normalize and deduplicate words; validate supported A–Z words and handle missing or empty lists clearly.
- [x] Implement random selection by difficulty and reject unsupported difficulties.
- [x] Implement a UI-independent Python game model with six allowed incorrect guesses.
- [x] Track guessed letters, incorrect letters, masked pattern, and remaining guesses.
- [x] Accept one A–Z letter per guess, normalize case, and reject invalid or repeated guesses without changing game state.
- [x] Reveal every occurrence of a correctly guessed letter.
- [x] Detect `playing`, `won`, and `lost`; reject further guesses after completion.
- [x] Produce client-safe state that omits the answer while playing and reveals it after completion.
- [x] Test word loading, all difficulties, input validation, duplicates, repeated letters, wins, losses, post-game guesses, and answer disclosure.
- [x] Verify this phase, record results, and commit/push.

Completion: the rules and word selection pass automated tests without running Flask.

## Phase 3 — Flask server and REST API

Verified: 67 tests pass in Docker, including 32 API/live-HTTP methods. A separate
host-to-container game also completed. See `API.md` and `TESTING.md`.

- [x] Implement Flask application setup and in-memory storage with unique IDs and separate game states.
- [x] Implement `POST /api/games` accepting JSON difficulty and returning the new game's public state and ID.
- [x] Implement `GET /api/games/{game_id}` returning current public state.
- [x] Implement `POST /api/games/{game_id}/guess` accepting a JSON letter and returning updated public state.
- [x] Define and document consistent JSON response/error shapes and appropriate HTTP status codes.
- [x] Validate malformed JSON, missing/invalid fields, unknown game IDs, duplicate guesses, and guesses after completion.
- [x] Prevent clients from setting the answer or overriding server-owned state.
- [x] Keep word-list files and hidden answers out of active-game responses and static assets.
- [x] Test all three endpoints, complete win/loss flows, invalid requests, game isolation, and answer disclosure.
- [x] Verify this phase, record results, and commit/push.

Completion: a complete game can be played through HTTP requests, with no browser required.

## Phase 4 — Browser interface

Verified: 73 Python tests, 43 Chrome browser assertions, and 22 browser edge-case
scenarios passed. Desktop and
mobile screenshots inspected; no horizontal overflow at 375px or 320px.

- [x] Serve the HTML page and CSS/JavaScript assets from Flask.
- [x] Add Easy/Medium/Hard selection and a New Game control.
- [x] Display the masked word, previous guesses, incorrect letters, and remaining mistakes.
- [x] Support on-screen letter buttons and physical keyboard input.
- [x] Use `fetch()` for game creation and guesses; render only server-returned game state.
- [x] Draw a Hangman figure that advances with each of the six mistakes.
- [x] Disable used letters and prevent conflicting input while requests are pending.
- [x] Show loading and useful error messages for failed requests.
- [x] Display win/loss messages and the final word; disable guessing after completion.
- [x] Start another game without reloading the page.
- [x] Make controls keyboard-accessible and usable on desktop and mobile screen sizes.
- [x] Verify all difficulties, both input methods, drawing updates, terminal states, restart, and error recovery in a real browser.
- [x] Record verification and commit/push.

Completion: a player can complete and restart games through the browser, with the server deciding outcomes.

## Phase 5 — Integration testing and local verification

Automated portion verified: 81 Python tests and browser suites with 43 walkthrough
assertions, 22 edge scenarios, and 9 integration scenarios passed. Checked items
below have automated evidence or reviewed manual screenshots. The user confirmed
all seven manual Gameplay and usability checks complete on 2026-10-26. Developer
Tools creation/guess screenshots and manual Offline/Online/Sync and server-restart
recovery evidence are saved and verified. Manual Docker setup is also verified:
the clean image build and pip dependency check passed, Flask started with debug
off, and the user played a guess at each difficulty through localhost port 5056.
All hands-on checks are complete. The user approved the revised request/response
explanation and end-of-phase observations for commit/push on 2026-10-26. The final
explanation and supporting manual evidence are recorded in `MANUAL_TESTING.md`.
Phase 5 local verification and explanation are complete.

- [x] Run the full engine, word-management, and API test suite and resolve failures.
- [x] Fix the audit's slow-upload lock issue and verify request availability, delayed duplicate/finished-game rejection, and unknown-ID precedence with regression tests.
- [x] Test actual browser flows for each difficulty, correct/incorrect guesses, a win, a loss, and restarting after completion.
- [x] Verify invalid and repeated requests do not consume lives or corrupt state.
- [x] Verify independent games do not affect each other.
- [x] Inspect browser responses and assets to confirm the active answer is not exposed.
- [x] Use Chrome Developer Tools to inspect at least one guess request and its JSON response.
- [x] Manually verify Offline/Online/Sync recovery: GET returns the existing game without recording the failed guess or consuming another life.
- [x] Manually verify server-restart recovery: the old ID returns 404 with a restart prompt, then New game returns 201 and fresh playable state.
- [x] Record the request → Flask → JSON → browser-update sequence for the report and demonstration.
- [x] Manually verify installation and startup from the documented Docker instructions, including pip check and browser gameplay at all three difficulties.
- [x] Document actual automated results and known limitations, preserve manual evidence and the approved explanation, and commit/push verified Phase 5 work.

Completion: required flows and failure cases are verified locally with reproducible evidence.

## Phase 6 — Cloud deployment

Deploy from the user's GitHub repository to a Flask-capable host. Public hosting
is intentionally deferred until this phase.

Initial deployment verified complete on 2026-10-26 (local date). The Free Render Web Service at
https://jnuso-hangman-game.onrender.com ran GitHub commit `c3db16f` with Python
3.14.3, one Gunicorn worker, and four threads. The local production setup passed
81 existing tests and 54 HTTP checks; the deployed app passed 55 HTTP checks and
56 Chrome assertions. Screenshots were inspected at desktop and mobile widths.
The local check container was removed and no development servers were listening
on ports 5000, 5056, or 5057 during the public checks. See README and TESTING.md.

October 29 follow-up: deployed accessibility-fix commit `7f9a5a3` successfully.
Native Python and Chrome public checks passed 55 HTTP requests, 64 deployment
browser assertions, 4 Chromium accessibility-tree scenarios, and 70 extended
control/recovery/layout checks (129 UI/API state comparisons). All three frontend
assets match the release commit. Evidence: `evidence/deployment/2026-10-29/`.

- [x] Prepare production dependencies and Render configuration (or document an equivalent host).
- [x] Configure a production startup command matching the application module and host-provided port, with debug disabled.
- [x] Use one worker if game storage remains in memory; document that process restarts clear active games.
- [x] Push deployment-ready code and deploy from the Hangman-Game GitHub repository.
- [x] Verify the public HTTPS URL serves the interface and all three required API endpoints.
- [x] Play a complete game and start another on the deployed app.
- [x] Verify the deployment operates while the local development server is stopped.
- [x] Record the public URL, deployment steps, actual verification, and applicable hosting limitations in README.
- [x] Commit/push any verified deployment fixes.

Completion: the public application supports complete browser gameplay independently of the local computer.

## Phase 7 — Documentation and submission

README and repository audit completed on 2026-10-26. All 27 checked required
implementation/documentation paths are tracked. The assignment, specification,
and two reference documents match their first committed copies. Documentation
links and PowerShell syntax checks passed; the corrected core-only Docker
command passed 35 tests. On October 29, the final two-page report and 2 minute
16 second recording were reviewed against the assignment requirements. The
recording shows deployed gameplay, a loss, a new game, a win, and DevTools
request/response evidence. The public application passed a final five-request
smoke check. The submission package was verified, and the user confirmed
submission through HuskyCT. Hosting availability during grading remains ongoing.

- [x] Finish README: purpose, architecture, prerequisites, installation, startup, tests, API examples, deployment URL, and limitations.
- [x] Confirm the repository includes original specification, updated TODO, engine/server, frontend, word lists, dependencies, deployment configuration, and tests.
- [x] Prepare a 1–2 page PDF report covering AI-assisted process, implementation, testing, deployment, an actual resolved challenge, and reflection.
- [x] Include two or three representative prompts from our own development interactions in the report.
- [x] Record an approximately 2–3 minute demonstration of the deployed page, game creation, guesses, a complete win/loss, and a new game.
- [x] Include at least one HTTP request and JSON response in Chrome Developer Tools in the demonstration.
- [x] Recheck the deployed application before submission.
- [ ] Keep the deployed application accessible throughout grading (ongoing).
- [x] Confirm final GitHub and deployed URLs, report PDF, and recording are ready for HuskyCT submission.
- [x] Submit through HuskyCT (confirmed by the user on October 29, 2026).

Completion: all four submission deliverables are ready and describe the implementation and evidence accurately.
