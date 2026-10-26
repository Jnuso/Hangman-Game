"""Request-body stalls must not hold the shared game-state lock."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import tempfile
from threading import Event
import unittest

from server import create_app
from word_manager import WordManager


class PausedBody(BytesIO):
    """Pause when Flask reads WSGI input, with an explicit release signal."""

    def __init__(self, payload):
        super().__init__(payload)
        self.read_started = Event()
        self.release = Event()

    def wait_for_release(self):
        self.read_started.set()
        if not self.release.wait(timeout=15):
            raise TimeoutError("Paused request body was not released by the test")

    def readinto(self, buffer):
        self.wait_for_release()
        return super().readinto(buffer)

    def read(self, size=-1):
        self.wait_for_release()
        return super().read(size)


class UnreadableBody(BytesIO):
    """An unknown game must be rejected before its body is consumed."""

    def readinto(self, buffer):
        raise AssertionError("Unknown-game request body was read")

    def read(self, size=-1):
        raise AssertionError("Unknown-game request body was read")


class SlowUploadApiTests(unittest.TestCase):
    def setUp(self):
        directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for difficulty, word in (("easy", "apple"), ("medium", "guitar"), ("hard", "rhythm")):
            (directory / f"{difficulty}.txt").write_text(word, encoding="utf-8")
        self.app = create_app(WordManager(directory))
        self.app.config["TESTING"] = True

    def request(self, method, path, **kwargs):
        # Every concurrent request owns its own Flask client and request context.
        with self.app.test_client() as client:
            response = client.open(path, method=method, **kwargs)
            return response.status_code, response.get_json()

    def new_game(self):
        status, state = self.request("POST", "/api/games", json={"difficulty": "easy"})
        self.assertEqual(status, 201)
        return state

    @contextmanager
    def paused_guess(self, game_id, letter):
        payload = ('{"letter":"' + letter + '"}').encode("ascii")
        body = PausedBody(payload)
        with ThreadPoolExecutor(max_workers=2) as pool:
            delayed = pool.submit(
                self.request, "POST", f"/api/games/{game_id}/guess",
                environ_overrides={
                    "wsgi.input": body,
                    "CONTENT_LENGTH": str(len(payload)),
                    "CONTENT_TYPE": "application/json",
                },
            )
            try:
                self.assertTrue(body.read_started.wait(timeout=5), "Flask never began reading the body")
                yield pool, delayed
            finally:
                # Release before executor shutdown, including after a failed assertion.
                body.release.set()

    def while_paused(self, pool, method, path, **kwargs):
        result = pool.submit(self.request, method, path, **kwargs)
        try:
            return result.result(timeout=3)
        except TimeoutError:
            self.fail(f"{method} {path} was blocked by another request's paused body")

    def test_paused_upload_allows_reads_other_guesses_and_creation(self):
        first = self.new_game()
        second = self.new_game()
        first_path = f"/api/games/{first['game_id']}"
        second_path = f"/api/games/{second['game_id']}"

        with self.paused_guess(first["game_id"], "z") as (pool, delayed):
            self.assertEqual(self.while_paused(pool, "GET", first_path), (200, first))
            self.assertEqual(self.while_paused(pool, "GET", second_path), (200, second))
            status, other = self.while_paused(pool, "POST", second_path + "/guess", json={"letter": "p"})
            self.assertEqual(status, 200)
            self.assertEqual(other["pattern"], "_ p p _ _")
            self.assertEqual(other["remaining_guesses"], 6)
            status, created = self.while_paused(pool, "POST", "/api/games", json={"difficulty": "hard"})
            self.assertEqual(status, 201)
            self.assertEqual(created["difficulty"], "hard")
            self.assertNotIn(created["game_id"], (first["game_id"], second["game_id"]))
            self.assertFalse(delayed.done(), "The upload must remain paused throughout these requests")

        status, state = delayed.result(timeout=5)
        self.assertEqual(status, 200)
        self.assertEqual(state["guessed_letters"], ["z"])
        self.assertEqual(state["incorrect_letters"], ["z"])
        self.assertEqual(state["remaining_guesses"], 5)
        self.assertEqual(self.request("GET", first_path), (200, state))
        self.assertEqual(self.request("GET", second_path), (200, other))
        self.assertEqual(self.request("GET", f"/api/games/{created['game_id']}"), (200, created))

    def test_delayed_final_miss_is_rejected_after_another_request_wins(self):
        game = self.new_game()
        path = f"/api/games/{game['game_id']}"
        for letter in "aplbcdfg":
            status, before = self.request("POST", path + "/guess", json={"letter": letter})
            self.assertEqual(status, 200)
        self.assertEqual(before["remaining_guesses"], 1)

        with self.paused_guess(game["game_id"], "z") as (pool, delayed):
            status, won = self.while_paused(pool, "POST", path + "/guess", json={"letter": "e"})
            self.assertEqual(status, 200)
            self.assertEqual(won["status"], "won")
            self.assertEqual(won["remaining_guesses"], 1)
            self.assertFalse(delayed.done())

        status, error = delayed.result(timeout=5)
        self.assertEqual(status, 409)
        self.assertEqual(error["error"]["code"], "game_finished")
        self.assertEqual(self.request("GET", path), (200, won))

    def test_delayed_duplicate_is_rejected_against_the_latest_history(self):
        game = self.new_game()
        path = f"/api/games/{game['game_id']}"

        with self.paused_guess(game["game_id"], "z") as (pool, delayed):
            status, accepted = self.while_paused(pool, "POST", path + "/guess", json={"letter": "Z"})
            self.assertEqual(status, 200)
            self.assertEqual(accepted["guessed_letters"], ["z"])
            self.assertEqual(accepted["remaining_guesses"], 5)
            self.assertFalse(delayed.done())

        status, error = delayed.result(timeout=5)
        self.assertEqual(status, 409)
        self.assertEqual(error["error"]["code"], "duplicate_guess")
        self.assertEqual(self.request("GET", path), (200, accepted))

    def test_unknown_game_is_rejected_without_reading_the_body(self):
        payload = b'{"letter":"a"}'
        status, error = self.request(
            "POST", "/api/games/unknown/guess",
            environ_overrides={
                "wsgi.input": UnreadableBody(payload),
                "CONTENT_LENGTH": str(len(payload)),
                "CONTENT_TYPE": "application/json",
            },
        )
        self.assertEqual(status, 404)
        self.assertEqual(error["error"]["code"], "not_found")


if __name__ == "__main__":
    unittest.main()
