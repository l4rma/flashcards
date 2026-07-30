import random
from dataclasses import dataclass

from fastapi import HTTPException

from app.models import Stats


@dataclass(frozen=True)
class TitleDef:
    key: str
    name: str
    rarity: str  # "common" | "rare" | "epic" | "legendary" — display only


@dataclass(frozen=True)
class ThemeDef:
    key: str
    name: str
    rarity: str
    # CSS custom-property overrides applied at the document root when this
    # theme is equipped (see frontend/src/collectionTheme.js) —
    # deliberately not duplicated as a second color list in the frontend
    # the way avatars.js mirrors AVATAR_KEYS: colors are richer here (3
    # values × 2 modes + an optional font) and only ever needed for the
    # *equipped* theme at a time, so the backend stays the single source
    # of truth and the frontend just applies whatever GET /collection says
    # is equipped.
    #
    # Two separate light/dark color sets, not one shared triple — each was
    # solved independently against WCAG AA (see index.css's dark-theme
    # comment for the audit that found the single-triple design failing
    # badly: a light-mode-tuned `primary-dark` used as text against a dark
    # page could fall as low as 1.33:1). `collectionTheme.js` picks
    # whichever set matches the current light/dark toggle and re-applies
    # automatically when that toggle changes.
    colors: dict[str, str]
    colors_dark: dict[str, str]
    font_display: str | None = None


TITLES: list[TitleDef] = [
    TitleDef("novice", "Vocabulary Novice", "common"),
    TitleDef("apprentice", "Grammar Apprentice", "common"),
    TitleDef("word_explorer", "Word Explorer", "common"),
    TitleDef("dedicated_student", "Dedicated Student", "common"),
    TitleDef("wordsmith", "Wordsmith", "rare"),
    TitleDef("fluent_friend", "Fluent Friend", "rare"),
    TitleDef("language_sage", "Language Sage", "rare"),
    TitleDef("polyglot_prodigy", "Polyglot Prodigy", "epic"),
    TitleDef("tongue_master", "Master of Tongues", "epic"),
    TitleDef("native_level_ninja", "Native-Level Ninja", "legendary"),
    TitleDef("legend_of_language", "Legend of Language", "legendary"),
]

THEMES: list[ThemeDef] = [
    ThemeDef(
        "ocean", "Ocean Blue", "common",
        {"primary": "#2779b7", "primary-dark": "#175e94", "primary-light": "#e8eef2"},
        {"primary": "#2779b7", "primary-dark": "#76b6e7", "primary-light": "#232f38"},
    ),
    ThemeDef(
        "sunset", "Sunset Coral", "common",
        {"primary": "#ca4a24", "primary-dark": "#a63614", "primary-light": "#f3eae8"},
        {"primary": "#ca4a24", "primary-dark": "#ed9980", "primary-light": "#392823"},
    ),
    ThemeDef(
        "lavender", "Lavender Dream", "common",
        {"primary": "#875dd0", "primary-dark": "#682ecc", "primary-light": "#ece9f2"},
        {"primary": "#875dd0", "primary-dark": "#d0beef", "primary-light": "#2c2537"},
    ),
    ThemeDef(
        "forest", "Deep Forest", "rare",
        {"primary": "#32834d", "primary-dark": "#1f6336", "primary-light": "#eaf1ec"},
        {"primary": "#32834d", "primary-dark": "#68cd89", "primary-light": "#27352b"},
    ),
    ThemeDef(
        "rose_gold", "Rose Gold", "rare",
        {"primary": "#b7575f", "primary-dark": "#a23942", "primary-light": "#f0eaea"},
        {"primary": "#b7575f", "primary-dark": "#e0aeb2", "primary-light": "#342729"},
    ),
    ThemeDef(
        "midnight", "Midnight", "epic",
        {"primary": "#686eb6", "primary-dark": "#434ba8", "primary-light": "#eaebf0"},
        {"primary": "#686eb6", "primary-dark": "#bbbee2", "primary-light": "#282934"},
        font_display="'Playfair Display', ui-serif, Georgia, serif",
    ),
    ThemeDef(
        "gold_leaf", "Gold Leaf", "legendary",
        {"primary": "#936f1a", "primary-dark": "#6d500d", "primary-light": "#f3efe8"},
        {"primary": "#936f1a", "primary-dark": "#e5b648", "primary-light": "#393223"},
        font_display="'Cormorant Garamond', ui-serif, Georgia, serif",
    ),
]


@dataclass(frozen=True)
class LootboxTierDef:
    key: str
    name: str
    coin_cost: int


LOOTBOX_TIERS: list[LootboxTierDef] = [
    LootboxTierDef("bronze", "Bronze Chest", 50),
    LootboxTierDef("silver", "Silver Chest", 150),
    LootboxTierDef("gold", "Gold Chest", 400),
]
LOOTBOX_TIER_KEYS = {tier.key for tier in LOOTBOX_TIERS}

