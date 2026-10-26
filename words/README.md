# Hangman word lists

These are original, manually curated starter lists assembled for this project
with AI assistance. They were not copied from the instructor's implementation
or downloaded from an external dictionary. Each list is intended to contain
40 entries. Phase 2 tests confirm each list has 40 unique lowercase ASCII words.

- **Easy:** familiar everyday objects, animals, and nature words, mostly short
  and with common letter patterns.
- **Medium:** generally longer familiar words with more varied letters.
- **Hard:** unusual letter combinations, uncommon letters, or limited vowels.
  Some are short: `lynx` and `rhythm` illustrate why length alone does not
  determine difficulty.

Difficulty is a curated gameplay choice, not an experimentally measured ranking.
The lists are deliberately small starting resources and can be expanded later.
Every difficulty allows the same six incorrect guesses.

## File format and loading

Use UTF-8 text, with one English A–Z word per line. The loader accepts a UTF-8
byte-order mark, strips surrounding whitespace, converts uppercase to lowercase,
skips blank lines, and removes duplicates within each difficulty. Entries with
spaces, punctuation, digits, or non-ASCII letters cause a clear file/line error
rather than being silently discarded. Missing, unreadable, or empty lists also
raise `WordListError`.

The server will select words from these files, but the directory must not be
served as browser assets. The API must not disclose the selected word while a
game is playing. Public repository access to the candidate lists does not
identify the randomly selected answer for a particular active game.
