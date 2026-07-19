# Preset avatar set — semantic keys, not raw emoji, so swapping these for
# real custom SVGs later (see TASKS.md Phase 16, blocked on artwork) is a
# rendering change on the frontend only, not a data migration. The
# frontend owns the key -> emoji/icon mapping; the backend only needs to
# know which keys are valid.
AVATAR_KEYS = [
    "fox",
    "cat",
    "dog",
    "rabbit",
    "owl",
    "panda",
    "koala",
    "lion",
    "tiger",
    "bear",
    "monkey",
    "penguin",
]

USERNAME_MAX_LENGTH = 24
