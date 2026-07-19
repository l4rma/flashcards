from dataclasses import dataclass
from pathlib import Path

# Dev-authored content, not user data — a plain text file per deck, living
# right alongside this parser (add a new .txt here to add a new deck; no
# code change needed). Parsed once at import time into an in-memory list —
# same "static content in code" idea as achievements.py/quests.py, just
# sourced from bundled text files instead of Python literals, since
# curated word lists read far more naturally as data than as
# ACHIEVEMENTS-style Python calls. Deliberately has NO Cards-table
# involvement — see SPEC.md's Open decisions #11: these are non-owned,
# browsable practice content, not something you import into your own deck.
DECKS_DIR = Path(__file__).parent

# Format (see any .txt file in this directory for a real example):
#   # comment lines and blank lines are ignored
#   <deck title>              <- first non-comment, non-blank line
#   english | french          <- one card per subsequent line
#   ...
# A malformed line (no "|") is skipped rather than failing the whole
# deck, so one typo in a large hand-edited file doesn't take the rest
# down with it.


@dataclass(frozen=True)
class PrebuiltCard:
    english: str
    french: str


@dataclass(frozen=True)
class PrebuiltDeck:
    key: str
    title: str
    cards: list[PrebuiltCard]


def _parse_deck_file(path: Path) -> PrebuiltDeck:
    title: str | None = None
    cards: list[PrebuiltCard] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if title is None:
            title = line
            continue
        if "|" not in line:
            continue
        english, _, french = line.partition("|")
        english, french = english.strip(), french.strip()
        if english and french:
            cards.append(PrebuiltCard(english=english, french=french))
    return PrebuiltDeck(key=path.stem, title=title or path.stem, cards=cards)


def _load_decks() -> list[PrebuiltDeck]:
    return [_parse_deck_file(path) for path in sorted(DECKS_DIR.glob("*.txt"))]


DECKS: list[PrebuiltDeck] = _load_decks()


def get_deck(key: str) -> PrebuiltDeck | None:
    return next((deck for deck in DECKS if deck.key == key), None)
