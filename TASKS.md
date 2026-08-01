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
- [x] `app/collection.py` (new): static `TitleDef` (11 titles) and
      `ThemeDef` (7 themes, both across common/rare/epic/legendary
      rarities) definitions, same code-not-database pattern as
      `achievements.py`/`quests.py`. `LootboxTierDef` × 3 (Bronze 50
      coins / Silver 150 / Gold 400), `REWARD_WEIGHTS` per tier over
      coins/xp/title/theme categories (title/theme dropped from the roll
      once nothing new is left in that category, not just weighted to 0).
- [x] `Stats` gains `owned_titles`/`owned_themes` (key lists),
      `equipped_title`/`equipped_theme` (nullable keys), and
      `lootbox_bronze`/`lootbox_silver`/`lootbox_gold` (flat int counts,
      not a nested map — consistent with every other DynamoDB counter in
      this app). Reset by "Reset all progress" (this is gamification
      progress, same reasoning as xp/level).
- [x] Acquisition: `POST /collection/lootboxes/{tier}/buy` (coins →
      inventory) *and* free via level-up — `leveling.finalize_level`
      grants 1 Bronze box per level gained (folded into its existing
      per-level-up `update_item`, not a second write). **Scope cut**: no
      achievement-tied box grants yet (see SPEC.md Open decisions #16).
- [x] `POST /collection/lootboxes/{tier}/open` (`collection.open_lootbox`)
      — decrements inventory, rolls a reward via `roll_lootbox_reward`,
      mutates `Stats` directly and persists via the existing plain
      `save_stats` (deliberately **not** a `transact_write_items` call —
      opening a box is a single explicit action with nothing to guard
      against double-processing, unlike achievement unlocks which
      re-check on every grade). Re-runs achievement/level-up checks
      afterward since a coin/xp reward can cross either threshold; both
      surface on the response alongside the reward itself.
      `POST /collection/equip` (body `{title?, theme?}`, same
      omit-vs-null convention as `PATCH /profile`) requires ownership.
- [x] New **Collection** page/nav tab (🎁, bottom pill bar grows from 4
      icons to 5): a Lootboxes card (Buy/Open per tier), a Titles grid and
      a Card-colours grid (both reusing the achievement grid's
      owned-color/locked-dimmed visual language, click to equip/un-equip,
      theme tiles show a color swatch), and a full-screen reveal modal on
      box-open (icon by reward kind, amount or name won).
- [x] Themes apply **app-wide** (not per-card) via
      `frontend/src/collectionTheme.js`'s `applyCollectionTheme` — sets
      the theme's colors/font as **inline** CSS custom properties on
      `<html>`, which win the cascade over both the light defaults and
      the `html.dark {...}` override block, so an equipped theme's accent
      reads the same in light and dark mode. Applied on equip
      (`CollectionPage`, immediate, no round trip) and on every app load
      (`App.jsx` fetches `GET /collection` alongside `GET /stats` to
      find and re-apply the currently-equipped theme). Two extra Google
      Fonts (Playfair Display, Cormorant Garamond) added to
      `index.html`'s existing font link for the two themes that override
      `font_display`. See SPEC.md Open decisions #17 for the "app-wide,
      not per-card" reading of your original "select cards" wording.
- [x] 22 new backend tests (`test_collection.py` — pure logic:
      roll/buy/open/equip; `test_collection_api.py` — end-to-end wiring
      including level-up-grants-a-box and reset-clears-collection). 150
      backend tests total. `npm run build` + `oxlint` clean.

## Phase 12 — Profile page redesign (Progress → Profile)
Assembles Phases 9-11 — do last in this cluster since it depends on all
three.
- [x] `StatsOut` gained two `@computed_field` properties,
      `xp_into_level`/`xp_for_next_level` (derived from `xp`/`level` via
      `leveling.xp_for_level`, not stored) — a ready `progress_current`/
      `progress_target` pair for the XP bar, free on every
      StatsOut-returning endpoint. 3 new backend tests
      (`test_leveling_progress_api.py`), 153 backend tests total.
- [x] `ProgressPage.jsx` → `ProfilePage.jsx` (old file deleted), nav tab
      key/label relabeled Progress → Profile (icon unchanged, 📈).
- [x] New header above the stat strip: avatar emoji (`avatars.js`) +
      username (falls back to "Your Profile") + equipped title's display
      name underneath (resolved from `GET /collection`, since `StatsOut`
      only carries the title *key* — not worth denormalizing the name
      onto `StatsOut` for a single call site). Then a new Level card:
      "Level *N*" + a purple `ProgressBar` reading the new computed
      fields directly.
- [x] Stat strip gains a 5th value (🎁 lootbox count, summed across tiers
      from `GET /collection`) and switched from a single-row flex to
      `grid grid-cols-3` (wraps 3-then-2) — **not** a viewport breakpoint,
      since the content column is capped narrow regardless of device
      width (see `DESIGN.md` Layout).
- [x] Daily Quests box and Achievements grid carried over unchanged —
      genuinely no behavior change, just relocated onto the renamed page.
      `npm run build` + `oxlint` clean.

## Phase 13 — Deck 2.0 (sub-decks, per-card labels, pre-built decks)
No dependency on Phases 9-12.
- [x] `Card` gains `label` (string, nullable) — one label per card, as
      planned. `CardCreate`/`CardUpdate` both validate it the same way
      (`_blank_to_none`: trimmed, blank string treated as `None`);
      `CardUpdate.label` uses the omit-vs-null convention
      (`model_fields_set`) since clearing a label is a real action, unlike
      french/english. 8 new backend tests (`test_labels.py`).
- [x] Deck page: optional "Sub-deck" field on the add-card form and on
      each row's edit form; a row of filter pills above the list ("All" +
      every distinct label currently in use, derived client-side via
      `[...new Set(cards.map(...))]` — no new endpoint) filters the
      visible list; each row shows its label as a small pill when set.
