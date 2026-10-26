# Hangman Game — CSE 4095 Assignment 14

A browser-based Hangman game planned with an independent Python game engine, a Flask REST API, and an HTML/CSS/JavaScript interface.

Repository: https://github.com/Jnuso/Hangman-Game

## Current status

Phase 1 prepares the development environment and repository. The game engine, word lists, API, browser interface, and public deployment are not implemented yet. There is no runnable server or game test suite at this stage.

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

For macOS/Linux, create the environment with `python3 -m venv .venv` and use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe` in subsequent commands. Those platforms have not yet been verified for this project.

## Tests

The project will use Python's built-in `unittest`; it requires no additional test framework dependency.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
```

At Phase 1 this discovers **zero tests**. That checks the discovery command only, not application behavior. Meaningful engine and API tests will be added with their implementation phases.

## Project layout

```text
Hangman-Game/
├── ASSIGNMENT.md
├── SPECIFICATION.md
├── TODO.md
├── README.md
├── DEVELOPMENT.md
├── requirements.txt
├── .gitignore
├── reference/
│   ├── TODO.original.md
│   └── cursor_transcript.md
├── static/       # Browser assets added in Phase 4
├── words/        # Difficulty lists added in Phase 2
└── tests/        # Tests added alongside implemented features
```

Source modules `game.py` and `word_manager.py` will be added at the repository root in Phase 2; `server.py` will follow in Phase 3. Empty directories contain `.gitkeep` placeholders so Git preserves the structure.

## Planned API and deployment

The API will provide `POST /api/games`, `GET /api/games/{game_id}`, and `POST /api/games/{game_id}/guess` using JSON. Request validation and HTTP status codes will be documented when implemented.

Render deployment is planned for Phase 6. The production server configuration, local startup command, and deployed HTTPS URL will be documented after implementation and verification.

## Development workflow

Review the next phase in `TODO.md`, implement its scope, run relevant checks, inspect the results, and update the checklist only after verification. Commit and push completed phases. Record representative prompts, validation, real challenges, and limitations in `DEVELOPMENT.md` for the final report.

The project is an independent repository inside the CSE4095 workspace. Run its Git commands from this folder. Do not commit credentials, virtual environments, or caches.
