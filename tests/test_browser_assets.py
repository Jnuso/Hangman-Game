"""Flask delivery checks; real browser behavior is checked separately."""

import unittest

from server import create_app


class BrowserAssetTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_home_serves_game_page(self):
        with self.client.get("/") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "text/html")
            self.assertIn(b"/static/style.css", response.data)
            self.assertIn(b"/static/app.js", response.data)
            self.assertIn(b'lang="en"', response.data)

    def test_required_assets_are_available_with_correct_types(self):
        for path, content_type in (("/static/style.css", "text/css"), ("/static/app.js", "text/javascript")):
            with self.subTest(path=path):
                with self.client.get(path) as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.mimetype, content_type)
                    self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_static_routes_cannot_escape_to_word_lists_or_sources(self):
        for path in ("/static/../words/easy.txt", "/static/%2e%2e/words/easy.txt", "/static/../server.py", "/static/words/easy.txt"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404)
                self.assertTrue(response.is_json)


if __name__ == "__main__":
    unittest.main()
