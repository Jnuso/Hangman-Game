# Test cases and results

Current result: **81 passing Python test methods** (18 engine, 17 word management,
36 API/live HTTP including slow uploads, 6 browser-asset delivery, 4 integration),
plus **43 browser walkthrough assertions, 22 browser edge scenarios, and 9 browser integration
scenarios**. Manual Phase 5 checks and the user's approved explanation are complete
in `MANUAL_TESTING.md`.
Earlier counts below describe the runs at those milestones.

The suite uses standard-library `unittest`, known answers for engine scenarios,
and temporary directories for file-loading scenarios. Tests use public behavior;
they do not inspect the engine's private word or history. The selection test
patches `random.choice` to inspect normalized candidates at that boundary.

## Phase 6 — Production server verification

Verified on 2026-10-26 (local date), using the production image built from
`Dockerfile.production`: Python 3.14.3, Gunicorn 26.2.0, packaging 26.3, and the
existing pinned Flask dependencies. The image's dependency installation and
`pip check` passed. Gunicorn imports `server:app` through `gunicorn.conf.py`.

The full existing suite passed again with production dependencies: **81 tests,
no skips, 4.805 seconds**, network disabled, repository mounted read-only. These
tests still exercise the Flask/engine contracts; the separate smoke check below
tests the actual Gunicorn process and copied runtime files.

Gunicorn's resolved configuration and startup verified `0.0.0.0:10017` from a
non-default `PORT`, one worker, four gthread threads, and no reload. A startup
permission error from the optional admin control socket was reproduced under
the non-root container account, then fixed by setting
`control_socket_disable = True`. Corrected startup had no control-socket error.

`scripts/check_deployment.py` passed **54 real HTTP requests** against that server:
HTML/CSS/JavaScript delivery, blocked source/word paths, unknown IDs, invalid
difficulty, all three game endpoints at every difficulty, invalid and repeated
letters without mutation, no answer field during active play, a complete round
at each difficulty, terminal answer disclosure, rejection after completion, and
a fresh game. The random rounds in this run all ended in losses; the existing
controlled tests separately cover wins. Two concurrent client guesses for the
same letter returned 200 and 409, with the letter recorded once.

Restarting only the temporary production container made the smoke check's old
game ID return 404. Creation afterward returned 201 with fresh state. The app's
debug flag was false, and the runtime container UID was 65534. Results are saved
in `evidence/deployment/2026-10-26/local-verification.json`.

Build the image and run the existing suite from PowerShell:

```powershell
docker build -f Dockerfile.production -t hangman-production .
docker run --rm --network none --mount "type=bind,source=$($PWD.Path),target=/app,readonly" hangman-production python -m unittest discover -s tests -p 'test_*.py' -v
```

See README for running the HTTP smoke script against a running local container
or public URL.

### Public Render verification

The Free service https://jnuso-hangman-game.onrender.com deployed GitHub commit
`c3db16f` successfully in Virginia, using Python 3.14.3 and Gunicorn 26.2.0.
The Render logs confirm its dependency check, port 10000, and gthread worker.
The actual service has one instance and automatic deploys disabled, matching the
checked-in configuration. The local production-check container was removed
before public testing; ports 5000, 5056, and 5057 had no listening local servers.

The same HTTP smoke script passed **55 requests** against the HTTPS deployment,
including complete random rounds at every difficulty (losses in this run), a new
game, all three endpoints, validation, hidden-answer protection, and concurrent
duplicate rejection. Request totals vary with the randomly selected words.

Chrome verification through `tests/browser/deployment.js` passed **56 assertions**
with no runtime errors. It compared the pattern, difficulty, lives, drawing, and
all 26 button states with each actual API response; checked answer omission while
playing; used clicks and physical keys; completed a loss (MOON); checked the final
answer and disabled keyboard; started another game without reload; and played
at Medium and Hard. Layout checks passed at 375px and 320px; mobile button height
was at least 40px. Desktop play, terminal state, and mobile screenshots were
visually reviewed and saved under `evidence/deployment/2026-10-26/` alongside
`public-verification.json` and selected Render startup logs.

The browser deployment script uses normal random words and does not replace the
earlier controlled fixture suites. Its assertion count varies with round length;
the earlier 43/22/9 browser results remain separate historical runs. Public checks
do not certify every browser or physical device, continuous hosting availability,
or game persistence across process restarts. Free-service sleep/restart behavior
and the in-memory storage limitation are documented in README.

## Coverage