- [x] Pre-built decks: `backend/app/prebuilt_decks/` is a Python package
      (`__init__.py` = parser, one `*.txt` per deck alongside it — add a
      file, get a deck, no code change). Format: first non-comment/blank
      line is the title, then `english | french` per line (`|` chosen
      over the originally-planned tab-separated format — visible and easy
      to hand-type, unlike a literal tab character). Parsed once at
      import time into `DECKS`. `build_lambda.sh` needed **no change** —
      it already does `cp -r app build/`, which picks up the new
      package/files automatically.
- [x] Shipped four starter decks (title, card count): **Pronouns** (28),
      **Numbers, Days & Months** (48), **50 Most Common Verbs** (50),
      **Sport** (29) — the exact set you asked for, so you can see the
      real shape of the feature before adding your own.
- [x] `GET /prebuilt-decks` (list) / `GET /prebuilt-decks/{key}` (404 if
      unknown) — no `Cards` table involvement, and deliberately no
      `user_id`/`store` dependency at all (the only routes in the app
      without one) since the content isn't user-scoped; still behind the
      same JWT authorizer as everything else (single `$default` API
      Gateway route covers every path). 6 new backend tests
      (`test_prebuilt_decks.py`).
- [x] 14 new backend tests total this phase, 167 backend tests passing.
      `npm run build` + `oxlint` clean. Nothing consumes the pre-built
      deck endpoints on the frontend yet — that's Phase 14.

## Phase 14 — Training 2.0 (Extra Training practice modes)
- [x] New "🎲 Extra Training" text link on the Train page (visible both
      while cards are due and on "Session complete") opens a picker —
      `TrainPage.jsx` gained a `mode: "train" | "picker" | "practice"`
      state; the due-card loop itself is completely untouched.
