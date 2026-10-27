# Development notes

These notes record our own process and evidence for the final report. Instructor transcript claims are not verification of this implementation.

## Phase 1 — Setup (October 25, 2026)

The reduced plan was reviewed and accepted before implementation. Preserved the supplied directions, specification, original TODO, and instructor transcript. Created tracked placeholders for `static/`, `words/`, and `tests/`; source modules will be introduced in their implementation phases.

Created a local virtual environment with Python 3.14.3, installed Flask 3.1.3, and pinned Flask and its installed dependencies in `requirements.txt`. Added Git exclusions and documented setup in README. Production hosting dependencies will be added in the deployment phase.

### Verification

- The virtual environment reports Python 3.14.3 and a prefix separate from the base interpreter.
- Flask imports and reports version 3.1.3.
- `python -m pip check` reports no broken requirements.
- The documented dependency installation command succeeds with the pinned requirements.
- `python -m unittest discover -s tests -p 'test_*.py' -v` runs successfully and reports **zero tests**. This is setup verification only; no game behavior has been tested or implemented yet.
- `git check-ignore` confirms exclusion of `.venv`, `.local-tmp`, `.env`, and Python cache files.
- The Git remote points to `https://github.com/Jnuso/Hangman-Game.git`.

### Challenge and resolution

The initial `venv` bootstrap failed because `ensurepip` could not write a bundled pip wheel in the sandbox's default temporary directory. Set `TEMP` and `TMP` for the setup process to the project-local `.local-tmp` directory and reran environment creation successfully. The directory is ignored by Git, and the README documents the workaround.

### Representative user prompts

- “ok here are the assignment directions before we begin look over each componet of this project and give me a rough overview before we continue any futher”
- “ok walk me through what we plan to do for this step”
- “ok that all makes sense and looks good lets begin”

### Limits at this phase

There is no game engine, word data, API, browser application, or deployment yet. No full application tests exist. Only the Windows development setup has been verified.

## Phase 2 — Implementation draft; testing deferred

The user requested implementation now and tests in the next chat. This supersedes
the plan's usual same-phase test-writing workflow for this work session. No test
files were created and no engine behavior, data checks, or test commands were run
during this implementation session. Phase 2 remains incomplete and its checklist
items remain unchecked pending verification. Commit/push awaits that verification.

Added `game.py` with a UI-independent `HangmanGame`, six lives, normalized ASCII
guesses, duplicate/invalid/finished-game errors, derived pattern and status, and
explicit public-state serialization. Returned history lists are copies so callers
cannot change game history through a serialized response.

Added `word_manager.py` with module-relative file loading, supported-difficulty
validation, UTF-8/BOM handling, normalization, deduplication, clear file/line errors,
and random selection. Added manually curated AI-assisted starter lists intended
to contain 40 words per difficulty; their provenance and difficulty rationale are
recorded in `words/README.md`. No new dependencies were needed.

Static review checked the source against the planned rules, focusing on validation
before mutation, all occurrences of a letter being revealed, and explicit omission
of `word` in active-game serialization. This is not evidence of passing tests.

### Next-chat testing handoff

- Test word normalization, duplicate removal, blank lines, BOM, invalid entries,
  missing/empty/unreadable files, default paths, and all supported difficulties.
- Check the bundled lists, intended entry counts, and difficulty selection.
- Test correct and incorrect guesses, repeated letters, uppercase guesses, invalid
  input types, Unicode, duplicates, win/loss boundaries, and post-game rejection.
- Verify rejected guesses leave state unchanged, histories cannot be mutated via
  returned lists, and the answer is omitted while playing and revealed at the end.
- Resolve findings, record actual test evidence, update the Phase 2 checklist, and
  commit/push only after verification.

## Phase 2 — Test implementation and verification

After reviewing code-reading methods and test-case/edge-case concepts, the user
authorized creating the tests. Added 35 unittest methods: 18 for the engine and
17 for normalization, word files, resources, and word-to-game integration.
`subTest` covers multiple inputs inside several methods. `TESTING.md` maps the
requirements to representative checks and gives reproduction commands.

Executed the full suite in `python:3.14-slim` with a read-only project mount and
network disabled. Result: **35 tests passed, exit code 0**. The tests required no
changes to production modules. No Flask, browser, or deployment checks were run;
those components have not been implemented yet.

