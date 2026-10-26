# Phase 2 test cases and results

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

## Limits

This verifies the engine and word-management layer, not the future Flask API,
browser interface, deployment, concurrency, or statistically measured difficulty.
The tests do not assume successive random selections differ and do not make
probabilistic assertions about selection frequencies. A passing suite is evidence
for the scenarios asserted, not proof that every possible defect is absent.
