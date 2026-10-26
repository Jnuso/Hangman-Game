"""Hangman rules and public state, independent of Flask and presentation."""

from word_manager import normalize_difficulty, normalize_word


class InvalidGuessError(ValueError):
    """A guess is not a single ASCII letter."""


class DuplicateGuessError(ValueError):
    """The letter has already been guessed."""


class GameFinishedError(ValueError):
    """A guess was submitted after the game ended."""


class HangmanGame:
    """One game with six lives and a server-owned answer.

    Call ``guess`` to update the game and ``to_dict`` to obtain client-safe
    state. Do not serialize the instance's internal attributes for clients.
    """

    MAX_INCORRECT_GUESSES = 6

    def __init__(self, word: str, difficulty: str = "medium") -> None:
        self._word = normalize_word(word)
        self._difficulty = normalize_difficulty(difficulty)
        self._guessed_letters: list[str] = []

    @property
    def difficulty(self) -> str:
        return self._difficulty

    @property
    def guessed_letters(self) -> list[str]:
        """Return a copy so callers cannot mutate the game's history."""
        return self._guessed_letters.copy()

    @property
    def incorrect_letters(self) -> list[str]:
        return [letter for letter in self._guessed_letters if letter not in self._word]

    @property
    def remaining_guesses(self) -> int:
        return self.MAX_INCORRECT_GUESSES - len(self.incorrect_letters)

    @property
    def pattern(self) -> str:
        return " ".join(
            letter if letter in self._guessed_letters else "_"
            for letter in self._word
        )

    @property
    def status(self) -> str:
        if all(letter in self._guessed_letters for letter in self._word):
            return "won"
        if self.remaining_guesses == 0:
            return "lost"
        return "playing"

    def guess(self, letter: str) -> dict:
        """Accept one A–Z letter and return updated public state.

        Uppercase input is accepted. Spaces, digits, punctuation, non-ASCII
        letters, duplicate guesses, and post-game guesses are rejected before
        any state changes.
        """
        if self.status != "playing":
            raise GameFinishedError("This game has ended. Start a new game.")
        if (
            not isinstance(letter, str)
            or len(letter) != 1
            or not letter.isascii()
            or not letter.isalpha()
        ):
            raise InvalidGuessError("Guess exactly one letter from A to Z.")
        letter = letter.lower()
        if letter in self._guessed_letters:
            raise DuplicateGuessError(f"The letter '{letter}' has already been guessed.")

        self._guessed_letters.append(letter)
        return self.to_dict()

    def to_dict(self) -> dict:
        """Return fresh JSON-compatible state; reveal the answer only at the end."""
        state = {
            "difficulty": self.difficulty,
            "pattern": self.pattern,
            "guessed_letters": self.guessed_letters,
            "incorrect_letters": self.incorrect_letters,
            "remaining_guesses": self.remaining_guesses,
            "status": self.status,
        }
        if state["status"] != "playing":
            state["word"] = self._word
        return state
