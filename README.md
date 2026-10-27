# Hangman Game — CSE 4095 Assignment 14

A browser-based Hangman game planned with an independent Python game engine, a Flask REST API, and an HTML/CSS/JavaScript interface.

Repository: https://github.com/Jnuso/Hangman-Game

## Current status

Phases 1–5 are complete. Automated checks pass: 81 Python tests,
43 browser walkthrough assertions, 22 browser edge scenarios, and 9 browser
integration scenarios. All 120 bundled words have controlled API win/loss coverage.
The playable interface supports all difficulties, mouse/keyboard guesses, an SVG
drawing, restart, and network recovery. Manual Phase 5 evidence and the approved
request/response explanation are in `MANUAL_TESTING.md`. Phase 6 production setup
has passed local Docker verification; the public deployment is still pending.

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

For macOS/Linux, create the environment with `python3 -m venv .venv` and use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe` in subsequent commands. Linux dependency installation, production startup, and the full test suite have passed in Docker. Native macOS installation has not been verified.

## Tests

The project uses Python's built-in `unittest`; it requires no additional test framework dependency.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
```

The suite currently contains **81 Python test methods**, with additional input combinations
covered by `subTest`. All passed in a Python 3.14 Linux Docker container. See
`TESTING.md` for the requirement coverage and Docker reproduction command. API
tests cover request validation, status codes, game isolation, answer disclosure,
concurrent duplicate guesses, complete games, and HTML/CSS/JavaScript delivery.
Slow-upload regressions also verify that request-body reads leave other games
usable and delayed guesses are checked against the latest game state.
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
├── Dockerfile.production
├── requirements.txt
├── requirements-production.txt
├── .python-version
├── gunicorn.conf.py
├── render.yaml
├── .gitignore
├── game.py
├── word_manager.py
├── server.py
├── reference/
│   ├── TODO.original.md
│   └── cursor_transcript.md
├── static/       # index.html, style.css, app.js
├── scripts/      # Real-HTTP deployment verification
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

`to_dict()` constructs the state returned through the API: `difficulty`,
`pattern`, `guessed_letters`, `incorrect_letters`, `remaining_guesses`, and
`status`. It adds `word` only after a win or loss. The server serializes
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

## Production setup and Render deployment

Public HTTPS URL: **pending deployment and verification**.

Render runs this repository as a Python Web Service. The checked-in `render.yaml`
records a Free service in Virginia, one instance, the `main` branch, and manual
deploys (`autoDeployTrigger: 'off'`). It can also be used to create a Blueprint.
The same settings can be entered when creating a Web Service directly:

| Setting | Value |
| --- | --- |
| Repository | `https://github.com/Jnuso/Hangman-Game` |
| Branch | `main` |
| Runtime | Python 3 |
| Root directory | Leave empty; this repository already has the app at its root |
| Python version | `3.14.3`, from `.python-version` |
| Build command | `python -m pip install -r requirements-production.txt && python -m pip check` |
| Start command | `gunicorn --config gunicorn.conf.py server:app` |
| Environment | `FLASK_DEBUG=0`, `PYTHONUNBUFFERED=1` |
| Scaling | One instance; one Gunicorn worker |
| Automatic deploys | Disabled; deploy reviewed changes manually |

`requirements-production.txt` includes the existing Flask dependencies and pins
Gunicorn 26.2.0 plus packaging 26.3. Normal Windows development continues to use
`requirements.txt`; Gunicorn runs on Linux in Render or Docker.

`gunicorn.conf.py` binds to `0.0.0.0` and Render's `PORT` (default 10000 locally).
One worker owns the in-memory game dictionary. Four threads handle overlapping
requests within that process; the existing lock protects game reads and updates.
The development reloader is disabled, and access/error logs go to the platform's
log streams. The optional Gunicorn admin socket is disabled because this app uses
HTTP only and its non-root test-container account has no writable home directory.
Flask debug mode is off.

To verify the production image locally in PowerShell:

```powershell
docker build -f Dockerfile.production -t hangman-production .
docker run --rm --name hangman-production --publish 127.0.0.1:5057:10000 hangman-production
```

Open `http://127.0.0.1:5057`. In a second PowerShell window at the repository root:

```powershell
docker run --rm --network container:hangman-production --mount "type=bind,source=$($PWD.Path)\scripts\check_deployment.py,target=/checks/check_deployment.py,readonly" hangman-production python /checks/check_deployment.py http://127.0.0.1:10000
```

The script creates its own games, exercises all three API endpoints and
difficulties, completes rounds, rejects invalid/duplicate/post-game guesses,
checks answer protection and assets, and submits two concurrent duplicate
requests. It can also check a deployed HTTPS URL by omitting the container
network option and replacing the URL. It does not restart the target service or
modify other players' games. `Dockerfile.test` remains the separate test-dependency
image; `Dockerfile.production` copies only runtime files and runs Gunicorn as a
non-root user.

Deployment verification must additionally check a real browser, a complete game
and New game, and public availability with the local check container stopped.
Record the actual public URL and results before marking Phase 6 complete.

Limitations: games disappear on process restarts, redeploys, or worker replacement.
One worker/instance is required until shared storage is introduced. Free Render
services spin down after 15 minutes without traffic and take time to wake up;
the page's existing missing-game recovery lets a player start another round.
Pushing to GitHub alone does not update this service while automatic deploys are
disabled; use Render's manual deploy action after reviewed runtime changes.

References: [Flask deployment on Render](https://render.com/docs/deploy-flask),
[Render Blueprint fields](https://render.com/docs/blueprint-spec),
[Python version selection](https://render.com/docs/python-version),
[Free service limits](https://render.com/docs/free), and
[Gunicorn settings](https://gunicorn.org/reference/settings/).

## Development workflow

Review the next phase in `TODO.md`, implement its scope, run relevant checks, inspect the results, and update the checklist only after verification. Commit and push completed phases. Record representative prompts, validation, real challenges, and limitations in `DEVELOPMENT.md` for the final report.

The project is an independent repository inside the CSE4095 workspace. Run its Git commands from this folder. Do not commit credentials, virtual environments, or caches.
