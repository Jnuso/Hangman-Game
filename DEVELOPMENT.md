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