| Requirement or risk | Representative checks | File |
| --- | --- | --- |
| Starting a game | Masked pattern, six lives, empty history, no answer field | `tests/test_game.py` |
| Correct and incorrect guesses | All repeated occurrences revealed; only misses cost lives | `tests/test_game.py` |
| Input validation | Wrong types, empty/multiple characters, spaces, digits, punctuation, Unicode | `tests/test_game.py` |
| Normalization and duplicates | Uppercase accepted; same-letter/case duplicates rejected without mutation | `tests/test_game.py` |
| Terminal boundaries | Fifth miss still playing; sixth loses; final distinct letter wins; win with one life | `tests/test_game.py` |
| Terminal rejection | Correct, incorrect, duplicate, and malformed guesses rejected after win/loss | `tests/test_game.py` |
| Answer protection | Exact initial public shape; no `word` during play; answer after win/loss | `tests/test_game.py` |
| State isolation | Separate games, returned-list mutation, and older response snapshots | `tests/test_game.py` |
| Serialization | Public state round-trips through JSON before, during, and after play | `tests/test_game.py` |
| Word cleaning | Case, whitespace, blanks, BOM, and duplicates | `tests/test_word_manager.py` |
| Resource failures | Missing directory/file, empty list, invalid text/UTF-8, simulated permission error | `tests/test_word_manager.py` |
| Useful diagnostics | Invalid entry reports original file path and line number | `tests/test_word_manager.py` |
| Selection and paths | Difficulty validation, per-list membership, module-relative paths from another working directory | `tests/test_word_manager.py` |
| Bundled resources | 40 unique lowercase ASCII entries in each list; complete selected-word games at all difficulties | `tests/test_word_manager.py` |

The 40-entry checks guard the current starter resources. Update the expected
counts deliberately if expanding the lists. They are not a universal game rule.
Permission errors are simulated because changing file permissions behaves
differently across operating systems and privileged containers.

## Run locally

