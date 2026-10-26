"""Word-resource validation and selection, using controlled file fixtures."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from game import HangmanGame
from word_manager import (
    WordListError,
    WordManager,
    normalize_difficulty,
    normalize_word,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class NormalizationTests(unittest.TestCase):
    def test_supported_difficulties_accept_case_and_surrounding_spaces(self):
        for raw, expected in (("easy", "easy"), (" MEDIUM ", "medium"), ("Hard", "hard")):
            with self.subTest(raw=raw):
                self.assertEqual(normalize_difficulty(raw), expected)

    def test_invalid_difficulties_are_rejected(self):
        for difficulty in (None, 7, [], {}, True, "", " ", "expert", "e asy"):
            with self.subTest(difficulty=difficulty):
                with self.assertRaises(ValueError):
                    normalize_difficulty(difficulty)

    def test_words_are_trimmed_and_lowercased(self):
        self.assertEqual(normalize_word(" \tAPPLE\n"), "apple")

    def test_words_must_be_nonempty_ascii_letters(self):
        for word in (None, 7, [], "", " ", "two words", "can't", "a-b", "a1", "café", "K"):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    normalize_word(word)


class WordManagerFileTests(unittest.TestCase):
    def setUp(self):
        # unittest's cleanup stack also handles fixtures if a test fails.
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for difficulty, contents in (
            ("easy", "apple\npear\n"),
            ("medium", "guitar\n"),
            ("hard", "rhythm\n"),
        ):
            (self.directory / f"{difficulty}.txt").write_text(contents, encoding="utf-8")

    def test_each_difficulty_selects_only_from_its_own_list(self):
        manager = WordManager(self.directory)
        for difficulty, expected in (
            ("easy", {"apple", "pear"}),
            ("medium", {"guitar"}),
            ("hard", {"rhythm"}),
        ):
            with self.subTest(difficulty=difficulty):
                self.assertIn(manager.choose_word(difficulty), expected)

    def test_selection_normalizes_difficulty(self):
        manager = WordManager(str(self.directory))
        self.assertEqual(manager.choose_word(" HARD "), "rhythm")

    def test_selection_rejects_unsupported_difficulty(self):
        manager = WordManager(self.directory)
        for difficulty in (None, [], "", "expert"):
            with self.subTest(difficulty=difficulty):
                with self.assertRaises(ValueError):
                    manager.choose_word(difficulty)

    def test_loader_handles_bom_whitespace_blanks_and_case_duplicates(self):
        (self.directory / "easy.txt").write_text(
            "\ufeff APPLE \n\napple\nPear\n PEAR \n\t\n", encoding="utf-8"
        )
        manager = WordManager(self.directory)
        # Observe candidates at the random-selection boundary, not private state.
        with patch("word_manager.random.choice", return_value="pear") as choose:
            self.assertEqual(manager.choose_word("easy"), "pear")
        self.assertEqual(tuple(choose.call_args.args[0]), ("apple", "pear"))

    def test_missing_required_file_reports_its_path(self):
        path = self.directory / "medium.txt"
        path.unlink()
        with self.assertRaises(WordListError) as caught:
            WordManager(self.directory)
        self.assertIn(str(path), str(caught.exception))

    def test_missing_directory_is_reported_clearly(self):
        directory = self.directory / "missing"
        with self.assertRaises(WordListError) as caught:
            WordManager(directory)
        self.assertIn(str(directory / "easy.txt"), str(caught.exception))

    def test_empty_and_blank_only_lists_are_rejected(self):
        for contents in ("", " \n\t\n", "\ufeff\n"):
            with self.subTest(contents=contents):
                path = self.directory / "easy.txt"
                path.write_text(contents, encoding="utf-8")
                with self.assertRaises(WordListError) as caught:
                    WordManager(self.directory)
                self.assertIn(str(path), str(caught.exception))
                self.assertIn("no usable words", str(caught.exception))

    def test_invalid_entries_report_path_and_original_line_number(self):
        for entry in ("ice cream", "can't", "cat2", "café", "K"):
            with self.subTest(entry=entry):
                path = self.directory / "easy.txt"
                path.write_text(f"apple\n\n{entry}\npear\n", encoding="utf-8")
                with self.assertRaises(WordListError) as caught:
                    WordManager(self.directory)
                self.assertIn(str(path), str(caught.exception))
                self.assertIn("line 3", str(caught.exception))

    def test_invalid_utf8_is_wrapped_as_word_list_error(self):
        path = self.directory / "hard.txt"
        path.write_bytes(b"\xff\xfe\xff")
        with self.assertRaises(WordListError) as caught:
            WordManager(self.directory)
        self.assertIn(str(path), str(caught.exception))
        self.assertIsInstance(caught.exception.__cause__, UnicodeError)

    def test_unreadable_file_is_wrapped_without_platform_permission_assumptions(self):
        with patch("word_manager.Path.read_text", side_effect=PermissionError("denied")):
            with self.assertRaises(WordListError) as caught:
                WordManager(self.directory)
        self.assertIn(str(self.directory / "easy.txt"), str(caught.exception))
        self.assertIsInstance(caught.exception.__cause__, PermissionError)

    def test_default_paths_work_outside_project_working_directory(self):
        original_directory = Path.cwd()
        try:
            os.chdir(self.directory)
            manager = WordManager()
            self.assertIn(
                manager.choose_word("easy"),
                (PROJECT_ROOT / "words" / "easy.txt").read_text(encoding="utf-8").splitlines(),
            )
        finally:
            os.chdir(original_directory)


class BundledWordsTests(unittest.TestCase):
    def test_each_starter_list_has_forty_unique_lowercase_ascii_words(self):
        for difficulty in ("easy", "medium", "hard"):
            with self.subTest(difficulty=difficulty):
                words = (PROJECT_ROOT / "words" / f"{difficulty}.txt").read_text(
                    encoding="utf-8"
                ).splitlines()
                self.assertEqual(len(words), 40)
                self.assertEqual(len(set(words)), 40)
                for word in words:
                    self.assertTrue(word.isascii() and word.isalpha() and word.islower())

    def test_selected_words_support_complete_games_at_all_difficulties(self):
        manager = WordManager()
        for difficulty in ("easy", "medium", "hard"):
            with self.subTest(difficulty=difficulty):
                word = manager.choose_word(difficulty)
                candidates = (PROJECT_ROOT / "words" / f"{difficulty}.txt").read_text(
                    encoding="utf-8"
                ).splitlines()
                self.assertIn(word, candidates)
                game = HangmanGame(word, difficulty)
                self.assertNotIn("word", game.to_dict())
                for letter in dict.fromkeys(word):
                    state = game.guess(letter)
                self.assertEqual(state["difficulty"], difficulty)
                self.assertEqual(state["status"], "won")
                self.assertEqual(state["word"], word)
                self.assertEqual(state["remaining_guesses"], 6)


if __name__ == "__main__":
    unittest.main()
