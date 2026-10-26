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
