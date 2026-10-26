# Hangman Game — CSE 4095 Assignment 14

A browser-based Hangman game planned with an independent Python game engine, a Flask REST API, and an HTML/CSS/JavaScript interface.

Repository: https://github.com/Jnuso/Hangman-Game

## Current status

Phases 1–4 are complete. Phase 5 automated checks now pass: 77 Python tests,
43 browser walkthrough assertions, 22 browser edge scenarios, and 9 browser
integration scenarios. All 120 bundled words have controlled API win/loss coverage.
The playable interface supports all difficulties, mouse/keyboard guesses, an SVG
drawing, restart, and network recovery. Manual Phase 5 review remains pending;
see `MANUAL_TESTING.md`. Public deployment remains Phase 6 work.

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

The suite currently contains **77 Python test methods**, with additional input combinations
covered by `subTest`. All passed in a Python 3.14 Linux Docker container. See
`TESTING.md` for the requirement coverage and Docker reproduction command. API
tests cover request validation, status codes, game isolation, answer disclosure,
concurrent duplicate guesses, complete games, and HTML/CSS/JavaScript delivery.
There are also **43 browser walkthrough assertions, 22 edge scenarios, and 9 integration scenarios**; see `tests/browser/README.md` for
reproduction instructions and verification limits.

`tests/test_integration.py` plays controlled wins and six-miss losses for every
bundled word (240 game flows across two test methods), and verifies real server
startup/restart in subprocesses. Those process tests use port 5000 and skip when
it is already occupied, avoiding requests to an unrelated running local server.
The full verified Docker run had no skips. Browser integration compares the page
with 51 server response states, and checks two tabs, reload, and offline recovery.

## Project layout

```text
Hangman-Game/
├── ASSIGNMENT.md
├── SPECIFICATION.md
├── TODO.md
├── README.md
├── DEVELOPMENT.md
├── TESTING.md
├── API.md
├── Dockerfile.test
├── requirements.txt
├── .gitignore
├── game.py
├── word_manager.py
├── server.py
├── reference/
│   ├── TODO.original.md
│   └── cursor_transcript.md
├── static/       # index.html, style.css, app.js
├── words/        # Three starter difficulty lists and provenance/format notes
└── tests/        # Core/API/asset tests and browser QA fixtures
```

`game.py` and `word_manager.py` implement the core; `server.py` exposes it through Flask. Empty directories contain `.gitkeep` placeholders so Git preserves the structure.

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

## Play locally

```powershell
.\.venv\Scripts\python.exe server.py
```

Open `http://127.0.0.1:5000` in a browser. Select a difficulty and click New game.
Guess using the letter buttons or your keyboard. Used letters and finished games
disable guessing; New game starts another round without a page reload.

If a guess response is lost, use Sync game to retrieve the server's actual state
before continuing. A missing game prompts you to start another. Refreshing the
page currently returns to the initial screen rather than restoring a game.

Malformed responses cannot replace the current game. Failed creation leaves an
existing game available, while uncertain guesses require sync. Composition,
modified, repeated, and already-handled keyboard events are ignored. The browser
validates response structure and game identity; Flask still owns game decisions.

The development server listens on loopback with debug disabled.
Use `POST /api/games`, `GET /api/games/{game_id}`, and
`POST /api/games/{game_id}/guess`. See `API.md` for JSON examples, validation,
status codes, and PowerShell requests. The root `/` serves the browser page;
`/static/` serves only frontend assets, not word lists or source modules.

Games are in memory and disappear on restart. Each process has separate storage;
a lock protects concurrent requests within one process. Use one production worker
until shared storage is added. There is no automatic game expiration or login.

## Planned deployment

Phase 6 will deploy from this GitHub repository to a host capable of running Flask
(Render is the assignment's suggested option). Production configuration and the
public HTTPS URL will be documented then. `Dockerfile.test` is for repeatable
tests, not production hosting. No deployment was performed in Phase 4.

## Development workflow

Review the next phase in `TODO.md`, implement its scope, run relevant checks, inspect the results, and update the checklist only after verification. Commit and push completed phases. Record representative prompts, validation, real challenges, and limitations in `DEVELOPMENT.md` for the final report.

The project is an independent repository inside the CSE4095 workspace. Run its Git commands from this folder. Do not commit credentials, virtual environments, or caches.