The coding worker initially rejected this project path because it is outside its
configured roots; it also could not access Docker while Docker Desktop was off.
Started Docker Desktop and used an isolated, explicitly supplied source snapshot
for independent worker review. The main suite ran directly inside Docker after
allowing access to the engine outside the sandbox; no host Python test run was
substituted for Docker verification.

The independent review worker did not finish: its first attempt hit a provider
rate limit, and a resumed attempt hit a provider timeout. Its result contained no
usable review or passing test evidence, so no worker artifacts were integrated.
The 35-test passing result above comes from the primary agent's direct Docker run,
not from that incomplete worker job. Phase 2 implementation and tests were
committed and pushed as `bb6743d`.

## Phase 3 — Flask REST API

Implemented `server.py` with an application factory, per-app in-memory game
storage, UUID4 game IDs, and a lock around shared reads/updates. Added the three
required create/retrieve/guess routes. All state is returned through the engine's
public serializer. Creation accepts only `difficulty`; guesses accept only
`letter`. The server rejects attempts to supply answers or override state.

Documented the API contract in `API.md`, including JSON request/error shapes,
201/200 successes, 400/404/405/409/413/415 errors, normalization, request size,
error precedence, no-store responses, Location headers, and storage limits.
Default HTTP errors retain their headers while returning JSON. Static serving
is disabled until browser implementation, preventing word/source-file exposure.
Local `python server.py` binds to loopback on port 5000 with debug disabled.

Added 21 API/live-HTTP unittest methods. Full Docker run: **56 tests passed,
exit code 0**, using Python 3.14 and pinned Flask 3.1.3 dependencies. Tests include
all difficulties, full wins/losses, validation failures without mutation, unknown
IDs, app/game isolation, concurrent duplicate requests, answer omission/reveal,
HTTP method headers, size limits, and inaccessible resource/source paths.

The live HTTP test starts a real loopback server and uses urllib requests to play
complete winning and losing games. A separate temporary container bound to an
ephemeral Windows localhost port was exercised with PowerShell: creation returned
201, active GET omitted `word`, and a complete losing game ended at zero lives
with `word` present. The temporary container was removed. Dockerfile.test makes
the dependency-equipped test image reproducible without new Python dependencies.

The initially available older test image had Python 3.12 and lacked Flask; built
a dedicated Python 3.14 image from pinned project requirements instead. No host
Python test execution was substituted for Docker verification.

Attempted a focused independent coding-worker review using an isolated supplied
source snapshot because this repository is outside worker roots. It hit provider
HTTP 429 and returned no review or verified tests. Inspected the failed result;
none of its artifacts were applied. All passing evidence above is from the main
suite and smoke check, not that worker.

Limitations: browser UI and cloud hosting remain future phases. Games are not
persistent, automatically expired, authenticated, or shared between processes.
Use one worker for this in-memory design. Native Windows Python API execution
has not been verified; the HTTP smoke client ran on Windows against Linux Docker.

### Phase 3 follow-up — Edge cases and race conditions

At the user's request, extended API coverage before the code walkthrough. Added
11 tests and upgraded the two-request duplicate test to eight synchronized
same-letter/case-variant requests. Barrier-based starts replace the previous
unsynchronized submission; each thread has its own Flask client.

Added races at the final life and winning transition, distinct-guess accounting,
read/write snapshot consistency, parallel creation, and invalid-versus-valid
requests. Added exact-size boundary checks, invalid encoding/trailing JSON,
accepted JSON media types, error cache headers, and last-life rejection behavior.

Full Docker suite: **67 tests passed, exit code 0**. No production-code changes
were needed. Tests accept either valid serial processing order and check final
state invariants; they do not claim exhaustive scheduling coverage or test
multi-process shared storage. Documentation records the expanded cases.

## Phase 4 — Browser interface

Implemented HTML, CSS, and JavaScript under `static/`, served from Flask with `/`
as the entry page. The interface uses a paper/forest-green palette, responsive
layout, SVG drawing, difficulty selection, letter buttons, physical keyboard,
guess history, remaining chances, and win/loss messages. The browser renders API
state and never selects a word or determines correctness independently.