- [x] `ExtraTrainingPicker.jsx`: pick a source — all your cards, a subset
      by label (one button per distinct label, counts shown, reuses the
      already-fetched `GET /cards`), or a pre-built deck
      (`GET /prebuilt-decks`). Each pre-built deck has a **Preview**
      button (fetches the full deck, opens a scrollable English-word-only
      modal — reuses the achievement-detail popup's exact shell) and a
      **Practice** button. Its own ✕ closes the picker back to Train.
      Pre-built deck rows are deliberately **not** given the Deck list's
      tilted-stack treatment — see `DESIGN.md`'s Signature element
      section for why (a visual cue that this content isn't yours).
- [x] `PracticeSession.jsx`: **confirmed** (not just assumed) fully
      schedule-free — no `Card` mutation, no coins/xp/streak/quest/
      achievement credit, **no API call at all** on grading (local
      `correct`/`wrong` counters only). **Confirmed**: a single linear
      pass through the queue, once — no requeue-on-Wrong the way the real
      Train loop has, per explicit request ("going through that one
      deck, once"). A fixed floating ✕ pill (top-right, same visual
      treatment as the nav bar's own floating pills) exits at any point.
      Reaching the end shows a "Practice complete" tally with **Practice
      again** (same queue, restarts) and **Done**.
- [x] Pre-built-deck cards have no real `id` from the API
      (`PrebuiltCardOut` carries none) — the picker assigns a synthetic
      `prebuilt-<index>` id when building the local practice queue,
      React-key use only.
- [x] Frontend-only phase, no backend changes — 167 backend tests still
      passing unchanged. `npm run build` + `oxlint` clean.
- [x] `ExtraTrainingPicker.jsx` gained an **Ordered / Shuffled** toggle
      (same two-pill segmented-control pattern as `ThemeToggle.jsx`,
      defaulting to Ordered) at the top of the picker, applying to
      whichever source is started next — a plain in-memory Fisher-Yates
      shuffle right before `toQueue`, frontend-only, no backend/API
      change (mirrors "Session queue logic lives in the frontend" for the
      real Train loop). `oxlint` clean.

### Achievements for practice, leveling, collection, profile, and labels
Requested after Phase 14 shipped — 13 new achievement tiers covering
every feature added in Phases 9-14 that didn't already have one, plus a
real correctness fix the new "level" achievements surfaced.
- [x] `Stats` gains `used_label`, `practiced_prebuilt_deck`,
      `practiced_own_full_deck`, `practiced_sub_deck`,
      `practice_sessions_completed`, `lootboxes_opened` — all reset by
      "Reset all progress" (gamification progress, same as everything
      else added since Phase 10). None of these are exposed via
      `StatsOut`/`GET /stats` (internal achievement-tracking plumbing,
      same as `total_correct`/`comebacks`/etc. already weren't) —
      progress is only visible through `GET /achievements`.
- [x] New `POST /practice/completed` (`{source: "own_deck"|"sub_deck"|
      "prebuilt"}`) — the only signal the backend gets that an Extra
      Training round happened, called once by `PracticeSession.jsx` on a
      full completion (not on early exit). `used_label` is set directly
      in `POST /cards` when a label is provided at creation (edits via
      `PATCH /cards/{id}` don't track it — that route has no
      stats/achievement wiring at all, matching how deck-size
      achievements also only count creation, not edits).
- [x] 13 new `AchievementDef`s in `achievements.py`: `profile_set_up`
      (username + avatar), a 4-tier `level` family (5/10/25/50), a
      3-tier `lootboxes` family (1/10/50), `equipped_title`/
      `equipped_theme`, `title_collector`/`theme_collector` (target =
      `len(collection.TITLES)`/`len(collection.THEMES)` at import time),
      `used_label`, `practiced_prebuilt`/`practiced_own_deck`/
      `practiced_sub_deck`, and a 3-tier `practice` family (5/25/100).
      66 tiers / 26 collapsed families+standalones total (was 53/10).
- [x] **Bug fix, caught by a genuinely failing test during development**:
      `leveling.finalize_level` used to run once per request, *after*
      `check_and_unlock_achievements` — so an achievement condition
      reading `stats.level` (the new "level" family) evaluated a stale
      level from before that request's own level-up. Fixed by calling
      `_finalize_level` **twice** per request in every route that can
      move xp (`POST /cards`, `POST /cards/{id}/grade`,
      `POST /stats/session-complete`, `POST /collection/lootboxes/{tier}/open`,
      `POST /practice/completed`): once right after the routine
      mutation (achievements then see the current level), once more
      after achievements/quests are checked (to catch a level-up from
      *their* reward xp). Safe to call twice — a no-op when xp hasn't
      crossed a new threshold.
- [x] Also fixed a stale comment in `models.py` (said
      `lifetime_coins_earned`/`sessions_completed`/etc. are "deliberately
      NOT reset" — described the pre-reversal design from Phase 5's
      history, not current behavior; `reset_all_stats` has zeroed them
      for a long time). Caught while adding the new fields nearby.
- [x] `test_all_achievements_locked_with_no_activity` needed one
      accommodation: `stats.level` starts at 1, not 0 (unlike every
      other achievement-backing stat), so the "level_5" tile's
      `progress_current` is legitimately 1 with zero activity, not 0 —
      documented as the one exception rather than weakened generally.
- [x] 15 new backend tests (`test_new_achievements.py`). 182 backend
      tests total. Frontend: `completePractice(source)` in `api.js`,
      threaded picker→TrainPage→PracticeSession (`source` prop),
      `PracticeSession.jsx` calls it via a `useEffect` keyed on `[done,
      source]` — deliberately not listing the `onAchievementsUnlocked`/
      `onLeveledUp` callback props as deps (they're plain functions from
      `App.jsx`, not memoized, so a naive exhaustive-deps fix would
      re-fire the effect — and re-POST — on every parent re-render while
      `done` stays true); a ref holds the latest callbacks instead.
      `npm run build` + `oxlint` clean, zero warnings.

### Bug-fix batch: label case, missing achievement checks, Settings layout
User-reported, fixed together.
- [x] Labels are now case-insensitive — `schemas._normalize_label`
      lowercases at write time (both `CardCreate`/`CardUpdate`), so
      "Animals"/"animals"/"ANIMALS" always group as one sub-deck. 3 new
      backend tests.
- [x] Deck page gained **bulk-select**: a "Select" toggle puts the list
      into a checkbox mode (click anywhere on a row to toggle; selected
      rows drop their tilt for a `ring-2 ring-primary` highlight instead
      of edit/delete buttons), a bulk-action bar (Select all — respects
      the active label filter —, set-label-for-selected, delete-selected)
      appears above the list. Both bulk actions are `Promise.all` loops
      over the existing per-card `PATCH`/`DELETE` endpoints — no new bulk
      endpoint needed — and forward every response's achievement/level-up
      notices to the celebration queue, not just the first.
- [x] **Bug fix**: the stats bar's coin count only updated on whichever
      action happened to already call `refreshStats` (mainly grading) —
      an achievement/level-up reward from *any other* action (adding a
      card, equipping something, changing your profile) changed coins
      server-side but the bar kept showing the stale number until the
      next grade. Fixed by having `App.jsx`'s
      `handleAchievementsUnlocked`/`handleLeveledUp` call `refreshStats()`
      whenever they're given a non-empty list — centralized there instead
      of threading `onChanged` through every page, so any future action
      reporting a reward gets this for free.
- [x] **Bug fix**: `PATCH /cards/{id}`, `PATCH /profile`, and
      `POST /collection/equip` never checked achievements/level at all —
      achievements like "Organizer"/"Make It Yours"/"Dressed to
      Impress"/"New Look" only surfaced on some later, unrelated action
      that happened to check. Added the same double-`_finalize_level` +
      `check_and_unlock_achievements` pattern used everywhere else to all
      three. `used_label` (Phase 13/18) now fires on an edit that adds a
      label too, not just at creation — the "only counts creation"
      design note is superseded. Two existing tests
      (`test_profile_set_up_unlocks_once_username_and_avatar_are_both_set`,
      `test_equipped_title_and_theme_achievements`) had encoded the old
      "identity actions don't check achievements" behavior as their
      premise and needed rewriting, not just their assertions patched. 2
      new tests for the update_card/equip paths.
- [x] Settings page: **Change password** is now a single button that
      opens a popup (reuses the achievement-detail popup's modal shell)
      instead of an always-visible 3-field inline form. **Reset all
      progress** moved into the **Danger zone** card alongside **Delete
      ALL cards** (previously sat in its own neutral card) — every
      destructive-progress action now shares one visual treatment.
      **Log out** moved to a standalone button at the very bottom of the
      page, outside the danger zone (logging out isn't destructive, so it
      shouldn't carry that card's coral-tinted, confirm-gated weight).
- [x] 4 new backend tests this batch (3 label-normalization, 1
      update-card-triggers-used_label) plus 2 existing tests rewritten to
      match the new behavior instead of just having their assertions
      patched. 186 backend tests passing. `npm run build` + `oxlint`
      clean.

### Daily quest "perfect day" bonus + Profile page stat cleanup
User-requested, fixed together.
- [x] Completing **every** daily quest on the same day now awards one
      bonus silver lootbox, on top of each quest's own coin reward —
      `quests.check_and_award_daily_bonus`, gated by the new
      `Stats.daily_quest_bonus_awarded` flag (reset in both `sync_day`
      and `reset_all_stats`, same policy as the rest of the daily-quest
      state). Checked from `POST /cards` and `POST /cards/{id}/grade`
      right after `check_and_complete_quests`; reported as
      `newly_awarded_daily_bonus` on `CardOut` (`DailyQuestBonusNotice` —
      `lootbox_tier` instead of `coin_reward`, since the reward's a chest
      not coins). `CelebrationModal` gained a `daily_bonus` heading and
      branches on `lootbox_tier` vs `coin_reward` to render the right
      reward line. 7 new backend tests (pure-logic idempotency/reset/
      day-rollover cases in `test_quests.py`, plus two API-level tests in
      `test_api.py`).
- [x] Profile page: the streak/coins/cards/accuracy/lootboxes strip lost
      **accuracy** and is now a single-row `grid-cols-4` (was a
      wrapping 5-item `grid-cols-3`).
- [x] Profile page: new **Lifetime stats** box directly under Daily
      Quests — total cards, reviewed, learned (correct), practiced
      (wrong), accuracy, and mastered, as plain `label │ value` rows,
      deliberately **no emoji/icons and no `font-display`** (per explicit
      "keep it discrete" request) — the one box on this page that doesn't
      use the flashy Fraunces-numbers-plus-icon treatment everywhere
      else. New `TextStat` component in `ProfilePage.jsx` backs it.
- [x] 193 backend tests passing. `npm run build` + `oxlint` clean.

### Daily stats box, due-tomorrow, and daily achievements
Requested after Phase 14 shipped, out of the numbered phase sequence —
same pattern as the "Achievements for practice, leveling, collection,
profile, and labels" addendum above.
- [x] Unified the app's day-rollover boundary: `stats.logical_today()`
      (3am Europe/Oslo, `zoneinfo`, no new dependency) replaces
      `date.today()` (UTC midnight) for daily quests, the streak
      (`last_active_date`), and the two new daily counters below — a
      single "gamification day" concept end to end, per explicit request.
      Mirrored client-side in `streak.js`'s `logicalToday()` (used by
      `trainedToday`'s 🔥 lit-state check, which shares this boundary
      now). **Deliberately excludes** `session_date`/`session_initial_due`
      (the Train page's due-count freeze) and `Card.due_date` itself —
      both stay UTC-anchored, since `Card.due_date` is UTC-bucketed
      (Open decisions #1) and a due-count freeze needs to agree with
      that bucket, not the Oslo-shifted day. Documented, accepted,
      self-correcting edge case during the ~1-2 hour UTC/Oslo gap — see
      `stats.sync_day`'s docstring.
- [x] `Stats` gains `wrong_today`/`practice_sessions_today` (join the
      existing `quest_cards_added_today`/`quest_correct_today`), all four
      reset together in `sync_day` on gamification-day rollover, and by
      "Reset all progress" (progress, not identity — same policy as
      everything else added since Phase 10). Exposed via `GET /stats`
      (`StatsOut`) for the Profile page's new box below.
- [x] `POST /practice/completed` now also calls `stats.sync_day` (it
      didn't before) and increments `practice_sessions_today`.
- [x] Profile page's existing Lifetime stats box gained a second
      `label │ value` grid below a divider, **same box**, headed "Daily
      stats" (per explicit request, not a separate card): added/
      reviewed/correct/wrong/accuracy today, practice rounds today, and
      due tomorrow. Labeled **Correct**/**Wrong** rather than the
      Lifetime section's Learned/Practiced naming, since "Practiced"
      would collide with Extra Training's own "practice round" wording
      two rows below in the same box.
- [x] "Due tomorrow" is a live client-side count (cards from the
      already-fetched `GET /cards` list whose `due_date` equals
      UTC-tomorrow) — not a resetting counter, no new endpoint.
- [x] Three new standalone achievements reading the daily counters
      directly, no new tracking fields needed (the achievement unlock
      record itself is what makes it permanent): "Big Day" (🗓️, 10 cards
      added in a day), "Study Day" (📊, 30 reviewed in a day), "Practice
      Day" (🔂, 3 Extra Training rounds in a day).
- [x] New tests: `logical_today`'s 3am/DST boundary (winter + summer),
      `wrong_today`/`practice_sessions_today` increment + reset, the
      three new achievements (including that they stay unlocked after
      the underlying daily counter resets), and `GET /stats`/
      reset-all-progress coverage of the new fields. 205 backend tests
      passing. `oxlint` clean.

### WCAG AA color/contrast audit (light/dark + Collection themes)
Requested after a "dark mode colors look pretty bad, especially the
create-card box" report — out of the numbered phase sequence, same
pattern as the two addenda above.
- [x] Full app-wide WCAG AA audit (4.5:1 normal text, checked at each
      token's actual rendered size/weight) via a small contrast-ratio
      script, covering every real text/background pairing used in the
      app for both built-in themes and all seven Collection themes ×
      light/dark. Found real failures, not just subjective ugliness:
      `text-white` on `bg-primary`/`bg-wrong` buttons down to 2.55:1 in
      dark mode, `text-ink-soft/70` captions (used almost everywhere)
      down to 2.9:1, and Collection themes' `primary-dark` used as text
      against a dark surface down to 1.33:1 (Midnight) — themes
      previously applied one shared light-mode-tuned color triple
      identically in both modes.
- [x] `index.css`: new base `primary`/`primary-dark`/`wrong`/`wrong-dark`
      hex values, all passing 4.5:1 everywhere they're actually used.
      `primary`/`wrong` end up the same hex in light and dark mode (not
      an oversight — "the color that holds 4.5:1 white button text"
      lands at nearly the same lightness solved from either end).
- [x] Structural fix, not just recolor: **the `-dark` variants
      (`primary-dark`/`wrong-dark`) are now used only as text on a
      tinted/plain surface, never as a hover-state button background** —
      a single token can't be simultaneously light enough to read as
      text on a dark surface and dark enough to hold white button text.
      Every `hover:bg-primary-dark`/`hover:bg-wrong-dark` (13 buttons
      across `TrainPage`/`DeckPage`/`PracticeSession`/
      `ExtraTrainingPicker`/`CollectionPage`/`SettingsPage`/
      `CelebrationModal`) became `hover:brightness-90` instead.
- [x] Every `text-ink-soft/70` (23 occurrences — nearly every small
      caption/label in the app) and the one `text-primary-dark/80` hover
      lost their opacity modifier (`/70` → none, `/80` → `/90`) — the
      alpha, not the base color, was what pushed small text below AA;
      `ink-soft` alone already clears it with margin, so the base
      palette didn't need to change for this.
- [x] `backend/app/collection.py`'s `ThemeDef` gained a second color set,
      `colors_dark` alongside the existing `colors` (light) — all 7
      Collection themes now have independently-solved light and dark
      variants (`GET /collection`'s `ThemeOut` gained `colors_dark` to
      match), plus nudged saturation/hue spread per theme (crisp Ocean
      blue, muted Forest green, desaturated Rose Gold blush, etc.) for
      more visual distinction between them, per explicit request.
- [x] `collectionTheme.js`: `themeColorsForCurrentMode(theme)` picks the
      right set for the current light/dark toggle; a `MutationObserver`
      on `<html>`'s `class` re-applies automatically when that toggle
      changes (previously an equipped theme never reacted to a dark-mode
      toggle at all — colors could go stale until a full reload).
      `CollectionPage`'s theme swatches also use this instead of the
      always-light `.colors.primary`.
- [x] Verified visually, not just numerically: a throwaway `npm run dev`
      + Playwright harness (mocked auth token in `sessionStorage`, mocked
      `/api/*` responses, deleted before finishing — never committed, per
      `CLAUDE.md`'s established pattern) screenshotted Deck/Train/
      Profile/Collection in both themes, plus the Deck page with the
      Midnight Collection theme equipped in dark mode (the worst-case
      scenario the audit found) to confirm the fix actually renders
      correctly, not just passes the math.
- [x] 205 backend tests still passing (schema/data change only, no
      behavior change — no new tests needed here). `npm run build` +
      `oxlint` clean.

### Extra Training picker: unify "Your decks" / "Pre-built decks" styling
Requested after a "these two sections look strange, inconsistent with
each other" report — out of the numbered phase sequence, same pattern as
the addenda above.
- [x] New shared `DeckRow` component in `ExtraTrainingPicker.jsx`: title +
      "N cards" on the left, Preview/Practice buttons on the right — used
      for *every* row in both sections now, replacing "Your deck"'s old
      enclosing box of plain pill-buttons (no Preview, "All my cards"/
      each sub-deck as a single click-to-start button).
- [x] "Your deck" → "Your decks" (plural), per explicit request.
- [x] Own-deck/sub-deck rows gained a working **Preview** button — no
      network call needed (the full card list, `english` included, is
      already fetched via `GET /cards`), just opens the same preview
      modal pre-built decks already used, filtered to that row's cards.
- [x] Pre-built deck rows now say "N cards" instead of "N words" (the
      only place in the app that called them words) — matches the new
      shared `DeckRow` copy.
- [x] Verified visually with the same throwaway `npm run dev` + Playwright
      harness pattern (mocked auth/API, not committed) — both sections
      render identically in light and dark, and the own-deck Preview
      modal works. `oxlint` clean; no backend change, no test changes
      needed (frontend-only, no new logic beyond the existing preview
      modal reused as-is).

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
- [x] **Pronunciation audio** — done, ahead of the rest of this backlog
      phase (planned/approved/implemented as its own pass, out of
      sequence, same as the addenda elsewhere in this file). A speaker
      icon on `FlipCard`'s back (French) face, shared by Train and Extra
      Training's Practice Session. Generated server-side via **Amazon
      Polly** (Léa, fr-FR, neural) as planned back when this item was
      first written — the earlier Web Speech API attempt's failure (no
      voices exposed to Chromium on this dev machine even with
      `espeak-ng` installed) is exactly what pushed the design toward
      server-side generation from the start; see SPEC.md's new
      "Pronunciation audio" section for the full design (content-hash S3
      cache key rather than card id, private-bucket-behind-CloudFront
      storage, the `/audio/*` behavior sharing the frontend's existing
      distribution).
  - [x] `backend/app/pronunciation.py`: `AudioStore`/`get_audio_store`
        (mirrors `database.py`'s `Store`/`get_store` DI seam exactly, so
        it's moto-testable), `get_or_create_audio_url` (hash-based cache
        key, S3 `head_object` check, Polly `synthesize_speech` on a
        miss, `put_object`, returns a CloudFront URL). New
        `GET /pronounce?text=...` route, same JWT gate as everything
        else.
  - [x] `terraform/audio.tf` (new file): private S3 bucket + Block Public
        Access + a second Origin Access Control, mirroring
        `frontend.tf`'s own bucket exactly. `terraform/frontend.tf`
        gained a new origin + `/audio/*` ordered_cache_behavior on the
        *same* distribution (`caching_optimized`, not
        `caching_disabled` like `/api/*` — audio objects are immutable).
        `terraform/lambda.tf` gained IAM (`polly:SynthesizeSpeech`,
        necessarily `Resource = "*"` since Polly has no resource-level
        ARN for synthesis; `s3:GetObject`/`PutObject` scoped to the new
        bucket) and two new env vars, `AUDIO_BUCKET`/`AUDIO_CDN_DOMAIN`.
  - [x] `frontend/src/pronunciation.js`: `getPronunciationUrl(text)`,
        module-level `Map` cache (mirrors `theme.js`'s module-level state
        pattern) keyed the same way as the backend's own cache, caching
        the in-flight Promise too so a double-tap before the first
        request resolves doesn't fire a second one. New
        `SpeakerIcon.jsx` (custom SVG, same precedent as
        `ThemeIcon.jsx`/`CoinIcon.jsx`). `FlipCard.jsx`'s `CardFace`
        (`variant === "back"` only) gained the button — `e.stopPropagation()`
        first, since it sits inside the card's own flip-trigger handler.
  - [x] New `backend/tests/test_pronunciation.py` (8 tests: cache
        hit/miss via a `_synthesize` call-count spy, case/whitespace
        normalization, distinct texts get distinct keys, empty/overly-
        long text both 400, the real `GET /pronounce` route). New
        `audio_store` pytest fixture (piggybacks on `store`'s already-
        open `mock_aws()` context — a second independent one would be
        redundant) works around a genuine moto bug found while writing
        these: moto's `SynthesizeSpeech` mock validates `VoiceId`
        against voices' display *Name* ("Léa", accented) instead of the
        real API *Id* ("Lea" — confirmed against botocore's own
        `polly/2016-06-10/service-2.json`, which is what real AWS
        actually accepts), so every accented-name voice would otherwise
        spuriously fail only in tests. 213 backend tests passing.
        `oxlint` + `npm run build` clean. Visually verified (icon
        placement/legibility in light+dark, tapping it doesn't flip the
        card, playback fires) via the established throwaway
        `npm run dev` + Playwright pattern, mocked `/pronounce` response
        and `HTMLMediaElement.play` — not committed.
  - [x] **Two real deploy-time bugs**, neither catchable by the moto-based
        test suite (moto doesn't model IAM authorization or per-region
        Polly engine availability — both are real-AWS-only failure
        modes), found via `aws logs tail` on the actual Lambda after the
        first deploy came back silent:
        1. `_exists()`'s `head_object` came back `403 Forbidden` instead
           of `404 Not Found` for every (nonexistent-key) cache-miss
           check, so every request crashed before ever reaching Polly —
           explaining "no sound, nothing in the bucket either". Root
           cause: the IAM policy granted `s3:GetObject`/`PutObject` on
           `bucket-arn/*` (object-level) but not `s3:ListBucket` on the
           bucket itself (a *different* resource ARN, no trailing `/*`)
           — S3's documented behavior is to return 403 rather than 404
           for a missing key when the caller lacks list access, to avoid
           confirming/denying what does or doesn't exist in the bucket.
           Fixed with a third IAM statement in `lambda.tf`.
        2. Once that was fixed, `SynthesizeSpeech` itself failed:
           `ValidationException: The selected engine is not supported in
           this region` — confirmed via `aws polly describe-voices
           --language-code fr-FR` that eu-north-1 (Stockholm, where this
           app is deployed) only supports Léa on the **standard** engine,
           not neural, at all. eu-west-1 (Ireland) does support neural
           for Léa, so `pronunciation.py`'s Polly client is now pinned to
           `region_name="eu-west-1"` explicitly (a new `POLLY_REGION`
           constant) regardless of the Lambda's own region — S3/DynamoDB/
           everything else stays in eu-north-1 unaffected, since Polly
           doesn't care where the resulting audio bytes end up stored.
        Both fixes verified against real AWS directly (`aws iam
        simulate-principal-policy` for the first, a real
        `aws polly synthesize-speech` call against eu-west-1 for the
        second) before redeploying, not just re-tried blind.
- [ ] AI example sentences: given known deck words + N new candidate words,
      generate example sentences restricted to that vocabulary; UI to
      review and add the new words to the deck
