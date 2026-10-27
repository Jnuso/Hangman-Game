"""Exercise a running deployment over HTTP, creating only this check's games."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import string
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def check_deployment(base_url: str) -> dict:
    base_url = base_url.rstrip("/")
    url = urlsplit(base_url)
    if url.scheme not in {"http", "https"} or not url.netloc or url.query or url.fragment:
        raise ValueError("Supply an HTTP or HTTPS base URL without a query or fragment.")
    checked = []

    def request(path: str, expected: int, body: dict | None = None):
        payload = None if body is None else json.dumps(body).encode("utf-8")
        outgoing = Request(
            base_url + path,
            data=payload,
            headers={} if body is None else {"Content-Type": "application/json"},
        )
        try:
            response = urlopen(outgoing, timeout=20)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read().decode("utf-8")
            assert response.status == expected, (path, expected, response.status, raw[:200])
            data = json.loads(raw) if response.headers.get_content_type() == "application/json" else raw
        checked.append((outgoing.get_method(), path, expected))
        return data

    def active(state: dict):
        assert state["status"] == "playing" and "word" not in state, state
        assert set(state) == {
            "game_id", "difficulty", "pattern", "guessed_letters",
            "incorrect_letters", "remaining_guesses", "status",
        }, state

    def create(difficulty: str):
        state = request("/api/games", 201, {"difficulty": difficulty})
        active(state)
        assert state["difficulty"] == difficulty, state
        assert state["remaining_guesses"] == 6, state
        assert state["guessed_letters"] == state["incorrect_letters"] == [], state
        assert all(slot == "_" for slot in state["pattern"].split(" ")), state
        return state

    assert "Hangman" in request("/", 200)
    request("/static/app.js", 200)
    request("/static/style.css", 200)
    request("/words/easy.txt", 404)
    request("/server.py", 404)
    request("/api/games/unknown", 404)
    request("/api/games", 400, {"difficulty": "unsupported"})

    rounds = []
    for difficulty in ("easy", "medium", "hard"):
        state = create(difficulty)
        path = f"/api/games/{state['game_id']}"
        assert request(path, 200) == state
        state = request(path + "/guess", 200, {"letter": "a"})
        active(state)
        request(path + "/guess", 409, {"letter": "A"})
        request(path + "/guess", 400, {"letter": "ab"})
        assert request(path, 200) == state
        for letter in string.ascii_lowercase[1:]:
            if state["status"] != "playing":
                break
            state = request(path + "/guess", 200, {"letter": letter})
            if state["status"] == "playing":
                active(state)
        assert state["status"] in {"won", "lost"}, state
        assert isinstance(state.get("word"), str) and state["word"].isascii(), state
        if state["status"] == "won":
            assert state["pattern"].replace(" ", "") == state["word"], state
        else:
            assert state["remaining_guesses"] == 0, state
        request(path + "/guess", 409, {"letter": "z"})
        assert request(path, 200) == state
        rounds.append({"difficulty": difficulty, "status": state["status"]})

    # A fresh game after completed rounds also tests two overlapping clients.
    fresh = create("easy")
    path = f"/api/games/{fresh['game_id']}"

    def duplicate():
        outgoing = Request(
            base_url + path + "/guess",
            data=b'{"letter":"a"}',
            headers={"Content-Type": "application/json"},
        )
        try:
            response = urlopen(outgoing, timeout=20)
        except HTTPError as error:
            response = error
        with response:
            response.read()
            return response.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(lambda _: duplicate(), range(2)))
    assert statuses == [200, 409], statuses
    state = request(path, 200)
    active(state)
    assert state["guessed_letters"] == ["a"], state
    assert state["remaining_guesses"] in {5, 6}, state
    return {
        "base_url": base_url,
        "requests_checked": len(checked) + 2,
        "completed_rounds": rounds,
        "concurrent_duplicate_statuses": statuses,
        "restart_game_id": fresh["game_id"],
        "result": "passed",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="For example, https://your-app.onrender.com")
    args = parser.parse_args()
    print(json.dumps(check_deployment(args.base_url), indent=2))
