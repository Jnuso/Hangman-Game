"""Load validated difficulty lists and select a random Hangman answer."""

from pathlib import Path
import random


DIFFICULTIES = ("easy", "medium", "hard")
DEFAULT_WORDS_DIRECTORY = Path(__file__).resolve().parent / "words"


def normalize_difficulty(difficulty: str) -> str:
    """Accept a supported difficulty, ignoring surrounding spaces and case."""
    if not isinstance(difficulty, str):
        raise ValueError("Difficulty must be easy, medium, or hard.")
    difficulty = difficulty.strip().lower()
    if difficulty not in DIFFICULTIES:
        raise ValueError("Difficulty must be easy, medium, or hard.")
    return difficulty


def normalize_word(word: str) -> str:
    """Normalize one nonempty ASCII alphabetic word; reject unsupported input."""
    if not isinstance(word, str):
        raise ValueError("Words must contain only letters A to Z.")
    word = word.strip()
    if not word or not word.isascii() or not word.isalpha():
        raise ValueError("Words must contain only letters A to Z.")
    return word.lower()


class WordListError(ValueError):
    """A required word list cannot be loaded or contains invalid data."""


class WordManager:
    """Load all three lists once, rejecting invalid entries and empty lists.

    File paths default to this module's directory, not the shell's working
    directory. Pass a different directory when using other word-list files.
    """

    def __init__(self, words_directory: str | Path | None = None) -> None:
        directory = (
            DEFAULT_WORDS_DIRECTORY
            if words_directory is None
            else Path(words_directory)
        )
        self._words: dict[str, tuple[str, ...]] = {}
        for difficulty in DIFFICULTIES:
            path = directory / f"{difficulty}.txt"
            try:
                lines = path.read_text(encoding="utf-8-sig").splitlines()
            except (OSError, UnicodeError) as exc:
                raise WordListError(f"Unable to read word list '{path}': {exc}") from exc

            unique_words = dict.fromkeys(self._load_words(lines, path))
            if not unique_words:
                raise WordListError(f"Word list '{path}' contains no usable words.")
            self._words[difficulty] = tuple(unique_words)

    @staticmethod
    def _load_words(lines: list[str], path: Path) -> list[str]:
        words = []
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                words.append(normalize_word(line))
            except ValueError as exc:
                raise WordListError(
                    f"Invalid word in '{path}' at line {line_number}; "
                    "use one A–Z word per line."
                ) from exc
        return words

    def choose_word(self, difficulty: str) -> str:
        """Select uniformly from the requested list after validating difficulty."""
        return random.choice(self._words[normalize_difficulty(difficulty)])