# Reward category weights per tier. "title"/"theme" are dropped from the
# roll (not just given a 0 weight) once nothing new is left to award in
# that category, so a completionist never gets a wasted roll.
REWARD_WEIGHTS: dict[str, dict[str, int]] = {
    "bronze": {"coins": 60, "xp": 25, "title": 10, "theme": 5},
    "silver": {"coins": 40, "xp": 25, "title": 20, "theme": 15},
    "gold": {"coins": 20, "xp": 20, "title": 30, "theme": 30},
}
COIN_REWARD_RANGE: dict[str, tuple[int, int]] = {"bronze": (10, 30), "silver": (40, 80), "gold": (100, 200)}
XP_REWARD_RANGE: dict[str, tuple[int, int]] = {"bronze": (10, 30), "silver": (40, 80), "gold": (100, 200)}


def _unowned(defs: list, owned_keys: list[str]) -> list:
    return [d for d in defs if d.key not in owned_keys]


def roll_lootbox_reward(stats: Stats, tier: str) -> dict:
    """Rolls one reward from `tier`'s weighted table and applies it
    directly to `stats` (coins/xp/owned_titles/owned_themes) — the caller
    is responsible for persisting `stats` afterward (same
    mutate-then-save_stats pattern as the rest of stats.py), and for
    re-running achievement/level-up checks since a coin or xp reward here
    can trigger either, same as any other coin/xp-earning action.
    Returns a small dict describing what was won, for the reveal UI."""
    weights = dict(REWARD_WEIGHTS[tier])
    unowned_titles = _unowned(TITLES, stats.owned_titles)
    unowned_themes = _unowned(THEMES, stats.owned_themes)
    if not unowned_titles:
        weights.pop("title", None)
    if not unowned_themes:
        weights.pop("theme", None)

    category = random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]

    if category == "title":
        won = random.choice(unowned_titles)
        stats.owned_titles.append(won.key)
        return {"kind": "title", "key": won.key, "name": won.name}
    if category == "theme":
        won = random.choice(unowned_themes)
        stats.owned_themes.append(won.key)
        return {"kind": "theme", "key": won.key, "name": won.name}
    if category == "xp":
        low, high = XP_REWARD_RANGE[tier]
        amount = random.randint(low, high)
        stats.xp += amount
        return {"kind": "xp", "amount": amount}

    low, high = COIN_REWARD_RANGE[tier]
    amount = random.randint(low, high)
    stats.coins += amount
    stats.lifetime_coins_earned += amount
    return {"kind": "coins", "amount": amount}


def buy_lootbox(stats: Stats, tier: str) -> None:
    tier_def = next((t for t in LOOTBOX_TIERS if t.key == tier), None)
    if tier_def is None:
        raise HTTPException(status_code=404, detail=f"Unknown lootbox tier {tier!r}")
    if stats.coins < tier_def.coin_cost:
        raise HTTPException(status_code=400, detail="Not enough coins")
    stats.coins -= tier_def.coin_cost
    _set_lootbox_count(stats, tier, _get_lootbox_count(stats, tier) + 1)


def open_lootbox(stats: Stats, tier: str) -> dict:
    if tier not in LOOTBOX_TIER_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown lootbox tier {tier!r}")
    if _get_lootbox_count(stats, tier) <= 0:
        raise HTTPException(status_code=400, detail="No lootboxes of this tier to open")
    _set_lootbox_count(stats, tier, _get_lootbox_count(stats, tier) - 1)
    stats.lootboxes_opened += 1
    return roll_lootbox_reward(stats, tier)


def _get_lootbox_count(stats: Stats, tier: str) -> int:
    return getattr(stats, f"lootbox_{tier}")


def _set_lootbox_count(stats: Stats, tier: str, value: int) -> None:
    setattr(stats, f"lootbox_{tier}", value)


def equip_title(stats: Stats, title_key: str | None) -> None:
    if title_key is not None and title_key not in stats.owned_titles:
        raise HTTPException(status_code=400, detail="Title not owned")
    stats.equipped_title = title_key


def equip_theme(stats: Stats, theme_key: str | None) -> None:
    if theme_key is not None and theme_key not in stats.owned_themes:
        raise HTTPException(status_code=400, detail="Theme not owned")
    stats.equipped_theme = theme_key


def describe_collection(stats: Stats) -> dict:
    """Builds the GET /collection payload: every title/theme definition
    annotated with owned/equipped, plus lootbox tier info + current
    inventory counts."""
    return {
        "titles": [
            {
                "key": t.key,
                "name": t.name,
                "rarity": t.rarity,
                "owned": t.key in stats.owned_titles,
                "equipped": t.key == stats.equipped_title,
            }
            for t in TITLES
        ],
        "themes": [
            {
                "key": t.key,
                "name": t.name,
                "rarity": t.rarity,
                "colors": t.colors,
                "colors_dark": t.colors_dark,
                "font_display": t.font_display,
                "owned": t.key in stats.owned_themes,
                "equipped": t.key == stats.equipped_theme,
            }
            for t in THEMES
        ],
        "lootboxes": [
            {
                "tier": t.key,
                "name": t.name,
                "coin_cost": t.coin_cost,
                "count": _get_lootbox_count(stats, t.key),
            }
            for t in LOOTBOX_TIERS
        ],
    }