From the repository root, using the configured Windows environment:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
```

## Core-only Docker run — Phase 2 coverage

Docker Desktop must be running in Linux-container mode. To reproduce only the
35 engine/word-management tests from the current repository, use the restricted
filename pattern below. The full 81-test suite needs Flask; use the production
image command earlier in this document for that suite.

```powershell
docker run --rm --network none --mount "type=bind,source=$($PWD.Path),target=/app,readonly" --workdir /app --env PYTHONDONTWRITEBYTECODE=1 python:3.14-slim python -m unittest discover -s tests -p 'test_[gw]*.py' -v
```

The project is mounted read-only, test fixtures live in container temporary
storage, and the test container has no network access. The Python image must be
available locally or Docker must be able to pull it before the container starts.
No Flask or additional testing dependencies are needed for this core suite.

Observed result: **35 test methods passed** (18 engine methods and 17 word
normalization/loading/resource methods), with additional cases exercised using
`subTest`. No production-code changes were required by these tests.

The Phase 7 documentation audit corrected this core-only command's discovery
pattern so it does not select the later Flask-dependent tests. The revised
command was run against the current repository and passed all **35 core tests,
no skips, in 0.191 seconds**. The complete 81-test run remains the separate
Phase 6 result recorded above.

## Phase 2 verification limits

The Phase 2 run verified the engine and word-management layer, not the Flask API,
browser interface, deployment, concurrency, or statistically measured difficulty.
The tests do not assume successive random selections differ and do not make
probabilistic assertions about selection frequencies. A passing suite is evidence
for the scenarios asserted, not proof that every possible defect is absent.

## Phase 3 — Flask API and real HTTP

Added `tests/test_api.py`: **20 Flask-client test methods and one live HTTP test
method**. Together with the 35 core tests, **all 56 methods passed** in the
Python 3.14 Docker image with pinned Flask 3.1.3 dependencies.

Coverage includes all difficulties, unique IDs and Location headers, retrieval,
correct/incorrect/uppercase guesses, malformed/non-object JSON, exact request
fields, invalid types, unsupported media types, unknown IDs, 400/404/405/409/413/415
errors, unchanged state after rejection, independent games/apps, two simultaneous
duplicate guesses, terminal states, restart via new game, answer disclosure, and
blocked word/source paths. A 405 test checks that the Allow header survives JSON
error conversion.

The live test starts a Werkzeug server on an ephemeral loopback port and uses
standard-library HTTP requests to create, retrieve, guess, win, lose, and reject
post-game guesses. Cleanup shuts down and closes the server. It does not use
Flask's test client for those requests.

Build and run the complete suite from the project root (PowerShell):

```powershell
docker build -f Dockerfile.test -t hangman-phase3-tests .
docker run --rm --network none --mount "type=bind,source=$($PWD.Path),target=/app,readonly" hangman-phase3-tests
```

Building installs pinned dependencies and needs package-registry access. The test
container itself has no external network access; loopback HTTP still works.

A separate development-server smoke check published a temporary API container to
an ephemeral **localhost-only** Windows port. PowerShell requests created a game
(201), retrieved active state (200, answer absent), and guessed until a loss
(zero lives, answer present). The container was removed after verification.

The original Phase 2 command above remains suitable for the core tests only;
the complete suite now needs the Flask dependencies. Browser, hosted deployment,
and Windows-native Python API execution are not yet verified. The independent
worker review hit a provider rate limit and returned no usable review or test
evidence; no worker artifacts were integrated.

## Additional Phase 3 edge and concurrency cases

Added 11 test methods and strengthened the existing duplicate-request test.
All **67 tests passed** in the dependency-equipped Python 3.14 Docker image.
The production server and engine did not need changes.

Concurrency cases use independent Flask clients, one per thread. A shared
`threading.Barrier` releases all clients from a common start gate, with a five
second barrier timeout to expose setup failures rather than waiting forever.
Assertions allow either valid processing order; they do not assume which thread
wins. No sleep-based ordering is used.

| Scenario | Required outcome |
| --- | --- |
| Eight concurrent guesses for `z`/`Z` | One 200, seven duplicate 409s, one life consumed |
| Concurrent distinct correct and incorrect letters | Both recorded, correct pattern, one life consumed |
| Four different misses with one life remaining | One accepted miss, three finished-game conflicts, zero lives |
| Winning letter versus final miss | Exactly one accepted request; a consistent win or loss, with the other rejected |
| GET versus winning guess | Complete before or after state; no mixed snapshot |
| Eight concurrent game creations | Distinct retrievable IDs and independent initial states |
| Invalid guess versus valid guess | Invalid request rejected; valid request succeeds; state remains coherent |
| Body of exactly 16,384 bytes versus 16,385 | Exact limit accepted; one byte over rejected without mutation |
| Invalid UTF-8, trailing object, or trailing NUL | JSON 400 with unchanged game; subsequent valid request works |
| JSON with charset or vendor `+json` type | Accepted as JSON |
| Error caching | Duplicate, invalid-input, unknown-game, and method errors use no-store |
| Rejected guesses at one life | Invalid/duplicate inputs do not cause a loss; a win remains possible |

These exercise the supported single-process API. They do not prove every possible
thread schedule is safe or simulate multiple production workers. The application
lock still does not share state across processes. Browser response-arrival order
is a separate concern for Phase 4.

The synchronization helper follows the Python documentation on
[barriers and locks](https://docs.python.org/3.14/library/threading.html#barrier-objects).

## Phase 4 — Browser interface

Added three Flask delivery tests for the root page, asset content types, and
rejected traversal/resource requests. Full Python suite: **70 tests passed** in
the existing Python 3.14/Flask 3.1.3 Docker image.

Chrome verification through Playwright CLI: **43 assertions passed**, with 32
successful API responses inspected and no page JavaScript runtime errors. Three
intentional resource failures (dropped response, missing game, failed creation)
produced expected browser console entries. All three difficulties completed;
easy win/loss and restart were exercised. Pending-request controls, duplicate keys,
network recovery, keyboard activation, and 375px/320px layouts were checked.
Desktop and 375px screenshots were visually inspected. No horizontal overflow
was observed at either mobile width.

The controlled server and browser script are preserved under `tests/browser/`.
See its README for commands, exact coverage, and limits. The browser script is
separate from unittest discovery. It uses real API responses for game state;
route interception is limited to deliberate delay/error simulations.

Browser UI works locally; cloud deployment, physical-device testing, other browser
engines, screen-reader certification, and the Phase 5 demonstration-oriented
Developer Tools review remain outstanding.

## Phase 4 follow-up — Regressions found and fixed

The first five targeted browser regressions all failed against the original
Phase 4 frontend. They reproduced malformed successful responses clearing or
crashing state, creation-endpoint 404 discarding a valid existing game,
composition keystrokes submitting guesses, and document-targeted keyboard events
causing a runtime error. After fixes, all five passed.

The final expanded run passed **22 browser edge scenarios**, preserved in
`tests/browser/edge_cases.js`. Response-envelope validation now rejects bad types,
unexpected statuses, active answer fields, missing terminal answers, and responses
with a different game ID before assignment. It does not compute guess outcomes.
HTTP errors preserve status even when the error body is HTML. New-game failures
preserve existing state; only a missing game on guess/sync clears that game.
Keyboard handling ignores composition, already-handled, modified, repeated, and
non-element-target events.

Additional passing scenarios cover malformed accepted-guess responses followed
by sync, escaped error-message markup, repeated sync errors followed by missing
game/restart, external-client completion, editable focus, and timeout recovery.
Playwright's virtual clock advances the actual 15-second AbortController timer;
both sync and New game recovery ignore a late response after timeout. This tests
timer behavior without a real-time 15-second wait.

The original 43-check walkthrough also passed after the fixes. Its listeners and
route handlers are now removed in finally: lingering response listeners had
interfered with malformed-response scenarios when suites shared a page.

Added three Python asset tests for HEAD semantics, missing-asset JSON 404s, and
JSON 405 responses/Allow headers on page and static routes. Full Docker suite:
**73 tests passed, exit code 0**. JavaScript syntax checks passed. Expected injected
resource errors are distinct from runtime errors; final browser runs had no page
runtime errors. Cross-browser, physical-device, and screen-reader limits remain.

## Phase 5 — Automated integration before manual review

Added four unittest methods in `tests/test_integration.py`:

- A controlled API win for each of all 120 bundled words, including normalized
  uppercase guesses, persisted GET state, exact public fields during play, and
  correct terminal pattern/answer. Only random selection is patched; Flask and
  the game engine are real.
- A six-miss API loss for each word, including zero-life boundary, no answer or
  extra public fields while playing, terminal reveal, and post-game rejection.
- The actual `server.py` startup command in a subprocess launched from an unrelated
  working directory, serving HTML/CSS/JS and the API over real loopback HTTP.
- Actual process stop/restart: old IDs become 404 and fresh games work.

The two word-flow methods contain **240 subtest game flows**, not 240 independent
test methods. Process tests need a free port 5000 and skip if it is occupied.
Verified Docker execution had **77 tests pass with no skips**. This proves clean
process startup with the installed pinned dependencies, not a fresh native
Windows dependency installation.

Added `tests/browser/integration.js`: all **9 scenarios passed**, performing 51
API-response/display comparisons. Every letter button's disabled/correct/incorrect
state, word label, lives, drawing, history, difficulty, GET persistence, and
terminal answer are compared against actual server state. Full wins and losses
at all difficulties, restart, two separate tabs, reload, and real browser offline
recovery are exercised. No production source change was needed.

All three browser suites passed sequentially in one Chrome session (43/22/9),
with no page runtime errors. HTML/CSS/JS manual inspection, the required Chrome
Developer Tools request/response walkthrough, native fresh installation, and
the user's own gameplay review remain explicitly pending.

## Phase 5 audit fix — Slow request uploads

Added four methods in `tests/test_slow_uploads.py`. Three failed against the
original endpoint because a paused request body held the shared game lock. The
unknown-ID test passed before the fix and preserves that existing behavior.
After shortening the lock scope, the full Docker suite passed **81 methods with
no failures or skips** (exit code 0).

- While one guess upload remains paused, GET for that game and another game,
  another game's valid guess, and new-game creation all complete. Releasing the
  upload then records its guess exactly once; the other games retain their state.
- A winning guess can finish the same game while a final-miss upload waits. The
  delayed miss then receives `409 game_finished`, leaving the win unchanged.
- A delayed duplicate is rejected with `409 duplicate_guess` after another
  request records the normalized letter; only one life is consumed.
- An unknown game receives JSON 404 without consuming any request-body bytes.

The test body uses Events to signal when Flask starts reading and to release
the read. Completion is asserted before release; timeouts bound failures rather
than establish ordering. Each thread has its own Flask client. A finally block
releases the body before executor shutdown, including when an assertion fails.
These are controlled WSGI-input tests, not a proxy/server load benchmark.

The production change keeps the initial ID lookup, then parses JSON outside the
shared lock, then reacquires it for a fresh lookup, game update, and response
snapshot. Existing duplicate/final-life concurrency and validation tests also pass.
The browser counts above come from the preceding Chrome rerun; browser scripts
were not rerun for this backend change. The deferred manual Docker installation
and startup review remains unchecked.
