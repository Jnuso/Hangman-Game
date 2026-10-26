"""Complete bundled-word API flows and actual development-server startup."""

import json
import os
from pathlib import Path
import socket
import string
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from server import create_app
from word_manager import WordManager


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FIELDS = {
    "game_id", "difficulty", "pattern", "guessed_letters",
    "incorrect_letters", "remaining_guesses", "status",
}


class BundledWordApiTests(unittest.TestCase):
    def setUp(self):
        self.manager = WordManager()
        self.client = create_app(self.manager).test_client()

    def words(self):
        for difficulty in ("easy", "medium", "hard"):
            for word in (ROOT / "words" / f"{difficulty}.txt").read_text(encoding="utf-8").splitlines():
                yield difficulty, word

    def create(self, difficulty, word):
        # Control selection only; all HTTP validation and game rules remain real.
        with patch.object(self.manager, "choose_word", return_value=word):
            response = self.client.post("/api/games", json={"difficulty": difficulty})
        self.assertEqual(response.status_code, 201)
        state = response.json
        self.assertEqual(set(state), PUBLIC_FIELDS)
        self.assertEqual(state["difficulty"], difficulty)
        self.assertEqual(state["pattern"], " ".join("_" * len(word)))
        return f"/api/games/{state['game_id']}"

    def test_every_bundled_word_can_be_won_through_api(self):
        for difficulty, word in self.words():
            with self.subTest(difficulty=difficulty, word=word):
                path = self.create(difficulty, word)
                letters = list(dict.fromkeys(word))
                for index, letter in enumerate(letters):
                    response = self.client.post(path + "/guess", json={"letter": letter.upper()})
                    self.assertEqual(response.status_code, 200)
                    state = response.json
                    self.assertEqual(state["remaining_guesses"], 6)
                    self.assertEqual(state["incorrect_letters"], [])
                    self.assertEqual(state["guessed_letters"], letters[:index + 1])
                    self.assertEqual(self.client.get(path).json, state)
                    if index < len(letters) - 1:
                        self.assertEqual(state["status"], "playing")
                        self.assertEqual(set(state), PUBLIC_FIELDS)
                self.assertEqual(state["status"], "won")
                self.assertEqual(set(state), PUBLIC_FIELDS | {"word"})
                self.assertEqual(state["word"], word)
                self.assertEqual(state["pattern"], " ".join(word))

    def test_every_bundled_word_loses_on_six_misses_through_api(self):
        for difficulty, word in self.words():
            with self.subTest(difficulty=difficulty, word=word):
                path = self.create(difficulty, word)
                misses = [letter for letter in string.ascii_lowercase if letter not in word][:6]
                self.assertEqual(len(misses), 6, "Fixture needs six distinct absent letters")
                for index, letter in enumerate(misses):
                    response = self.client.post(path + "/guess", json={"letter": letter})
                    self.assertEqual(response.status_code, 200)
                    state = response.json
                    self.assertEqual(state["remaining_guesses"], 5 - index)
                    self.assertEqual(state["incorrect_letters"], misses[:index + 1])
                    self.assertEqual(state["pattern"], " ".join("_" * len(word)))
                    self.assertEqual(self.client.get(path).json, state)
                    if index < 5:
                        self.assertEqual(state["status"], "playing")
                        self.assertEqual(set(state), PUBLIC_FIELDS)
                self.assertEqual(state["status"], "lost")
                self.assertEqual(state["word"], word)
                self.assertEqual(set(state), PUBLIC_FIELDS | {"word"})
                rejected = self.client.post(path + "/guess", json={"letter": misses[0]})
                self.assertEqual(rejected.status_code, 409)
                self.assertEqual(self.client.get(path).json, state)


class DevelopmentServerProcessTests(unittest.TestCase):
    """Exercise the documented script, not Flask's in-process test client.

    Port 5000 is private to the network-disabled test container. The working
    directory is unrelated to the project to catch resource-path assumptions.
    """

    def setUp(self):
        # Never send test mutations to a user's already-running local server.
        with socket.socket() as probe:
            probe.settimeout(0.25)
            if probe.connect_ex(("127.0.0.1", 5000)) == 0:
                self.skipTest("Port 5000 is already in use; stop the local server or run tests in Docker.")
        self.directory = self.enterContext(tempfile.TemporaryDirectory())
        self.log = self.enterContext(tempfile.TemporaryFile(mode="w+t"))
        self.process = None
        self.addCleanup(self.stop_server)

    def stop_server(self):
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
            self.process = None

    def start_server(self):
        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        self.process = subprocess.Popen(
            [sys.executable, str(ROOT / "server.py")], cwd=self.directory,
            env=environment, stdout=self.log, stderr=subprocess.STDOUT,
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and self.process.poll() is None:
            try:
                with urlopen("http://127.0.0.1:5000/", timeout=0.25) as response:
                    if response.status == 200:
                        return
            except (URLError, TimeoutError):
                time.sleep(0.05)
        self.log.seek(0)
        self.fail("Development server did not start: " + self.log.read())

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = Request("http://127.0.0.1:5000" + path, method=method, data=data,
                      headers={"Content-Type": "application/json"})
        try:
            response = urlopen(req, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_script_starts_page_assets_and_api_from_another_directory(self):
        self.start_server()
        for path, content_type in (("/", "text/html"), ("/static/app.js", "text/javascript"), ("/static/style.css", "text/css")):
            with self.subTest(path=path):
                with urlopen("http://127.0.0.1:5000" + path, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.headers.get_content_type(), content_type)
                    self.assertTrue(response.read())
        status, state = self.request("POST", "/api/games", {"difficulty": "easy"})
        self.assertEqual(status, 201)
        path = f"/api/games/{state['game_id']}"
        self.assertEqual(self.request("GET", path), (200, state))
        status, guessed = self.request("POST", path + "/guess", {"letter": "p"})
        self.assertEqual(status, 200)
        self.assertEqual(guessed["guessed_letters"], ["p"])
        self.assertNotIn("word", guessed)
        self.assertEqual(self.request("GET", "/words/easy.txt")[0], 404)

    def test_restart_forgets_old_games_and_accepts_new_ones(self):
        self.start_server()
        status, first = self.request("POST", "/api/games", {"difficulty": "hard"})
        self.assertEqual(status, 201)
        self.stop_server()
        self.start_server()
        status, missing = self.request("GET", f"/api/games/{first['game_id']}")
        self.assertEqual(status, 404)
        self.assertEqual(missing["error"]["code"], "not_found")
        status, fresh = self.request("POST", "/api/games", {"difficulty": "hard"})
        self.assertEqual(status, 201)
        self.assertNotEqual(fresh["game_id"], first["game_id"])
        self.assertEqual(fresh["status"], "playing")
        self.assertEqual(fresh["remaining_guesses"], 6)


if __name__ == "__main__":
    unittest.main()
