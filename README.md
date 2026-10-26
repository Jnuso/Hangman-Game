# Hangman Game — CSE 4095 Assignment 14

A browser-based Hangman game planned with an independent Python game engine, a Flask REST API, and an HTML/CSS/JavaScript interface.

Repository: https://github.com/Jnuso/Hangman-Game

## Current status

Phase 1 setup is complete. Phase 2 includes the game engine, word manager, three curated word lists, and 35 automated tests passing in a Python 3.14 Linux Docker container. The API, browser interface, and public deployment are not implemented. There is no runnable server yet.

See `TODO.md` for the accepted phased plan. Implement and verify one phase at a time.

## Requirements and scope

`ASSIGNMENT.md` defines the graded requirements. `SPECIFICATION.md` preserves the original, broader specification. The original roadmap and instructor conversation are preserved under `reference/`; their checked tasks and historical prompts do not describe this implementation's progress.

Required features include three difficulties, six allowed incorrect guesses, letter validation, win/loss detection, browser input, a changing Hangman drawing, testing, and deployment. The server will own the hidden answer and all game decisions. It will reveal the answer only after the game ends.

Terminal clients, bots, evaluation, scoring, leaderboards, replay, accounts, and multiplayer are outside this assignment's scope.

## Local development setup

Development uses **Python 3.14.3** on Windows and a project-local `.venv`. Flask is installed in that environment. The setup follows the [official Flask installation guidance](https://flask.palletsprojects.com/en/stable/installation/).

From PowerShell:

```powershell
git clone https://github.com/Jnuso/Hangman-Game.git
cd Hangman-Game
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

These commands use the environment's Python directly, so activating a PowerShell script is optional. They do not install packages globally.

If a restricted environment prevents Python from writing to its default temporary folder, use a local temporary directory for the setup process:

```powershell
New-Item -ItemType Directory -Path .local-tmp -Force | Out-Null
$env:TEMP = Join-Path (Get-Location) '.local-tmp'
$env:TMP = $env:TEMP
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The temporary directory and virtual environment are ignored by Git. These environment-variable changes apply only to the current PowerShell process.

Verify dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "from importlib.metadata import version; import flask; print('Flask', version('Flask'))"
```

For macOS/Linux, create the environment with `python3 -m venv .venv` and use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe` in subsequent commands. The Phase 2 core tests have passed in Linux Docker; a full macOS/Linux Flask installation has not been verified.

## Tests

The project uses Python's built-in `unittest`; it requires no additional test framework dependency.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
```

The suite currently contains **35 test methods**, with additional input combinations
covered by `subTest`. All passed in a Python 3.14 Linux Docker container. See
`TESTING.md` for the requirement coverage and Docker reproduction command. API
tests will follow with the API implementation; no HTTP or browser behavior has
been verified yet.

## Project layout

```text
Hangman-Game/
├── ASSIGNMENT.md
├── SPECIFICATION.md
├── TODO.md
├── README.md
├── DEVELOPMENT.md
├── TESTING.md
├── requirements.txt
├── .gitignore
├── game.py
├── word_manager.py
├── reference/
│   ├── TODO.original.md
│   └── cursor_transcript.md
├── static/       # Browser assets added in Phase 4
├── words/        # Three starter difficulty lists and provenance/format notes
└── tests/        # Tests added alongside implemented features
```

`game.py` and `word_manager.py` implement the Phase 2 core; `server.py` will follow in Phase 3. Empty directories contain `.gitkeep` placeholders so Git preserves the structure.

## Game core

`WordManager` loads all three word lists relative to its module and provides
`choose_word(difficulty)`. See `words/README.md` for list provenance, difficulty
choices, normalization, and invalid-file handling. The curated lists were created
for this implementation; they are not the instructor's original lists.

`HangmanGame(word, difficulty)` represents a single game. Its `guess(letter)`
method accepts a single ASCII letter, normalizes case, and returns updated public
state. Invalid guesses, duplicates, and guesses after completion raise dedicated
`ValueError` subclasses before changing the history. Correct guesses reveal all
occurrences; only incorrect guesses consume one of six lives.

`to_dict()` constructs the state that a future API may return: `difficulty`,
`pattern`, `guessed_letters`, `incorrect_letters`, `remaining_guesses`, and
`status`. It adds `word` only after a win or loss. The future server must serialize
through this method rather than returning the object's internal attributes.
Neither module imports Flask. Phase 2 tests exercise these behaviors independently of a web server.

## Planned API and deployment

The API will provide `POST /api/games`, `GET /api/games/{game_id}`, and `POST /api/games/{game_id}/guess` using JSON. Request validation and HTTP status codes will be documented when implemented.

Render deployment is planned for Phase 6. The production server configuration, local startup command, and deployed HTTPS URL will be documented after implementation and verification.

## Development workflow

Review the next phase in `TODO.md`, implement its scope, run relevant checks, inspect the results, and update the checklist only after verification. Commit and push completed phases. Record representative prompts, validation, real challenges, and limitations in `DEVELOPMENT.md` for the final report.

The project is an independent repository inside the CSE4095 workspace. Run its Git commands from this folder. Do not commit credentials, virtual environments, or caches.