A busy flag and disabled controls serialize client requests. Used letters and
terminal states disable guessing. Fetch calls have a 15-second timeout. If a
guess response is lost, the interface blocks further guesses and offers Sync
game, which retrieves state using GET instead of resubmitting an uncertain guess.
Missing games prompt a restart. Errors, loading, and game outcomes use a polite
live status region; controls have visible focus and descriptive labels. Reduced
motion is respected, and guesses ignore input focused inside the difficulty
selector. All dynamic text is inserted with textContent.

Verification: **70 Python unittest methods passed** in Docker, including three
new page/asset delivery and traversal tests. **43 Chrome browser assertions
passed** through Playwright CLI against controlled server-side word lists.
Inspected 32 successful API responses for active answer omission; no page runtime
errors occurred. Expected resource errors were injected for recovery scenarios.
The browser walkthrough covered all difficulties, both input methods, complete
win/loss, drawing progression, restart without reload, pending controls, dropped
response after acceptance, synchronization recovery, missing-game and creation
failure, keyboard activation, reduced motion, and mobile widths 375px/320px.

Captured and visually inspected desktop and mobile screenshots under ignored
`output/playwright/`. Preserved the repeatable fixture server and CLI walkthrough
under `tests/browser/`; production word lists remain separate. Browser launch
initially failed inside the Windows sandbox; launching the isolated Playwright
browser with the required process access resolved the tooling issue.

The user specified GitHub-based deployment for Phase 6. No site registration or
public hosting was performed. Remaining limits include refresh not restoring the
active game, no physical mobile or other-engine coverage, no screen-reader audit,
and no independent elapsed-time assertion for the full fetch-timeout path. Phase 5
will perform the broader local audit and demonstration-oriented API inspection.

### Phase 4 follow-up — Edge-case review

The user requested stronger edge coverage before the walkthrough. Wrote five
targeted regressions first; all failed against the existing UI. Two malformed
success-response cases cleared or crashed game state; a creation-endpoint 404
discarded a current game; composition input submitted a guess; and a keyboard
event targeted at document caused `target.closest is not a function`.

Added response-envelope validation before state assignment, including expected
game identity on guess/sync. This validates renderer inputs without implementing
game rules. HTTP error parsing retains status even for HTML bodies. Missing-game
reset is scoped to guess/sync requests, preserving existing games when creation
fails. Keyboard handling now ignores composition/default-prevented events and
checks Element targets before using DOM element methods.

Expanded to 22 passing browser edge scenarios, including malformed fields,
missing terminal answers, wrong game IDs, lost/malformed accepted-guess responses,
error-message HTML escaping, sync retries/404, another client's win, editable and
modified-key input, and late responses following timeout recovery. The actual
15-second application timer is exercised using Playwright virtual time for both
Sync and New game recovery. No page runtime errors remained in the final runs.

The original browser walkthrough also revealed test pollution: its anonymous
response listeners stayed attached and tried to parse the edge suite's deliberate
null responses. Replaced them with named listeners and finally cleanup. Both
browser suites then passed sequentially: 43 original assertions plus 22 edge
scenarios. A formatting-only trailing semicolon in the CLI function expression
was corrected before final execution.

Added three asset-delivery edge tests. Full Docker suite passed **73 Python test
methods**, and Node syntax checks passed for the application and browser scripts.
Updated README, testing instructions, and checklist with current evidence. No
deployment work or Phase 5 completion was claimed in this follow-up.

## Phase 5 — Automated tests before manual review

The user asked for automated test cases before continuing hands-on testing. Added
four Python integration methods covering 240 controlled bundled-word API game
flows (120 wins and 120 six-miss losses), real `server.py` subprocess startup from
another working directory, static/API delivery, and actual restart behavior.
Selection is controlled for exhaustive word coverage; engine and HTTP validation
remain real. Subprocess tests skip if local port 5000 is occupied to avoid
modifying a separately running server. Full Docker result: **77 tests passed,
exit code 0, no skips**.

Added nine browser integration scenarios using the existing server-side fixtures.
Compared UI fields, all alphabet button states, drawing parts, public response
fields, and persisted GET state after gameplay actions at all three difficulties.
Included separate tab isolation, documented refresh behavior, and actual browser
Offline/Online recovery. Result: **9 scenarios passed with 51 response/display
comparisons**, no failures or runtime errors. The original 43 browser checks and
22 edge scenarios were rerun sequentially with this new suite.

No application code changes were required. Added `MANUAL_TESTING.md` with all
hands-on checks left unchecked, including the assignment-required Chrome Network
inspection and request/response explanation. Updated Phase 5 progress to
distinguish automated evidence from the user's pending manual review. Clean
process startup in Docker does not claim fresh native dependency installation.

