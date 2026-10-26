"""HTTP contract tests using Flask's client and real loopback requests."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
from threading import Barrier, Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from werkzeug.serving import make_server

from server import create_app
from word_manager import WordManager


class ApiTests(unittest.TestCase):
    def setUp(self):
        directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for difficulty, word in (("easy", "apple"), ("medium", "guitar"), ("hard", "rhythm")):
            (directory / f"{difficulty}.txt").write_text(word, encoding="utf-8")
        self.manager = WordManager(directory)
        self.app = create_app(self.manager)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def new_game(self, difficulty="easy"):
        response = self.client.post("/api/games", json={"difficulty": difficulty})
        self.assertEqual(response.status_code, 201)
        return response.json

    def guess(self, game_id, letter):
        return self.client.post(f"/api/games/{game_id}/guess", json={"letter": letter})

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(set(response.json), {"error"})
        self.assertEqual(response.json["error"]["code"], code)
        self.assertTrue(response.json["error"]["message"])

    def parallel_requests(self, requests):
        """Release one independent client per request from a shared start gate."""
        start = Barrier(len(requests), timeout=5)

        def send(spec):
            method, path, body = spec
            with self.app.test_client() as client:
                start.wait()
                response = client.open(path, method=method, json=body)
                return response.status_code, response.json

        with ThreadPoolExecutor(max_workers=len(requests)) as pool:
            return list(pool.map(send, requests))

    def test_create_and_retrieve_all_difficulties(self):
        for difficulty, length in (("easy", 5), ("medium", 6), ("hard", 6)):
            with self.subTest(difficulty=difficulty):
                state = self.new_game(difficulty)
                self.assertEqual(state["difficulty"], difficulty)
                self.assertEqual(state["pattern"], " ".join("_" * length))
                self.assertEqual(state["remaining_guesses"], 6)
                self.assertEqual(state["status"], "playing")
                self.assertEqual(state["guessed_letters"], [])
                self.assertNotIn("word", state)
                response = self.client.get(f"/api/games/{state['game_id']}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json, state)
                self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_creation_returns_resource_location_and_unique_ids(self):
        ids = set()
        for _ in range(20):
            response = self.client.post("/api/games", json={"difficulty": "easy"})
            self.assertEqual(response.status_code, 201)
            game_id = response.json["game_id"]
            self.assertNotIn(game_id, ids)
            ids.add(game_id)
            self.assertEqual(response.headers["Location"], f"/api/games/{game_id}")

    def test_difficulty_case_and_whitespace_are_normalized(self):
        self.assertEqual(self.new_game(" EASY ")["difficulty"], "easy")

    def test_invalid_difficulty_types_and_values_are_rejected(self):
        for value in (None, [], {}, 4, True, "", "expert"):
            with self.subTest(value=value):
                response = self.client.post("/api/games", json={"difficulty": value})
                self.assert_error(response, 400, "invalid_difficulty")

    def test_create_requires_exactly_one_difficulty_field(self):
        for body in ({}, {"word": "apple"}, {"difficulty": "easy", "word": "apple"},
                     {"difficulty": "easy", "game_id": "chosen"}, {"difficulty": "easy", "status": "won"}):
            with self.subTest(body=body):
                self.assert_error(self.client.post("/api/games", json=body), 400, "bad_request")

    def test_nonobject_json_is_rejected_on_both_post_routes(self):
        game_id = self.new_game()["game_id"]
        for path in ("/api/games", f"/api/games/{game_id}/guess"):
            for body in ("null", "[]", '"easy"', "7", "true"):
                with self.subTest(path=path, body=body):
                    response = self.client.post(path, data=body, content_type="application/json")
                    self.assert_error(response, 400, "bad_request")

    def test_malformed_json_and_missing_bodies_are_rejected(self):
        game_id = self.new_game()["game_id"]
        before = self.client.get(f"/api/games/{game_id}").json
        for path in ("/api/games", f"/api/games/{game_id}/guess"):
            for body in ("", "{", '{"letter":}'):
                with self.subTest(path=path, body=body):
                    self.assert_error(self.client.post(path, data=body, content_type="application/json"), 400, "bad_request")
        self.assertEqual(self.client.get(f"/api/games/{game_id}").json, before)

    def test_non_json_content_types_receive_415(self):
        game_id = self.new_game()["game_id"]
        for path in ("/api/games", f"/api/games/{game_id}/guess"):
            for content_type in (None, "text/plain", "application/x-www-form-urlencoded"):
                with self.subTest(path=path, content_type=content_type):
                    self.assert_error(self.client.post(path, data="letter=a", content_type=content_type), 415, "unsupported_media_type")

    def test_unknown_game_ids_return_json_404(self):
        self.assert_error(self.client.get("/api/games/unknown"), 404, "not_found")
        self.assert_error(self.guess("unknown", "a"), 404, "not_found")

    def test_unknown_id_precedes_malformed_guess_body(self):
        self.assert_error(self.client.post("/api/games/unknown/guess", data="{"), 404, "not_found")

    def test_correct_and_incorrect_guesses_use_engine_state(self):
        game_id = self.new_game()["game_id"]
        hit = self.guess(game_id, "P")
        self.assertEqual(hit.status_code, 200)
        self.assertEqual(hit.json["pattern"], "_ p p _ _")
        self.assertEqual(hit.json["remaining_guesses"], 6)
        miss = self.guess(game_id, "z")
        self.assertEqual(miss.json["guessed_letters"], ["p", "z"])
        self.assertEqual(miss.json["incorrect_letters"], ["z"])
        self.assertEqual(miss.json["remaining_guesses"], 5)
        self.assertEqual(self.client.get(f"/api/games/{game_id}").json, miss.json)

    def test_invalid_guesses_preserve_game_state(self):
        game_id = self.new_game()["game_id"]
        before = self.client.get(f"/api/games/{game_id}").json
        for value in (None, [], {}, 7, True, "", "ab", " ", "7", "é", "K"):
            with self.subTest(value=value):
                self.assert_error(self.guess(game_id, value), 400, "invalid_guess")
                self.assertEqual(self.client.get(f"/api/games/{game_id}").json, before)

    def test_guess_missing_and_extra_fields_are_rejected_without_mutation(self):
        game_id = self.new_game()["game_id"]
        before = self.client.get(f"/api/games/{game_id}").json
        for body in ({}, {"letter": "a", "word": "a"}, {"letter": "a", "remaining_guesses": 99},
                     {"letter": "a", "difficulty": "hard"}, {"letter": "a", "status": "won"}):
            with self.subTest(body=body):
                response = self.client.post(f"/api/games/{game_id}/guess", json=body)
                self.assert_error(response, 400, "bad_request")
                self.assertEqual(self.client.get(f"/api/games/{game_id}").json, before)

    def test_duplicate_guesses_return_409_without_mutation(self):
        game_id = self.new_game()["game_id"]
        for letter in ("p", "z"):
            before = self.guess(game_id, letter).json
            self.assert_error(self.guess(game_id, letter.upper()), 409, "duplicate_guess")
            self.assertEqual(self.client.get(f"/api/games/{game_id}").json, before)

    def test_complete_win_and_loss_reveal_answer_only_at_completion(self):
        for guesses, outcome in (("aple", "won"), ("bcdfgh", "lost")):
            with self.subTest(outcome=outcome):
                game_id = self.new_game()["game_id"]
                for index, letter in enumerate(guesses):
                    response = self.guess(game_id, letter)
                    self.assertEqual(response.status_code, 200)
                    if index < len(guesses) - 1:
                        self.assertEqual(response.json["status"], "playing")
                        self.assertNotIn("word", response.json)
                        self.assertNotIn("word", self.client.get(f"/api/games/{game_id}").json)
                self.assertEqual(response.json["status"], outcome)
                self.assertEqual(response.json["word"], "apple")
                before = response.json
                self.assert_error(self.guess(game_id, "z"), 409, "game_finished")
                self.assertEqual(self.client.get(f"/api/games/{game_id}").json, before)
                self.assertEqual(self.new_game()["status"], "playing")

    def test_games_and_app_instances_have_separate_storage(self):
        first = self.new_game()
        second = self.new_game()
        self.guess(first["game_id"], "z")
        self.assertEqual(self.client.get(f"/api/games/{second['game_id']}").json, second)
        other = create_app(self.manager).test_client()
        self.assert_error(other.get(f"/api/games/{first['game_id']}"), 404, "not_found")

    def test_simultaneous_duplicate_guesses_accept_only_one(self):
        game_id = self.new_game()["game_id"]
        results = self.parallel_requests([
            ("POST", f"/api/games/{game_id}/guess", {"letter": letter})
            for letter in ("z", "Z") * 4
        ])
        self.assertEqual(sorted(status for status, _ in results), [200] + [409] * 7)
        for status, state in results:
            if status == 409:
                self.assertEqual(state["error"]["code"], "duplicate_guess")
        state = self.client.get(f"/api/games/{game_id}").json
        self.assertEqual(state["remaining_guesses"], 5)
        self.assertEqual(state["guessed_letters"], ["z"])

    def test_concurrent_distinct_guesses_are_both_recorded(self):
        game_id = self.new_game()["game_id"]
        results = self.parallel_requests([
            ("POST", f"/api/games/{game_id}/guess", {"letter": letter})
            for letter in ("p", "z")
        ])
        self.assertEqual([status for status, _ in results], [200, 200])
        state = self.client.get(f"/api/games/{game_id}").json
        self.assertCountEqual(state["guessed_letters"], ["p", "z"])
        self.assertEqual(state["pattern"], "_ p p _ _")
        self.assertEqual(state["remaining_guesses"], 5)
        self.assertEqual(state["incorrect_letters"], ["z"])

    def test_concurrent_misses_with_one_life_accept_exactly_one(self):
        game_id = self.new_game()["game_id"]
        for letter in "bcdfg":
            self.guess(game_id, letter)
        results = self.parallel_requests([
            ("POST", f"/api/games/{game_id}/guess", {"letter": letter})
            for letter in "hijk"
        ])
        self.assertEqual(sorted(status for status, _ in results), [200, 409, 409, 409])
        for status, body in results:
            if status == 409:
                self.assertEqual(body["error"]["code"], "game_finished")
        state = self.client.get(f"/api/games/{game_id}").json
        self.assertEqual(state["status"], "lost")
        self.assertEqual(state["remaining_guesses"], 0)
        self.assertEqual(len(state["incorrect_letters"]), 6)
        self.assertEqual(len(state["guessed_letters"]), 6)

    def test_winning_letter_racing_final_miss_has_one_valid_terminal_outcome(self):
        game_id = self.new_game()["game_id"]
        for letter in "aplbcdfg":
            self.guess(game_id, letter)
        results = self.parallel_requests([
            ("POST", f"/api/games/{game_id}/guess", {"letter": letter})
            for letter in ("e", "z")
        ])
        self.assertEqual(sorted(status for status, _ in results), [200, 409])
        state = self.client.get(f"/api/games/{game_id}").json
        accepted = next(body for status, body in results if status == 200)
        self.assertEqual(state, accepted)
        self.assertEqual(state["word"], "apple")
        if state["status"] == "won":
            self.assertEqual(state["remaining_guesses"], 1)
            self.assertEqual(state["pattern"], "a p p l e")
            self.assertNotIn("z", state["guessed_letters"])
        else:
            self.assertEqual(state["status"], "lost")
            self.assertEqual(state["remaining_guesses"], 0)
            self.assertEqual(state["pattern"], "a p p l _")
            self.assertNotIn("e", state["guessed_letters"])
        rejected = next(body for status, body in results if status == 409)
        self.assertEqual(rejected["error"]["code"], "game_finished")

    def test_get_racing_winning_guess_returns_a_complete_before_or_after_snapshot(self):
        game_id = self.new_game()["game_id"]
        for letter in "apl":
            self.guess(game_id, letter)
        path = f"/api/games/{game_id}"
        before = self.client.get(path).json
        results = self.parallel_requests([
            ("GET", path, None),
            ("POST", path + "/guess", {"letter": "e"}),
        ])
        self.assertEqual([status for status, _ in results], [200, 200])
        after = self.client.get(path).json
        self.assertEqual(after["status"], "won")
        self.assertIn(results[0][1], (before, after))
        self.assertEqual(results[1][1], after)

    def test_parallel_game_creation_produces_independent_retrievable_ids(self):
        results = self.parallel_requests([
            ("POST", "/api/games", {"difficulty": "easy"}) for _ in range(8)
        ])
        self.assertEqual([status for status, _ in results], [201] * 8)
        states = [state for _, state in results]
        self.assertEqual(len({state["game_id"] for state in states}), 8)
        for state in states:
            self.assertEqual(self.client.get(f"/api/games/{state['game_id']}").json, state)

    def test_invalid_request_does_not_block_a_concurrent_valid_guess(self):
        game_id = self.new_game()["game_id"]
        results = self.parallel_requests([
            ("POST", f"/api/games/{game_id}/guess", {"letter": value})
            for value in ([], "z")
        ])
        self.assertEqual([status for status, _ in results], [400, 200])
        state = self.client.get(f"/api/games/{game_id}").json
        self.assertEqual(state["remaining_guesses"], 5)
        self.assertEqual(state["guessed_letters"], ["z"])

    def test_request_body_limit_accepts_exact_limit_and_rejects_one_byte_over(self):
        limit = self.app.config["MAX_CONTENT_LENGTH"]
        for size, expected_status in ((limit, 200), (limit + 1, 413)):
            with self.subTest(size=size):
                game_id = self.new_game()["game_id"]
                path = f"/api/games/{game_id}"
                before = self.client.get(path).json
                payload = b'{"letter":"z"}'
                payload += b" " * (size - len(payload))
                response = self.client.post(path + "/guess", data=payload, content_type="application/json")
                self.assertEqual(response.status_code, expected_status)
                if size > limit:
                    self.assert_error(response, 413, "request_entity_too_large")
                    self.assertEqual(self.client.get(path).json, before)
                else:
                    self.assertEqual(response.json["remaining_guesses"], 5)

    def test_broken_encoding_and_trailing_json_do_not_change_state(self):
        game_id = self.new_game()["game_id"]
        path = f"/api/games/{game_id}"
        before = self.client.get(path).json
        for payload in (b'{"letter":"\xff"}', b'{"letter":"z"} {}', b'{"letter":"z"}\x00'):
            with self.subTest(payload=payload):
                response = self.client.post(path + "/guess", data=payload, content_type="application/json")
                self.assert_error(response, 400, "bad_request")
                self.assertEqual(self.client.get(path).json, before)
        # An HTTP parsing failure must not leave the lock held.
        self.assertEqual(self.guess(game_id, "z").status_code, 200)

    def test_supported_json_media_types_with_charset_are_accepted(self):
        for content_type in ("application/json; charset=utf-8", "application/vnd.hangman+json"):
            with self.subTest(content_type=content_type):
                response = self.client.post("/api/games", data='{"difficulty":"easy"}', content_type=content_type)
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json["difficulty"], "easy")

    def test_error_responses_are_not_cacheable(self):
        game_id = self.new_game()["game_id"]
        self.guess(game_id, "z")
        for response in (
            self.guess(game_id, "z"),
            self.guess(game_id, "ab"),
            self.client.get("/api/games/missing"),
            self.client.get("/api/games"),
        ):
            with self.subTest(status=response.status_code):
                self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_invalid_and_duplicate_guesses_cannot_consume_last_life(self):
        game_id = self.new_game()["game_id"]
        for letter in "bcdfg":
            self.guess(game_id, letter)
        before = self.client.get(f"/api/games/{game_id}").json
        self.assertEqual(before["remaining_guesses"], 1)
        self.assert_error(self.guess(game_id, "B"), 409, "duplicate_guess")
        self.assert_error(self.guess(game_id, "ab"), 400, "invalid_guess")
        self.assertEqual(self.client.get(f"/api/games/{game_id}").json, before)
        for letter in "aple":
            response = self.guess(game_id, letter)
        self.assertEqual(response.json["status"], "won")
        self.assertEqual(response.json["remaining_guesses"], 1)

    def test_unknown_routes_and_wrong_methods_return_json_and_preserve_allow(self):
        self.assert_error(self.client.get("/missing"), 404, "not_found")
        response = self.client.get("/api/games")
        self.assert_error(response, 405, "method_not_allowed")
        self.assertIn("POST", response.headers["Allow"])

    def test_word_resources_and_source_files_are_not_served(self):
        for path in ("/words/easy.txt", "/static/../words/easy.txt", "/static/words/easy.txt", "/game.py", "/SPECIFICATION.md"):
            with self.subTest(path=path):
                self.assert_error(self.client.get(path), 404, "not_found")

    def test_oversized_requests_are_rejected_as_json(self):
        response = self.client.post("/api/games", json={"difficulty": "a" * 17000})
        self.assert_error(response, 413, "request_entity_too_large")


class LiveHttpTests(unittest.TestCase):
    def test_complete_games_over_real_loopback_http(self):
        directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for difficulty in ("easy", "medium", "hard"):
            (directory / f"{difficulty}.txt").write_text("apple\n", encoding="utf-8")
        httpd = make_server("127.0.0.1", 0, create_app(WordManager(directory)))
        thread = Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(thread.join, 5)
        self.addCleanup(httpd.shutdown)
        base = f"http://127.0.0.1:{httpd.server_port}"

        def request(method, path, body=None):
            data = None if body is None else json.dumps(body).encode()
            req = Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=5) as response:
                self.assertIn("application/json", response.headers["Content-Type"])
                return response.status, json.load(response)

        for guesses, outcome in (("aple", "won"), ("bcdfgh", "lost")):
            status, state = request("POST", "/api/games", {"difficulty": "easy"})
            self.assertEqual(status, 201)
            self.assertNotIn("word", state)
            path = f"/api/games/{state['game_id']}"
            self.assertEqual(request("GET", path)[1], state)
            for letter in guesses:
                status, state = request("POST", path + "/guess", {"letter": letter})
                self.assertEqual(status, 200)
            self.assertEqual(state["status"], outcome)
            self.assertEqual(state["word"], "apple")
            with self.assertRaises(HTTPError) as caught:
                request("POST", path + "/guess", {"letter": "z"})
            with caught.exception as error:
                self.assertEqual(error.code, 409)
                self.assertEqual(json.load(error)["error"]["code"], "game_finished")


if __name__ == "__main__":
    unittest.main()
