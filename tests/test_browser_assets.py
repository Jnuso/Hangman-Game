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

    def test_head_requests_preserve_types_without_sending_asset_bodies(self):
        for path, content_type in (("/", "text/html"), ("/static/style.css", "text/css"), ("/static/app.js", "text/javascript")):
            with self.subTest(path=path):
                with self.client.head(path) as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.mimetype, content_type)
                    self.assertEqual(response.data, b"")
                    self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_missing_assets_return_json_instead_of_an_html_success_page(self):
        response = self.client.get("/static/missing.js")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"]["code"], "not_found")

    def test_post_to_page_or_assets_preserves_json_method_errors(self):
        for path in ("/", "/static/app.js"):
            with self.subTest(path=path):
                response = self.client.post(path, json={})
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.json["error"]["code"], "method_not_allowed")
                self.assertIn("GET", response.headers["Allow"])


if __name__ == "__main__":
    unittest.main()
