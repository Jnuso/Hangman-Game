"""Flask API for server-owned, in-memory Hangman games."""

from threading import RLock
from uuid import uuid4

from flask import Flask, abort, jsonify, request, url_for
from werkzeug.exceptions import HTTPException

from game import DuplicateGuessError, GameFinishedError, HangmanGame, InvalidGuessError
from word_manager import WordManager, normalize_difficulty


def create_app(word_manager: WordManager | None = None) -> Flask:
    """Create an independent app; inject a word manager for controlled tests.

    Games last only for this process. A lock protects reads and updates within
    one process, but does not share games between production worker processes.
    """
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    manager = WordManager() if word_manager is None else word_manager
    games: dict[str, HangmanGame] = {}
    lock = RLock()

    def error_response(code: str, message: str, status: int):
        return jsonify(error={"code": code, "message": message}), status

    @app.errorhandler(HTTPException)
    def http_error(error):
        # Preserve HTTP headers such as Allow on a 405 response.
        response = error.get_response()
        response.data = app.json.dumps({"error": {
            "code": error.name.lower().replace(" ", "_"),
            "message": error.description,
        }})
        response.content_type = "application/json"
        return response

    @app.after_request
    def prevent_stale_state(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    def read_body(field: str) -> dict:
        if not request.is_json:
            abort(415, description="Send a JSON object with Content-Type application/json.")
        body = request.get_json()
        if not isinstance(body, dict) or set(body) != {field}:
            abort(400, description=f"JSON must contain exactly the '{field}' field.")
        return body

    def find_game(game_id: str) -> HangmanGame:
        game = games.get(game_id)
        if game is None:
            abort(404, description="Game not found. Start a new game.")
        return game

    def public_state(game_id: str, game: HangmanGame) -> dict:
        # Never serialize game.__dict__: it contains the hidden answer.
        return {"game_id": game_id, **game.to_dict()}

    @app.post("/api/games")
    def create_game():
        body = read_body("difficulty")
        try:
            difficulty = normalize_difficulty(body["difficulty"])
        except ValueError as error:
            return error_response("invalid_difficulty", str(error), 400)
        game = HangmanGame(manager.choose_word(difficulty), difficulty)
        with lock:
            game_id = uuid4().hex
            games[game_id] = game
            response = jsonify(public_state(game_id, game))
        response.status_code = 201
        response.headers["Location"] = url_for("get_game", game_id=game_id)
        return response

    @app.get("/api/games/<game_id>")
    def get_game(game_id):
        with lock:
            return jsonify(public_state(game_id, find_game(game_id)))

    @app.post("/api/games/<game_id>/guess")
    def guess_letter(game_id):
        # Unknown IDs are reported before request-body errors for this route.
        with lock:
            game = find_game(game_id)
            body = read_body("letter")
            try:
                game.guess(body["letter"])
            except InvalidGuessError as error:
                return error_response("invalid_guess", str(error), 400)
            except DuplicateGuessError as error:
                return error_response("duplicate_guess", str(error), 409)
            except GameFinishedError as error:
                return error_response("game_finished", str(error), 409)
            return jsonify(public_state(game_id, game))

    return app


app = create_app()


if __name__ == "__main__":
    # Local development only. Production hosting is configured in Phase 6.
    app.run(host="127.0.0.1", port=5000, debug=False)
