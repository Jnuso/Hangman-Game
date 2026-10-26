"""Controlled-word server for browser QA only; never use for normal play."""

import argparse
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from server import create_app
from word_manager import WordManager


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5055)
    args = parser.parse_args()
    with TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for level, word in (("easy", "apple"), ("medium", "guitar"), ("hard", "rhythm")):
            (directory / f"{level}.txt").write_text(word, encoding="utf-8")
        create_app(WordManager(directory)).run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