The integration browser assertions collect a single DOM snapshot per response
instead of issuing thousands of per-button browser round trips. The optimized
script was reverified with the same nine passing scenarios and 51 comparisons.

## Phase 5 audit fix — Request bodies outside the shared lock

The code audit reproduced an availability bug: the guess endpoint held the
application-wide game lock while `request.get_json()` waited for client bytes.
Even a small stalled upload could therefore block state reads and guesses for
other games. The user reviewed the explanation and authorized the fix.

Added four focused tests using a paused WSGI input stream and explicit Events.
Before changing the endpoint, three tests failed because other requests could
not complete while the body was paused; the unknown-ID/no-body-read test passed.
The tests always release the paused body in finally before joining worker
threads, and use an independent Flask client per thread.

Changed the endpoint to check the ID briefly under the lock, parse the request
outside it, then reacquire the lock and retrieve the game again before applying
the guess and building its response. This preserves 404 precedence and ensures
delayed requests use current duplicate/finished-game state. The tests cover
unblocked reads, another game's guess, creation, a delayed final miss after a win,
a delayed duplicate, and unknown-ID rejection without reading the body.

The full Python 3.14 Docker suite passed **81 methods, no skips, exit code 0**.
An independent review of the test design found no actionable concerns. The
earlier Chrome rerun passed 43 walkthrough checks, 22 edge scenarios, and nine
integration scenarios; browsers were not rerun for this backend change.
Manual gameplay and supplied Developer Tools screenshots are now recorded in
`MANUAL_TESTING.md`, with six evidence images saved in the repository. The user's
own request/response explanation and recovery checks remain pending; the manual
clean-install/startup check is explicitly deferred until later in Docker.

A separate coding-workers backend review was attempted but stopped at a provider
rate limit (HTTP 429), returning no usable findings or test verification. No worker
artifacts were integrated; the 81-test result above comes from the direct Docker
run against this repository.

## Phase 5 completion — Manual verification and explanation

The user completed the offline/Sync and server-restart checks and supplied a
clean Docker build, dependency check, startup log, and browser guesses at every
difficulty. They drafted five answers explaining the request/Flask/JSON/browser
sequence, reviewed technical clarifications, and approved the final version.
The explanation and supplied evidence were committed and pushed in `49a8235`.
Phase 5 is complete; the earlier pending statuses above describe earlier runs.

## Phase 6 — Production preparation

The user approved beginning deployment from GitHub to Render and confirmed
Jack's workspace after connecting the Render plugin. The intended service uses
the Free plan, one instance, and manual deploys. No paid service or database is
needed. The public deployment and browser verification are still pending.

Added `.python-version` (3.14.3), a production requirements file (existing Flask
pins, Gunicorn 26.2.0, packaging 26.3), a shared Gunicorn configuration, a Render
Blueprint, a non-root production-check image, and a reusable real-HTTP smoke
script. Normal Windows development keeps its existing requirements file.
One worker preserves the in-memory game store; four threads allow overlapping
requests while the existing lock serializes game-state updates. `PORT` controls
the listening port, debug/reload stay off, and logs go to stdout/stderr.

Consulted official Render Blueprint/Python-version documentation, Gunicorn
settings, and PyPI release metadata. Validated the Blueprint against Render's
official JSON schema. The production image installed cleanly and passed
`pip check`; all 81 existing Python tests passed in Docker without skips.

The non-root startup check exposed Gunicorn's optional admin socket attempting
to create files under `/nonexistent`. Disabled that unused socket in the shared
configuration, rebuilt, and verified clean startup. The first smoke run also
exposed a logging mistake in the new checker (`Request.method` instead of
`Request.get_method()`); corrected it before the successful run.

The real Gunicorn server passed 54 HTTP requests, including complete rounds at
all three difficulties, validation, answer protection, and concurrent duplicate
guesses. A restart probe confirmed old-ID 404, fresh-game 201, debug false, and
UID 65534. Details and reproduction steps are in TESTING.md and README.

The coding-workers independent review was attempted with this project path but
returned `invalid_project` because it is outside that backend's configured
`CODING_AGENTS_ROOTS`. No findings, test verification, or artifacts came from that
worker. Direct Docker verification supplies the test evidence above.
