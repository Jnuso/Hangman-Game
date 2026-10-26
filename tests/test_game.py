"""Requirement-based examples for the UI-independent Hangman engine."""

import json
import unittest

from game import (
    DuplicateGuessError,
    GameFinishedError,
    HangmanGame,
    InvalidGuessError,
)


class HangmanGameTests(unittest.TestCase):
    def setUp(self):
        self.game = HangmanGame("apple", "easy")

    def test_new_game_has_masked_word_six_lives_and_no_answer(self):
        self.assertEqual(self.game.to_dict(), {
            "difficulty": "easy",
            "pattern": "_ _ _ _ _",
            "guessed_letters": [],
            "incorrect_letters": [],
            "remaining_guesses": 6,
            "status": "playing",
        })

    def test_constructor_normalizes_word_and_difficulty(self):
        game = HangmanGame(" APPLE ", " EASY ")
        self.assertEqual(game.difficulty, "easy")
        self.assertEqual(game.guess("a")["pattern"], "a _ _ _ _")

    def test_constructor_rejects_unsupported_words(self):
        for word in (None, 42, [], "", " ", "ice cream", "can't", "cat2", "café", "K"):
            with self.subTest(word=word):
                with self.assertRaises(ValueError):
                    HangmanGame(word)

    def test_constructor_rejects_unsupported_difficulties(self):
        for difficulty in (None, 42, [], "", "expert"):
            with self.subTest(difficulty=difficulty):
                with self.assertRaises(ValueError):
                    HangmanGame("apple", difficulty)

    def test_correct_guess_reveals_every_occurrence_without_costing_lives(self):
        state = self.game.guess("p")
        self.assertEqual(state["pattern"], "_ p p _ _")
        self.assertEqual(state["guessed_letters"], ["p"])
        self.assertEqual(state["incorrect_letters"], [])
        self.assertEqual(state["remaining_guesses"], 6)
        self.assertEqual(state["status"], "playing")

    def test_incorrect_guess_costs_exactly_one_life(self):
        state = self.game.guess("z")
        self.assertEqual(state["pattern"], "_ _ _ _ _")
        self.assertEqual(state["guessed_letters"], ["z"])
        self.assertEqual(state["incorrect_letters"], ["z"])
        self.assertEqual(state["remaining_guesses"], 5)

    def test_uppercase_guesses_are_normalized_in_history_and_pattern(self):
        self.game.guess("P")
        state = self.game.guess("Z")
        self.assertEqual(state["pattern"], "_ p p _ _")
        self.assertEqual(state["guessed_letters"], ["p", "z"])
        self.assertEqual(state["incorrect_letters"], ["z"])

    def test_invalid_guesses_raise_without_changing_any_public_state(self):
        self.game.guess("p")
        invalid = (None, 7, True, [], {}, b"a", "", "ab", " ", " p ", "7", "!", "é", "K", "Ａ", "\n")
        for letter in invalid:
            with self.subTest(letter=letter):
                before = self.game.to_dict()
                with self.assertRaises(InvalidGuessError):
                    self.game.guess(letter)
                self.assertEqual(self.game.to_dict(), before)

    def test_duplicate_correct_or_incorrect_letters_preserve_state(self):
        for original, duplicate in (("p", "p"), ("p", "P"), ("Z", "z")):
            with self.subTest(original=original, duplicate=duplicate):
                game = HangmanGame("apple")
                game.guess(original)
                before = game.to_dict()
                with self.assertRaises(DuplicateGuessError):
                    game.guess(duplicate)
                self.assertEqual(game.to_dict(), before)

    def test_fifth_miss_is_playing_and_sixth_miss_is_lost(self):
        for letter in "bcdfg":
            state = self.game.guess(letter)
            self.assertEqual(state["status"], "playing")
            self.assertNotIn("word", state)
        self.assertEqual(state["remaining_guesses"], 1)

        state = self.game.guess("h")
        self.assertEqual(state["remaining_guesses"], 0)
        self.assertEqual(state["status"], "lost")
        self.assertEqual(state["word"], "apple")
        self.assertEqual(state["incorrect_letters"], list("bcdfgh"))

    def test_last_distinct_letter_wins_and_reveals_answer(self):
        for letter in "apl":
            state = self.game.guess(letter)
            self.assertEqual(state["status"], "playing")
            self.assertNotIn("word", state)
        state = self.game.guess("e")
        self.assertEqual(state["pattern"], "a p p l e")
        self.assertEqual(state["status"], "won")
        self.assertEqual(state["word"], "apple")
        self.assertEqual(state["remaining_guesses"], 6)

    def test_player_can_win_with_only_one_life_remaining(self):
        for letter in "bcdfg":
            self.game.guess(letter)
        for letter in "aple":
            state = self.game.guess(letter)
        self.assertEqual(state["status"], "won")
        self.assertEqual(state["remaining_guesses"], 1)

    def test_single_letter_and_repeated_single_letter_words_win_in_one_guess(self):
        for word, pattern in (("a", "a"), ("aaa", "a a a")):
            with self.subTest(word=word):
                game = HangmanGame(word)
                state = game.guess("a")
                self.assertEqual(state["status"], "won")
                self.assertEqual(state["pattern"], pattern)
                self.assertEqual(state["remaining_guesses"], 6)

    def test_post_win_and_post_loss_guesses_are_rejected_without_mutation(self):
        for outcome, guesses in (("won", "aple"), ("lost", "bcdfgh")):
            with self.subTest(outcome=outcome):
                game = HangmanGame("apple")
                for letter in guesses:
                    game.guess(letter)
                before = game.to_dict()
                self.assertEqual(before["status"], outcome)
                for letter in ("z", "a", "ab", None):
                    with self.subTest(letter=letter):
                        with self.assertRaises(GameFinishedError):
                            game.guess(letter)
                        self.assertEqual(game.to_dict(), before)

    def test_separate_games_do_not_share_history_or_lives(self):
        other = HangmanGame("apple", "hard")
        before = other.to_dict()
        self.game.guess("z")
        self.game.guess("p")
        self.assertEqual(other.to_dict(), before)

    def test_returned_histories_cannot_be_used_to_mutate_game(self):
        self.game.guess("p")
        self.game.guess("z")
        before = self.game.to_dict()
        state = self.game.to_dict()
        state["guessed_letters"].append("a")
        state["incorrect_letters"].clear()
        self.game.guessed_letters.clear()
        self.game.incorrect_letters.append("b")
        self.assertEqual(self.game.to_dict(), before)

    def test_returned_guess_state_is_detached_from_later_guesses(self):
        old_state = self.game.guess("p")
        self.game.guess("z")
        self.assertEqual(old_state["guessed_letters"], ["p"])
        self.assertEqual(old_state["incorrect_letters"], [])
        self.assertEqual(old_state["remaining_guesses"], 6)

    def test_public_state_is_json_serializable_in_all_game_states(self):
        for guesses in ("", "p", "aple", "bcdfgh"):
            with self.subTest(guesses=guesses):
                game = HangmanGame("apple")
                for letter in guesses:
                    game.guess(letter)
                state = game.to_dict()
                self.assertEqual(json.loads(json.dumps(state)), state)


if __name__ == "__main__":
    unittest.main()
