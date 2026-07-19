# Flash Cards App — Tasks

Phased, spec-driven task list. Work through phases in order; each phase
should leave the app in a working, demoable state. See `SPEC.md` for the
design these tasks implement.

## Phase 0 — Project scaffolding
- [x] Set up backend project structure (FastAPI app, SQLAlchemy, SQLite)
- [x] Set up frontend project structure (React + Vite)
- [x] Basic README with how to run backend + frontend locally
- [x] `CLAUDE.md` at repo root: commands, architecture gotchas (manual
      SQLite migrations, singleton `Stats`, frontend-only session queue),
      and the check-spec/update-spec workflow itself

## Phase 1 — Backend core (local, SQLite)
- [x] `Card` model/table (`id`, `french`, `english`, `interval_days`,
      `due_date`, `created_at`, `last_reviewed_at`)
- [x] `POST /cards` — create card
- [x] `GET /cards` — list all cards
- [x] `GET /cards/due` — list due cards
- [x] `PATCH /cards/{id}` — edit card text
- [x] `DELETE /cards/{id}` — delete card
- [x] `POST /cards/{id}/grade` — apply scheduling algorithm (wrong/correct)

## Phase 2 — Frontend core (talking to local backend)
- [x] Add Card page/form — fields relabeled "Front"/"Back" (was
      "French"/"English"), reordered to match, placeholders "hello"/
      "bonjour" (was "chat"/"cat")
- [x] Manage Cards list (view/edit/delete) — simple table, no styling focus yet
- [x] Train page:
  - [x] Pull due cards into a session queue on start
  - [x] Show English word (front), flip on click to reveal French (back)
        — originally French-front/English-back, reversed per explicit
        request; see SPEC.md Open decisions
  - [x] Wrong / Correct buttons wired to `POST /cards/{id}/grade`
  - [x] Requeue Wrong cards within the session; drop Correct cards
  - [x] "Session complete" state when queue empties
- [x] Manual end-to-end pass: add a handful of real French/English pairs,
      run a training session, confirm scheduling behaves as expected

## Phase 3 — Make it look nice
- [x] Pick a lightweight styling approach — Tailwind CSS v4, custom theme
      per `DESIGN.md` (sage green, cream, rounded, Nunito)
- [x] Polish Add Card, Manage Cards, and Train pages
- [ ] Basic responsive layout (usable on phone + desktop) — layout is
      mobile-first/narrow by construction, verified via emulated viewports
      (375px/420px/1280px) during the redesign below, but still not
      verified on a real physical phone
- [x] Nav bar redesign: its own visual identity (pale-green `primary-light`
      fill + darker-green `primary` bottom border, both already in the
      palette — no new colors) instead of blending into the cream page
      background. Tabs switched from text labels to icon-only emoji
      buttons (🏋️ Train, 📚 Deck, 📈 Progress, ⚙️ Admin), each keeping an
      `aria-label`/`title` for accessibility. See `DESIGN.md` Navigation
      section
- [x] Combined **Add Card** + **Manage Cards** into one **Deck** page/tab
      (`DeckPage.jsx`) — add form pinned at top, manage list below,
      refreshes automatically after adding. `AddCardPage.jsx`/
      `ManageCardsPage.jsx` deleted (merged, not kept around unused)
- [x] Nav tab shape changed from circular (`rounded-full`) to a rounded
      square (`rounded-2xl`), per explicit request — the one spot in the
      app that deliberately doesn't use the pill-button shape
- [x] Admin page no longer shows a streak/coins/due-count summary — it
      duplicated the Progress page for no reason. `AdminPage.jsx` dropped
      its `getStats` fetch and loading state entirely, now just renders
      the two action buttons directly
- [x] **Full redesign** (mid-2026, well after the rest of this phase —
      user asked for a visual overhaul post-AWS-migration, using the
      `frontend-design` skill): nav moved to a floating pill bar fixed to
      the viewport bottom (**supersedes** the "rounded-2xl square tabs"
      bullet above — tabs are `rounded-full` again now that the bar itself
      is a pill, kept universal across mobile/desktop rather than
      switching to a top bar above some breakpoint), paired **Fraunces**
      (serif, vocabulary words/headings/stat numbers) with the existing
      **Nunito** (UI chrome) for real type contrast, added a running
      "index card" motif (punch-hole detail, stacked receding card edges
      behind the active `FlipCard` sized to the queue depth, tilted rows
      in the deck list), and restructured Progress's stats into one
      unified stat strip instead of stacked paragraph-in-a-box sections.
      Palette unchanged — see `DESIGN.md` for the full rationale.
      Verified visually via a throwaway Playwright harness (mocked
      auth/API, never committed) across phone/desktop/small-phone
      viewports and every page's interactive states (flipped card,
      session-complete, achievement modal); `npm run build` + `oxlint`
      both clean.
- [x] **Bug fix**: 🪙 coin emoji rendered inconsistently across
      platforms — user reported gold on desktop, a flat silver/"moon-like"
      disc on their phone. Root cause: emoji glyphs are drawn by each OS's
      own emoji font (Apple vs. Google's artwork for this exact character
      genuinely differ), not something CSS can control. Fixed by replacing
      all 5 usages (`StatsBar`, `ProgressPage`'s stat strip/quest reward
      badges/achievement modal, `CelebrationModal`) with a custom inline
      SVG (`components/CoinIcon.jsx`, new `--color-coin`/`--color-coin-dark`
      theme tokens) — renders identically on every device, and its center
      rule line echoes the same "ruled index card" motif from the redesign
      above rather than being generic coin clip-art.
- [ ] **Future**: replace the rest of the app's emoji (🔥 streak, 📚/📈/⚙️
      nav icons, all achievement/quest badges) with custom SVG icons too,
      same reasoning as the coin fix above (cross-platform emoji rendering
      is inconsistent by nature) — user's explicit request, not yet
      started. Larger scope than the coin fix: achievement/quest badges
      alone are a couple dozen distinct icons (see `achievements.py`/
      `quests.py`), so this is a real design pass, not a quick swap.
