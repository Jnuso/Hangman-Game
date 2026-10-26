# Test cases and results

Current result: **67 passing test methods** (18 engine, 17 word management, and
32 API/live HTTP). Earlier counts below describe the runs at those milestones.

The suite uses standard-library `unittest`, known answers for engine scenarios,
and temporary directories for file-loading scenarios. Tests use public behavior;
they do not inspect the engine's private word or history. The selection test
patches `random.choice` to inspect normalized candidates at that boundary.

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

## Verified Docker run

Docker Desktop must be running in Linux-container mode. From the repository root:

```powershell
docker run --rm --network none --mount "type=bind,source=$($PWD.Path),target=/app,readonly" --workdir /app --env PYTHONDONTWRITEBYTECODE=1 python:3.14-slim python -m unittest discover -s tests -p 'test_*.py' -v
```

The project is mounted read-only, test fixtures live in container temporary
storage, and the test container has no network access. The Python image must be
available locally or Docker must be able to pull it before the container starts.
No Flask or additional testing dependencies are needed for this core suite.

Observed result: **35 test methods passed** (18 engine methods and 17 word
normalization/loading/resource methods), with additional cases exercised using
`subTest`. No production-code changes were required by these tests.

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