- [x] **Togglable dark theme** (user request, using the `frontend-design`
      skill again): Light/Auto/Dark toggle on the Admin page
      (`components/ThemeToggle.jsx` + `ThemeIcon.jsx` — custom SVGs, not
      sun/moon emoji, consistent with the coin-icon reasoning above),
      persisted in `localStorage` (`theme.js`), defaulting to "Auto"
      (`prefers-color-scheme`, stays live if the OS theme changes
      mid-session). A tiny inline script in `index.html` applies the class
      synchronously pre-paint to avoid a flash-of-wrong-theme. Implemented
      as a single `html.dark { --color-*: ... }` override block in
      `index.css` — since every color in the app already flows through
      these named tokens, this needed **zero component-level color
      changes**; only fix needed was adding `ring-1 ring-ink/10` to every
      surface card, since plain `shadow-md`/`shadow-lg` alone (Tailwind's
      default near-black shadow color) stopped giving visible card edges
      once the background itself went dark. See `DESIGN.md`'s new "Dark
      theme" section for the full palette/rationale (warm "lamplight" dark,
      not a cold inverted tech palette; several tokens deliberately swap
      which end of light/dark they resolve to rather than inverting
      uniformly). Verified visually (light + dark, all pages/modals) via
      the same throwaway Playwright harness pattern as the earlier
      redesign; `npm run build` + `oxlint` both clean.

## Phase 4 — Gamification: streak + coins
- [x] `Stats` singleton model/table (`coins`, `current_streak`,
      `longest_streak`, `last_active_date`)
- [x] Streak logic on every grade (Wrong or Correct both count): first-ever
      grade → streak 1; same day again → no change; exactly one day since
      last active → streak += 1; bigger gap → streak resets to 1
- [x] Coins: +1 on Correct, 0 on Wrong (`COINS_PER_CORRECT`, originally 10,
      rebalanced down); no spend target yet
- [x] Wire into `POST /cards/{id}/grade` as a side effect
- [x] `GET /stats` endpoint
- [x] Unit tests for streak logic (consecutive days, same-day idempotency,
      gap resets, longest-streak tracking)
- [x] Frontend stats bar (🔥 streak, 🪙 coins) visible on all pages,
      refreshed after each grade in Train
- [x] Session progress bar (purple) above the card in Train, tracking
      fraction of today's due queue cleared — advances only on Correct,
      reaches 100% exactly when the queue empties
- [x] Session-complete bonus: flat `SESSION_COMPLETE_BONUS` (10) coins when
      the due queue empties (originally scaled `4 + current_streak`,
      simplified to flat); `POST /stats/session-complete` endpoint, called
      once by the frontend at that moment
- [x] Unit test for the flat session-complete bonus (no longer scales with
      streak)
- [x] `session_initial_due` frozen once/day on `Stats` (not recomputed from
      the live due-count) so the progress bar survives a page refresh
      mid-session
- [x] Admin page: two actions only — **Reset all progress** (`POST
      /reset-all-progress`: streak + coins + session baseline + every
      card's scheduling + all achievement unlocks in one action) and
      **Delete ALL cards** (`DELETE /cards`), each behind a confirm dialog.
      Originally four separate reset buttons (reset streak / reset coins /
      reset all stats / reset training progress); consolidated down to one
      since the granularity wasn't needed in practice — the now-unused
      `reset_streak`/`reset_coins`/`reset_session_tracking` functions and
      their endpoints were deleted rather than kept around unused
- [x] Per-card lifetime `times_correct`/`times_wrong` counters, incremented
      on every grade; **also cleared** by "Reset all progress" (reversed
      from an earlier "survives resets" design — see Phase 5 below and
      SPEC.md Open decisions for why)
- [x] Manage Cards page: header shows total card count + how many aren't
      yet correct this session; each row shows lifetime ✓/✗ counts
      (English/front word first, French/back below it, matching Train's
      front/back order; edit inputs reordered + placeholder-labeled to
      match)
- [x] `backend/seed_data.py`: verb list reordered to (english, french) pairs
      to read front-to-back, matching the flip order — the underlying
      `Card(french=..., english=...)` field assignment was already correct
      either way, this was purely for script readability

## Phase 5 — Gamification: achievements
- [x] `AchievementUnlock` table (one row per unlocked achievement; key +
      timestamp) — definitions live in code (`app/achievements.py`), not DB
- [x] `Stats.lifetime_coins_earned` / `Stats.sessions_completed` — permanent
      lifetime records for achievement conditions, deliberately not reset
      by any admin reset action (same pattern as per-card lifetime counters)
- [x] `Stats.current_correct_streak` / `Stats.longest_correct_streak` —
      consecutive Correct grades (any Wrong resets current to 0), tracked
      in `record_training_activity` alongside the existing daily streak
- [x] `Stats.session_had_wrong`/`flawless_sessions_completed` (Flawless
      Session), `largest_session_completed` (Marathon, high-water mark of
      `session_initial_due` at actual completion time), `comebacks`
      (Comeback Kid — needs `Card.last_grade` to detect wrong-then-correct),
      `cards_mastered` (Word Master — needs `Card.mastered`, flipped in
      `apply_grade` when `interval_days` crosses
      `scheduling.MASTERY_THRESHOLD_DAYS` = 64), `trained_before_7am`/
      `trained_after_11pm` (Early Bird/Night Owl, local wall-clock time via
      an optional `now` param on `record_training_activity`)
- [x] 53 achievement tiers across 10 families/standalones: streak
      7/30/60/100/365, lifetime correct, lifetime coins 10/100/500, deck
      size 1/10/30/50/100/250/500, session-complete
      1/5/10/25/50/100/250/500, correct-in-a-row 3/5/10/25/50/100, word
      mastery 1/5/10/25/50, marathon 25/50/100/200, first wrong answer,
      flawless session, comeback kid, early bird, night owl — see SPEC.md
      for the full list
- [x] Checked after grading a card, adding a card, and completing a session;
      idempotent. Admin's "Reset all progress" clears achievement unlocks
      *and* (after a real bug report — see below) the underlying lifetime
      stats they check, so a reset is a genuine full reset rather than
      something that re-unlocks itself on the next action
- [x] **Bug fix**: reset originally left lifetime achievement-tracking
      fields untouched (`lifetime_coins_earned`, `sessions_completed`,
      `cards_mastered`, `comebacks`, `longest_correct_streak`, time-of-day
      flags, per-card `times_correct`/`times_wrong`/`mastered`) so
      achievements would "survive" a reset. User-reported symptoms: visible
      `coins` balance permanently drifting below `lifetime_coins_earned`
      (which achievements actually check), and achievements like "Flawless
      Session" showing unlocked after just adding a card, no session ever
      completed. Fixed by having `reset_all_stats`/`reset_card_progress`
      zero these fields too. One unavoidable exception remains: deck-size
      achievements can still show nonzero progress right after a reset,
      since this action doesn't delete cards (only "Delete ALL cards" does)
- [x] `AchievementDef.coin_reward`: 10 for the easiest/first tier of a
      family (or standalone achievements, set explicitly), scaling up per
      tier position via `REWARD_BY_TIER_INDEX` (20/35/60/100/150/250/400).
      Applied in `check_and_unlock_achievements`, which snapshots all
      conditions *before* applying any reward in that pass — otherwise one
      achievement's reward could spuriously push a coin-threshold
      achievement over target within the same check (a real bug caught by
      a test: unlocking `streak_7` mid-loop was pushing `coins_10` over its
      threshold in the very same pass). Cross-call cascades (an earlier
      unlock's reward genuinely qualifying a coin achievement on the *next*
      grade) are expected and fine
- [x] `GET /achievements` endpoint, includes `progress_current`/
      `progress_target`/`coin_reward` per achievement (progress capped at
      target)
- [x] Tiered families (streak, correct, coins, deck) collapsed via
      `AchievementDef.family` to **at most two** grid entries: the highest
      completed tier (colored, `history` lists earlier completed tiers) and
      the next not-yet-unlocked tier (dimmed, own live progress) — one tile
      if nothing's unlocked yet or the ladder is fully complete, otherwise
      two. Collapsing happens at read-time in `list_achievements`, doesn't
      affect unlock-checking (`check_and_unlock_achievements` still checks
      every tier independently)
- [x] Unit tests: unlock conditions, idempotency, permanence after a stat
      reset, `clear_achievements`, progress values, two-tile family
      collapsing (partial ladder and fully-completed ladder cases)
- [x] **New "Progress" page** (frontend): streak/coins/session summary,
      extra stats (total cards, total correct/wrong, accuracy %), and an
      achievement grid — emoji badges for now (real art later), locked
      ones dimmed, click for a popup with description, a progress bar
      (current/target), unlock date/time if unlocked, and (completed tile
      of a tiered family only) a "Previously completed" list of earlier
      tiers
- [x] Daily quests — `app/quests.py`: `QuestDef` (same shape as
      `AchievementDef`), static `DAILY_QUESTS` list (Deck Builder: add 5
      cards today; Daily Training: originally "complete today's session" —
      redesigned since, see below). `DailyQuestCompletion` table (one row
      per `quest_key` + `completed_date`) gates each quest's coin reward to
      once/day, mirroring `AchievementUnlock`. `check_and_complete_quests`
      uses the same snapshot-then-reward two-phase pattern as
      `check_and_unlock_achievements`. `GET /quests` endpoint. Admin's
      "Reset all progress" also clears quest completions
      (`clear_quest_completions`). New "Daily Quests" box on the Progress
      page, directly under the streak/coins summary. 9 unit tests + 3 API
      tests
- [x] **Bug fix**: the "add cards" quest originally computed progress live
      from `Card.created_at` (count of cards created today) instead of a
      stored counter. User-reported symptom: after a DB reseed (forced by
      this feature's own schema change), the quest showed as already
      completed on first load, because the 25 seeded verbs got inserted
      with today's timestamp — `seed_data.py` bypasses `POST /cards`
      entirely, so a live timestamp-based count can't distinguish "added
      through the app today" from "exists with today's date for any
      reason." Fixed by adding `Stats.quest_cards_added_today`, incremented
      only by `record_quest_card_added` from the real `POST /cards`
      endpoint — mirrors how the training quest already worked. Also fixes
      a secondary issue this caused: previously, admin's "Reset all
      progress" couldn't actually reset this quest's progress either (cards
      aren't deleted by that action), so it could show as instantly
      re-completed after a same-day reset — now a genuine `Stats` counter,
      it resets correctly. Regression test added
      (`test_bulk_inserted_cards_do_not_count_toward_add_cards_quest`).
      Required a manual `ALTER TABLE stats ADD COLUMN
      quest_cards_added_today ...` against the live `flashcards.db` (per
      the no-Alembic gotcha in `CLAUDE.md`) since the app was already in
      real use with real seeded data at this point, not just dev fixtures
- [x] **Redesign**: Daily Training changed from "complete today's session"
      (boolean) to "get 10 cards correct today, or fewer if fewer are due"
      — a numeric countdown using the exact same daily-frozen baseline as
      the Train page's own progress bar (`min(10, session_initial_due)`),
      per explicit request that both bars count down identically.
      `QuestDef.target` changed from a fixed `int` to a
      `Callable[[Stats], int]` to support this (only `daily_train`'s target
      actually varies; `daily_add_cards`' is a lambda returning the
      constant). Added `Stats.quest_correct_today` (replaces the deleted
      `quest_session_completed_today`), incremented by
      `record_quest_correct_grade` on every Correct grade in
      `POST /cards/{id}/grade`. `sync_quest_day` now also calls
      `stats.sync_session` itself (computing today's due count) so
      `session_initial_due` is correctly frozen regardless of whether the
      Train or Progress page loads first that day. Required a manual
      `ALTER TABLE stats ADD COLUMN quest_correct_today ...` +
      `ALTER TABLE stats DROP COLUMN quest_session_completed_today` against
      the live `flashcards.db` (SQLite 3.46 supports `DROP COLUMN`).
      Caught and fixed a related ordering bug during this change:
      `record_quest_card_added` must run *after* `POST /cards`'s first
      `db.commit()`, not before — with `autoflush=False` in the test
      session, its internal due-count query couldn't see the just-added
      card otherwise, freezing `session_initial_due` one card short. 9 unit
      tests updated, 1 API test updated + 1 new
- [x] **Fix**: Daily Training's target was 0 (trivially "complete") on a day
      with no cards due — user-reported. Added `Stats.quest_train_floor`
      (`app/quests.py`'s `TRAIN_FLOOR_START`/`_GROWTH`/`_MAX` = 5/5/50),
      target now `max(quest_train_floor, min(10, session_initial_due))`.
      Floor grows +5 on each new calendar day (`Stats.sync_day`, skipping
      day one), deliberately outgrowing a small deck's natural due count —
      an explicit, accepted trade-off per the user ("it will just make you
      want to create a bigger deck"), not a bug to guard against. Reset by
      "Reset all progress" back to 5. 6 new/updated backend tests (103→106
      total), deployed (Lambda code update only, no infra change).
- [x] **Reverted**: Daily Training's target is now a flat, always-10
      `TRAIN_TARGET` constant, per explicit request — no longer adaptive to
      `session_initial_due`, no more growing floor. `Stats.quest_train_floor`
      and `app/quests.py`'s `TRAIN_FLOOR_START`/`_GROWTH`/`_MAX` removed
      entirely (DynamoDB needs no migration for the drop — old items just
      keep the now-unread attribute). Description text changed to
      "Practice 10 cards in Train." Accepted trade-off, reversing the
      previous fix's whole point: this quest can now go uncompleted on a
      day with fewer than 10 cards due — deliberate, not a regression.
      Frontend-only change otherwise (the Train page's progress bar reads
      the same `GET /quests` data, so it picks up the flat 10
      automatically, no `TrainPage.jsx` edit needed). Removed the
      floor-growth tests in `test_stats.py` (they tested a mechanism that
      no longer exists) and updated the affected `test_quests.py`/
      `test_api.py` assertions — 101 backend tests pass.
- [x] Achievement-unlock celebration — confetti (`canvas-confetti`, new
      frontend dependency, ~3KB) + a modal ("Grats! You earned an
      achievement!", badge, title, description, coin reward) whenever an
      achievement is newly unlocked. Backend: `achievements.describe_achievements(keys)`
      looks up display info for a list of keys; `POST /cards`,
      `POST /cards/{id}/grade`, and `POST /stats/session-complete` now
      capture `check_and_unlock_achievements`'s previously-discarded return
      value and attach it as `newly_unlocked_achievements` on their
      response (`CardOut`/`StatsOut` both gained this field, default `[]`
      so every other endpoint returning those types is unaffected). No new
      endpoint — reuses the existing three action responses since that's
      the only place an unlock can happen. 3 new API tests
- [x] Extended the celebration to daily quest completions too. Backend:
      `quests.describe_quests(keys)` (mirrors `describe_achievements`);
      `CardOut` gained `newly_completed_quests: list[QuestCompletionNotice]`
      (only `POST /cards`/`POST /cards/{id}/grade` — quests don't complete
      via session-complete). Frontend: renamed
      `AchievementUnlockModal.jsx` → `CelebrationModal.jsx` since
      `AchievementUnlockNotice`/`QuestCompletionNotice` have the identical
      shape — takes a `celebration` object tagged `kind: "achievement" |
      "quest"` to pick the heading text ("Grats! You earned an
      achievement!" vs "Quest complete!"). `App.jsx`'s queue renamed
      `unlockQueue` → `celebrationQueue`, now fed by both
      `onAchievementsUnlocked` and a new `onQuestsCompleted` callback
      threaded through `TrainPage`/`DeckPage`. 2 new API tests
- [x] **Bug fix**: Early Bird / Night Owl time-of-day achievements. Night
      Owl was `hour >= 23` only, so training right after midnight (e.g.
      00:19) didn't count as "late" — and incorrectly satisfied Early
      Bird's old `hour < 7` instead. User-reported (still missing Night
      Owl at 00:18); confirmed not a timezone issue (`datetime.now()`
      correctly matched the system's real `Europe/Oslo` clock). Fixed:
      `EARLY_BIRD_START_HOUR = 4` added; Early Bird is now
      `[4am, 7am)`, Night Owl is `[11pm, 4am)` (`hour >= 23 or hour < 4`) —
      adjacent, non-overlapping windows. Descriptions updated to match. 2
      new regression tests (midnight-crossing Night Owl, Early Bird not
      firing before 4am)
- [x] **Bug fix**: Progress page's top summary box showed "Due cards
      today: {session_initial_due}" — user-reported as "not updating"
      because that's exactly what it's designed to do (frozen once per
      day for the Train page's progress bar baseline, not a live due
      count — see Session progress bar), so it looked stuck/wrong on the
      one page that otherwise shows live numbers. Replaced with 📚 total
      card count (`cards.length`, matches the 🔥/🪙 emoji-prefixed style of
      Streak/Coins above it) — a number that's actually meant to be
      static-ish and update only when cards are added/deleted, unlike the
      daily session baseline.
- [ ] Chests — reward-opening mechanic; first real coin sink (not yet
      scoped)

## Phase 6 — Local network access (Docker) — RETIRED

Superseded by the AWS migration (Phase 7): the user decided local dev and
Docker no longer need to work at all ("testing in prod" — deploys go
straight to the real AWS environment, which is the only environment
tested against going forward; no CI/CD pipeline yet, deploys are manual,
see Phase 7). `docker-compose.yml`, `backend/Dockerfile`,
`frontend/Dockerfile`, and `frontend/nginx.conf` were deleted. Kept below
as a historical record of real problems solved (the nginx/Docker DNS saga
in particular took three failed attempts) — don't reintroduce Docker for
this app without re-reading why these were abandoned, not just the fact
that they were.

- [x] `backend/Dockerfile` — uvicorn on 0.0.0.0:8000
- [x] `frontend/Dockerfile` — multi-stage: `npm run build`, served by nginx
- [x] `frontend/nginx.conf` — proxies `/api/*` to the backend container
      (same relative-URL convention as the Vite dev proxy, so no frontend
      code changes needed)
- [x] `docker-compose.yml` at repo root; `backend/data/` bind-mounted so
      SQLite persists across rebuilds (moved from `backend/flashcards.db`
      to `backend/data/flashcards.db` for safer volume-mounting — mounting
      a directory avoids Docker's "creates a directory in place of a
      missing file" bind-mount gotcha)
- [x] Verified: both images build, containers start, nginx proxy reaches
      the backend, and existing card data survives via the bind mount
- [x] README instructions for LAN access from another device (e.g. phone)
- [x] Fixed: backend's host port mapping (8000:8000) conflicted with a
      locally-running dev `uvicorn` on the same port, making `docker
      compose up` fail immediately with "address already in use" on a
      fresh attempt. Backend is no longer exposed to the host by default
      (nginx reaches it over the internal Docker network regardless) —
      confirmed both can now run simultaneously without conflict.
- [x] **Confirmed working on the user's machine** after the port-conflict
      fix above — real-world testing surfaced three rounds of Docker
      networking bugs before that (static `proxy_pass` racing container
      startup → a resolver-based fix that was intermittently flaky under
      real use → a custom `nc`-based wait script that worked in this
      sandbox but couldn't resolve `backend` at all on the user's own
      machine). Current state: plain static `proxy_pass` (simplest possible
      nginx.conf) + `restart: unless-stopped` on both services. Full
      history in `CLAUDE.md` Rules section — don't reintroduce either
      abandoned approach.
- [x] Backend healthcheck removed entirely (tried polling `GET /cards`,
      then a dedicated `GET /health`, then widening the interval 5s → 30s
      — user correctly pushed back that a recurring check "just to run a
      backend and frontend together" shouldn't be needed at all). Verified
      by testing: 5/5 clean full teardown/recreate cycles succeeded with
      no healthcheck, using only plain `depends_on: - backend` (ordering,
      no health condition) + `restart: unless-stopped` on `frontend` — the
      same restart policy that was already doing the real work of
      recovering from a lost startup race. The `/health` endpoint was
      removed too since nothing calls it anymore.
- [x] **Bug fix**: backend container's clock was UTC, not the host's real
      timezone — broke every local-wall-clock-time check (daily streak
      rollover, Early Bird/Night Owl) by up to several hours depending on
      the host's offset from UTC. Confirmed via `docker exec
      flash-cards-backend-1 date` vs the host's `date` (2 hours apart for
      `Europe/Oslo` in summer). User-reported as "Night Owl achievement not
      unlocking" — the host-machine dev server never showed this symptom
      since it isn't containerized, which is what made it non-obvious.
      Fixed by bind-mounting the host's resolved `/etc/localtime` read-only
      into the backend service (`- /etc/localtime:/etc/localtime:ro` in
      `docker-compose.yml`) — no hardcoded zone name, works on any host.
      Required recreating the backend container (`docker compose up -d
      --no-deps backend`) to pick up the new mount; card data untouched
      (separate bind mount, unaffected by the recreate).

## Phase 7 — AWS deployment (Terraform + Cognito + Lambda + DynamoDB)

Went through two design passes before landing here — see SPEC.md's Tech
stack / Open decisions #9 for why ECS+ALB+RDS and a plain EC2 instance
were both considered and not chosen. No local/Docker deployment target
exists anymore (Phase 6, above) — this is the only environment.

### Backend rewrite (multi-tenancy + DynamoDB port, done together)
- [x] `Card`/`Stats` became plain dataclasses (`app/models.py`) — no ORM.
      `Card` gained `user_id`; `Stats` changed from a hardcoded singleton
      (`id=1`) to one item per user (PK `user_id`).
- [x] `app/database.py` rewritten: boto3 `Store` (bundles the 4 table
      resources + a **separate plain low-level client** for
      `transact_write_items` — see `CLAUDE.md` Rules for the
      double-serialization gotcha this avoids), `serialize_item` helper,
      `create_tables` (used by tests against moto; real tables come from
      Terraform).
- [x] `app/cards.py` (new) — DynamoDB Card CRUD: `Cards` table, PK
      `user_id`/SK `id`, GSI `due-index` (PK `user_id`/SK `due_date`) for
      due-card queries. Addressing a card by `Key={user_id, id}` closes
      the `_get_card_or_404` IDOR class of bug by construction, not by
      remembering a filter.
- [x] `app/stats.py` rewritten as **pure mutation functions** (no I/O
      except `get_or_create_stats`/`save_stats`) — a route fetches once,
      threads the same `Stats` object through every mutating call, saves
      once. `sync_session`/`quests.sync_quest_day` merged into one
      `stats.sync_day` (they always ran together anyway).
- [x] `app/achievements.py`/`app/quests.py` rewritten: `total_cards`/
      `total_correct`/`total_wrong` added to `Stats` as running counters,
      replacing the old live SQL-style aggregate (DynamoDB has no
      `SUM`/`COUNT` query) — incremented at the same call sites as every
      other counter. Achievement/quest unlock+reward is one
      `transact_write_items` call (Put per unlock/completion +
      **one** summed `Update ADD coins/lifetime_coins_earned` — a
      transaction can't include two operations on the same item, so
      simultaneous rewards are pre-summed in app code, not applied as
      separate `Update`s). Snapshot-before-reward invariant preserved.
      `list_achievements`/`list_quests`'s tiered-family-collapsing logic
      is pure Python over already-fetched data — confirmed completely
      unaffected by the storage backend, contrary to how risky it was
      originally assessed to be.
- [x] `app/auth.py` — no local-dev branch at all (none needed, since
      there's no local deployment target): reads the already-verified
      `sub` claim from the Lambda event API Gateway's JWT authorizer
      attaches (`request.scope["aws.event"]...`) — does no cryptographic
      verification itself, that already happened in API Gateway.
- [x] `app/main.py` — every route takes `user_id` from
      `Depends(get_current_user_id)`, threads it through; `handler =
      Mangum(app)` added (later gained `api_gateway_base_path="/api"` —
      see the CloudFront/API Gateway bug fixes further down).
- [x] `requirements.txt`: dropped `sqlalchemy`/`uvicorn`, added `mangum`,
      `boto3`, `moto[dynamodb]` (test-only).
- [x] Tests rewritten against **moto-mocked DynamoDB**
      (`tests/conftest.py`'s `store` fixture) — no real AWS access needed
      to run the suite. New cross-user isolation tests (cards/stats/
      achievements/quests invisible to and unaffected by another user;
      a reset by one user never touches another's rows). 100/100 passing.
- [x] `seed_data.py` deleted — no meaningful "local dev user" concept left
      to seed for once local dev was dropped entirely.
- [ ] `GET /health` — not added; API Gateway+Lambda doesn't need a
      target-group-style health check the way ALB did. Revisit only if a
      real monitoring/smoke-test need comes up.

### Terraform infrastructure
- [x] `terraform/bootstrap/` — S3 state bucket for Terraform's own state.
      No DynamoDB lock table — S3 has native state locking
      (`use_lockfile = true`, set in `versions.tf`'s backend block) as of
      Terraform 1.11+, replacing the older S3+DynamoDB pairing. `terraform
      plan` verified clean against the real AWS account for both this and
      the main config before either was applied (see Deployment below —
      both have since been applied and are live).
- [x] `terraform/dynamodb.tf` — 4 tables (`Cards` + `due-index` GSI,
      `Stats`, `Achievements`, `QuestCompletions`), On-Demand billing.
- [x] `terraform/lambda.tf` — function (zip-packaged), least-privilege IAM
      role scoped to exactly the 4 table ARNs and the operations actually
      used, CloudWatch log group.
- [x] `terraform/api_gateway.tf` — HTTP API, JWT authorizer (Cognito
      issuer + app client audience), single `$default` Lambda-proxy route
      (Mangum/FastAPI handle internal routing), auto-deploy stage.
- [x] `terraform/cognito.tf` — user pool, public SPA app client (PKCE,
      callback/logout URLs referencing the CloudFront resource directly),
      user pool domain. Self-signup open by default.
- [x] `terraform/frontend.tf` — private S3 bucket, CloudFront Origin
      Access Control, CloudFront distribution (default→S3, `/api/*`→API
      Gateway). **Caught two real bugs post-deployment, both now in
      `CLAUDE.md`'s Rules and conventions**: (1) a CloudFront Function
      stripping `/api` on `viewer-request` caused CloudFront to route using
      the *rewritten* path, silently falling through to the default (S3)
      behavior for every `/api/*` request — replaced with Mangum's
      `api_gateway_base_path="/api"` on the Lambda side instead, no
      CloudFront Function at all. (2) `Managed-AllViewer` origin request
      policy forwarded the viewer's own Host header to the API Gateway
      origin, which rejected it with a blanket 403 — switched to
      `Managed-AllViewerExceptHostHeader`.
- [x] `terraform/variables.tf`/`outputs.tf`/`providers.tf`/`versions.tf`/
      `data.tf` — region default `eu-north-1`. `terraform.tfvars.example`/
      `backend.hcl.example` document the values to copy and fill in.
- [x] `terraform init -backend=false && terraform validate` passes;
      `terraform plan` against the real AWS account (profile with valid
      credentials: `debian`) comes back clean — **24 resources to add, 0
      errors** — before any real `apply` was run.

### Frontend Cognito wiring
- [x] `frontend/src/auth.js` — PKCE Authorization Code flow: `login()`
      (redirect to Cognito's `/oauth2/authorize`), `handleRedirectCallback()`
      (exchange `?code=` for tokens), `logout()`, `getAccessToken()`. No
      hand-rolled silent refresh — a 401 just redirects to `login()` again.
- [x] `frontend/src/api.js` — attaches `Authorization: Bearer <token>`,
      redirects to `login()` on 401.
- [x] Auth-gate in `App.jsx` (redirect if no token/no `?code=`, exchange if
      present, "Signing in…" state during the round trip).
- [x] Logout action on the Admin page.
- [x] `frontend/.env.example` documents `VITE_COGNITO_DOMAIN`/
      `VITE_COGNITO_CLIENT_ID`/`VITE_REDIRECT_URI` (safe as public
      build-time values — public PKCE client, no secret). `npm run build`
      verified still succeeds.

### Lambda packaging
- [x] `backend/requirements-lambda.txt` (fastapi/mangum/pydantic —
      excludes boto3, which the Lambda Python runtime already bundles, and
      excludes pytest/httpx/moto, which are test-only).
- [x] `backend/build_lambda.sh` — `pip install --platform manylinux2014_x86_64`
      for the Lambda target, zips `app/` + deps into `backend/lambda.zip`.
      Verified: builds successfully, and the resulting package's
      `app.main.handler` imports cleanly.
- [x] `frontend/deploy.sh` — `npm run build`, `aws s3 sync`, CloudFront
      invalidation, reading bucket/distribution IDs from `terraform
      output`.

### Deployment
- [x] `terraform -chdir=terraform/bootstrap apply` (created the state
      bucket, `flash-cards-tfstate-362499c5`).
- [x] Copied `terraform/backend.hcl.example` → `backend.hcl` with the
      bootstrap outputs, `terraform init -backend-config=backend.hcl`.
- [x] `./backend/build_lambda.sh`, then `terraform apply` in `terraform/`
      (created all 24 resources).
- [x] Copied `frontend/.env.example` → `.env` with the `terraform output`
      Cognito values, ran `./frontend/deploy.sh`.
- [x] Diagnosed and fixed the two CloudFront/API Gateway bugs above via a
      mix of raw `aws cloudfront update-distribution` diagnostics (default
      behavior swap, temporary extra path pattern, temporarily removing
      `custom_error_response` to see unmasked errors) and a proper
      Terraform fix + apply once the root cause was confirmed. Verified:
      unauthenticated `GET /api/cards` through CloudFront now returns the
      same `401 {"message":"Unauthorized"}` as hitting API Gateway
      directly (previously masked as a 403 served from S3).
- [x] **End-to-end smoke test with two separate signed-up users** — user
      confirmed manually via the Hosted UI: two accounts, independent
      cards/coins/achievements each, no cross-user leakage on the real
      deployed stack.
- [x] **Version control**: `git init`, audited for secrets (none found —
      `.gitignore` already covered `.env`/`backend.hcl`/`.tfstate`/
      `.terraform/`/`lambda.zip`; one gap fixed, `terraform/bootstrap/` had
      no `.gitignore` of its own), pushed to a new private GitHub repo
      (`gh repo create flashcards --private --source=. --remote=origin
      --push`) at https://github.com/l4rma/flashcards. Local repo root
      later renamed `flash-cards` → `flashcards` to match (AWS resource
      names deliberately left as `flash-cards-*`, see `CLAUDE.md`'s Source
      control section).
- [ ] CI/CD (GitHub Actions or similar) to automate the above on push —
      mentioned as a goal but not yet scoped/built; natural next step now
      that the repo exists on GitHub and the first manual deployment is
      verified working.
- [ ] **Style the Cognito Hosted UI to match the app's look** (currently
      default AWS styling — user noticed and asked). Confirmed feasible,
      two options, not yet decided/started:
      1. **Managed Login branding** (`aws_cognito_managed_login_branding`
         Terraform resource — provider 5.100, already in use here, supports
         it) — a real branding config (primary color, background, logo,
         font, button/input corner radius) that could closely match
         `DESIGN.md`'s sage-green/cream/pill-button palette without
         hand-writing CSS. Requires switching the user pool domain to the
         newer "managed login" UI version first (one-time, reversible
         Terraform change, `aws_cognito_user_pool_domain`'s
         `managed_login_version`).
      2. **Classic Hosted UI CSS override** — inject raw CSS against AWS's
         fixed set of class names (`.background-customizable`,
         `.submitButton-customizable`, etc.) plus an optional logo image.
         Older mechanism, more fiddly/limited (can only re-skin existing
         elements, no layout changes), but doesn't touch the domain's UI
         version.

### Post-launch polish
- [x] **Duplicate-card prevention on the Deck page's add form.**
      Frontend-only, same-field (front-vs-front, back-vs-back),
      case-insensitive, debounced ~500ms so warnings don't flicker while
      typing — inline warning under the matching field, Add button
      disabled, `handleSubmit` re-checks the live (non-debounced) values
      as a backstop. No backend change — see `SPEC.md`'s Open decisions
      #10 for why this is deliberately frontend-only and not cross-field.

## Phase 8 — Bug fix: streak flame "already trained today?" state
- [x] Streak flame (🔥, previously always shown "lit"/colored on the stats
      strip and Profile) now has an **unlit/dark state** (`grayscale
      opacity-40`) for the window before today's first grade lands, even
      though `current_streak` still correctly reflects a streak carried
      over from a prior day. Frontend-only, new `frontend/src/streak.js`
      (`trainedToday(stats)`): compares `stats.last_active_date` against
      **the browser's UTC date**, not its local date — deliberately, since
      the backend's own streak logic (`stats.py`'s `record_training_activity`)
      is anchored to `date.today()` on the Lambda, which runs in UTC by
      default; comparing against the client's local date would drift from
      that and misreport the flame's lit state around local midnight in
      non-UTC timezones (this app has already been bitten by exactly this
      category of bug twice — see SPEC.md Open decisions #8's Docker
      clock-skew story). Backend streak logic itself needed no change.
      Used by both `StatsBar.jsx` (top stat strip, all pages) and
      `ProgressPage.jsx`'s stat strip. Verified via `npm run build` +
      `oxlint`, both clean (no dev server available to click through, see
      `CLAUDE.md`'s Commands section — self-check only, visual
      confirmation is yours).

## Phase 9 — Profile identity & Settings redesign
Username + avatar + change password, and folding them into a renamed
**Settings** page (was Admin) alongside the existing actions. No
dependency on any other new phase — safe to build first or in any order
relative to Phase 8.
- [x] `Stats` gains `username` (string, nullable) and `avatar_key` (string,
      nullable — a semantic key into a fixed preset list, not a stored
      image). App-level field, not a Cognito user-pool attribute; username
      uniqueness not enforced — both per the assumptions as planned.
      Deliberately **not** reset by "Reset all progress" (new regression
      test `test_reset_all_progress_does_not_clear_profile_identity`).
- [x] `PATCH /profile` (`app/main.py`) — sets `username`/`avatar_key`
      independently (`ProfileUpdate.model_fields_set` distinguishes
      "omitted" from "sent null"), returns the updated `StatsOut`.
      Validation lives in `schemas.py` field validators: username trimmed,
      blank→`None`, max `USERNAME_MAX_LENGTH` (24) chars (422 if over);
      `avatar_key` must be one of `app/profile.py`'s `AVATAR_KEYS` (422 if
      not). `GET /stats` (`StatsOut`) also gained both fields. 10 new
      backend tests (`test_profile.py`), 111 total passing.
- [x] Preset avatar set — 12 emoji (fox/cat/dog/rabbit/owl/panda/koala/
      lion/tiger/bear/monkey/penguin), `frontend/src/avatars.js`'s
      `AVATARS` list mirrors backend `AVATAR_KEYS` exactly (kept in sync
      by hand — no shared source across the Python/JS boundary). Picker is
      a 6-column emoji grid on Settings, selecting saves immediately (no
      separate Save step, unlike username).
- [x] Change password — in-app form (current/new/confirm), `auth.js`'s new
      `changePassword()` POSTs directly to Cognito's Identity Provider API
      (`cognito-idp.<region>.amazonaws.com`, region parsed out of
      `VITE_COGNITO_DOMAIN` rather than a new env var) with
      `X-Amz-Target: AWSCognitoIdentityProviderService.ChangePassword` and
      the current access token — same "raw fetch, no SDK" style as the
      OAuth calls. Required a real (small) infra change: the access
      token needs the `aws.cognito.signin.user.admin` OAuth scope, added
      to both `login()`'s requested scope string and
      `terraform/cognito.tf`'s `allowed_oauth_scopes` — **not yet
      deployed** (needs `terraform apply` + a Lambda/frontend deploy,
      holding off for a single confirmed deploy once more of this phase
      cluster lands). Existing logged-in sessions will pick up the new
      scope on their next login (access tokens already expire hourly).
- [x] `AdminPage.jsx` → `SettingsPage.jsx` (old file deleted), nav
      icon/label relabeled Admin → Settings in `App.jsx`. New "Profile"
      card (avatar grid + username field/Save) and new "Change password"
      card, both above the unchanged Appearance/Reset/Log out/Danger-zone
      cards — five cards total now (`DESIGN.md` updated). `npm run build`
      + `oxlint` clean; no dev server run per established preference (see
      `CLAUDE.md`/memory — self-check only, visual confirmation is
      yours). **Still needs deployment** (see change-password note above)
      before it's testable live — `PATCH /profile`/avatar/username work
      today without a redeploy being strictly required for *those* parts,
      but change-password won't work until the Cognito scope change is
      applied.

## Phase 10 — Leveling system (XP + Level)
- [x] `Stats` gains `xp` (int) and `level` (int, default 1) — reset by
      "Reset all progress" (this IS gamification progress, unlike Phase
      9's profile identity; see SPEC.md Open decisions #15 for why that's
      consistent with the app's established anti-lifetime-fields-survive-
      resets policy from Open decisions #5).
- [x] XP mirrors coin-earning 1:1 — a Correct grade
      (`record_training_activity`) and the session-complete bonus
      (`award_session_complete`) both gained a matching `stats.xp +=`
      line right next to their existing `stats.coins +=`. Achievement/
      quest coin rewards also grant matching XP: their existing
      `transact_write_items` `UpdateExpression` grew from
      `"ADD coins :r, lifetime_coins_earned :r"` to also `, xp :r` — same
      atomic write, one more attribute, no new transaction.
- [x] `app/leveling.py` (new): `xp_for_level(level)` = cumulative XP to
      *reach* a level (`100 * (level-1) * level / 2` — 100/300/600/1000
      for levels 2-5), `level_for_xp(xp)`, `LEVEL_UP_COIN_REWARD = 20`.
      `finalize_level(store, user_id, stats)` recomputes level from the
      *final* xp total and, if it rose, awards `LEVEL_UP_COIN_REWARD *
      levels_gained` bonus coins via one plain `update_item` —**not**
      folded into the achievement/quest transactions (no completion-row
      needed to guard against double-award, since level is always
      re-derivable from xp; see SPEC.md's Leveling section for the full
      reasoning). Called once per request, after every other
      stats-mutating step, from `POST /cards`, `POST /cards/{id}/grade`,
      `POST /stats/session-complete` — the three routes that can move xp.
- [x] `LevelUpNotice` schema (same shape as Achievement/Quest notices);
      `CardOut`/`StatsOut` gained `newly_leveled_up: list[LevelUpNotice]`.
      Level-up celebration reuses `CelebrationModal`, new
      `kind: "level_up"` → "Level up!" heading. Frontend: `TrainPage`/
      `DeckPage` gained an `onLeveledUp` callback alongside the existing
      achievement/quest ones, feeding the same `App.jsx` celebration
      queue.
- [x] No persistent Level/XP display yet — deliberately deferred to Phase
      12 (Profile page redesign), which is where the header bar actually
      lives; for now leveling is only visible via the celebration popup.
- [x] 17 new backend tests (`test_leveling.py` — pure formula/
      `finalize_level` unit tests; `test_leveling_api.py` — end-to-end
      wiring through `POST /cards`/`/grade`/`/stats/session-complete`,
      deliberately asserting XP *deltas* and the level/xp consistency
      invariant rather than hardcoded totals, since achievement-reward
      cascades make exact cumulative XP hard to hand-predict) + 2 in
      `test_stats.py` for the pure per-grade/session-bonus XP wiring.
      128 backend tests total. `npm run build` + `oxlint` clean.

## Phase 11 — Collection systems + Collection page (titles, themes, lootboxes)
Depends on Phase 10 (XP as a lootbox reward, level-ups as an acquisition
trigger). This is the "chests" feature flagged as unscoped back in Phase
5 — titles/themes and lootboxes are built together since neither is
meaningfully useful alone (a title you can never obtain isn't real; a
lootbox with nothing in it isn't real).
- [ ] Static `CollectibleDef`-style definitions (same code-not-database
      pattern as `achievements.py`/`quests.py`) for **titles** (a display
      string) and **card-colour/font themes** (a named theme + its CSS
      token overrides).
- [ ] `Stats` gains `owned_titles`/`owned_themes` (key lists),
      `equipped_title`/`equipped_theme` (nullable keys), and a lootbox
      inventory (**assumed** a count per tier — exact tier names/count
      pinned down when this phase starts).
- [ ] Lootbox tiers, each with a coin cost (**assumed** purchasable *and*
      earnable free from level-ups/achievement milestones) and a
      weighted-random reward table: coins, XP, an unowned title, an
      unowned theme.
- [ ] Endpoint to open one box from inventory (reward applied + inventory
      decremented in one `transact_write_items` call, same pattern as
      achievement/quest rewards) and an endpoint to equip a title/theme.
- [ ] New **Collection** page/nav tab (bottom pill bar grows from 4 icons
      to 5): browse owned + not-yet-owned titles/themes (locked ones
      dimmed, same visual language as the achievement grid), equip one of
      each, and a lootbox section to open boxes with a reveal animation.
- [ ] **Assumed** scope for themes: the equipped theme re-tints
      `FlipCard`'s surface/accent color (and swaps the display font, if
      the theme includes one) app-wide — not a per-individual-card
      color tag. Flag if you actually meant per-card colours instead.

## Phase 12 — Profile page redesign (Progress → Profile)
Assembles Phases 9-11 — do last in this cluster since it depends on all
three.
- [ ] `ProgressPage.jsx` → `ProfilePage.jsx`, nav relabeled Progress →
      Profile.
- [ ] New header above the existing stat strip: username + equipped title
      (Phase 9/11), Level + XP progress bar (Phase 10).
- [ ] Stat strip gains a 5th value: lootbox inventory count (Phase 11) —
      **assumed** layout will need to adjust for 5 values on narrow
      viewports; will confirm exact treatment when this phase starts.
- [ ] Daily Quests box and Achievements grid carry over unchanged — no
      behavior change, just now on the renamed page.

## Phase 13 — Deck 2.0 (sub-decks, per-card labels, pre-built decks)
No dependency on Phases 9-12 — could be built any time after Phase 8.
- [ ] `Card` gains `label` (string, nullable). **Assumed** one label per
      card (a sub-deck is "cards sharing a label"), not multiple tags per
      card — flag if you want multi-tag instead.
- [ ] Label editor on each Deck-list row (and optionally at card-creation
      time); Deck page can filter/group by label — pure client-side
      filtering over the already-fetched card list, no new endpoint.
- [ ] Pre-built decks: a dev-authored key/value text file per deck,
      committed to the repo (**assumed** `backend/app/prebuilt_decks/*.txt`,
      one deck per file, simple `front<TAB>back` lines — exact format
      pinned down when this phase starts), parsed at Lambda cold-start
      into an in-memory list (same "static content in code" pattern as
      achievements/quests, sourced from bundled text files instead of
      Python literals — `build_lambda.sh` needs to include this
      directory in the zip).
- [ ] Read-only endpoints to list pre-built decks and fetch one's word
      pairs — no `Cards` table involvement, per your "browse/practice
      without owning" answer.

## Phase 14 — Training 2.0 (Extra Training practice modes)
Depends on Phase 13 (labels + pre-built-deck content to select from).
- [ ] New "Extra Training" entry point on the Train page — pick a source:
      all your cards, a subset by label, or a pre-built deck.
- [ ] Practice sessions are **entirely schedule-free**, per your answer:
      no `Card` mutation at all (no `interval_days`/`due_date`/
      `times_correct`/`times_wrong` changes; pre-built-deck words have no
      `Card` row to begin with). **Assumed**: this also means no
      coins/streak/quest/achievement credit during practice, since that
      machinery isn't Card-row-independent today — a practice session's
      only feedback is a client-side end-of-round summary, never sent to
      the backend. Flag if you actually want partial credit (e.g. still
      earning coins) during practice.
- [ ] Frontend-only queue logic reused from the existing Train
      shuffle/requeue-on-Wrong pattern, pointed at a different card
      source, skipping every grade-side-effect API call.

## Phase 15 — Sound effects
Deliberately near the end — decorates interactions introduced by every
phase above (grade, flip, achievement/quest/level-up celebration,
lootbox open).
- [ ] Trigger points: card flip, Correct/Wrong grade, achievement/quest/
      level-up celebration, lootbox open.
- [ ] **Assumed** source: a small set of permissively-licensed (CC0) short
      SFX files bundled in `frontend/public/sounds/`, played via plain
      `Audio()` — no new npm dependency, same "small, no framework
      wrapper" precedent as `canvas-confetti`. Specific sounds picked
      when this phase starts.
- [ ] Mute/volume control on the Settings page (Phase 9), persisted in
      `localStorage` alongside the existing theme preference.

## Phase 16 — Custom icons (nav bar + achievement families) — blocked
- [ ] **Blocked on you supplying SVG artwork**, per your answer — stays a
      backlog item, no active build work now. Nothing to do to keep the
      eventual swap easy: nav icons and achievement badges are already
      single, well-isolated points (`App.jsx`'s nav array,
      `AchievementDef.badge`), so dropping in real SVGs later is a data
      change, not a refactor.

## Phase 17 — Future AI features (backlog, not started)
- [ ] Pronunciation audio: research TTS options, add `audio_url` (or
      generate on demand) and a "play" button on the Train page.
      Tried browser Web Speech API first (free, zero backend) — reverted:
      Chromium-based browsers on Linux don't expose any voices to it, even
      with `espeak-ng`/`speech-dispatcher` installed at the OS level. Next
      attempt should generate audio server-side (e.g. backend endpoint
      shelling out to `espeak-ng`, or a real AI TTS API) and have the
      frontend just play a normal audio file.
- [ ] AI example sentences: given known deck words + N new candidate words,
      generate example sentences restricted to that vocabulary; UI to
      review and add the new words to the deck
