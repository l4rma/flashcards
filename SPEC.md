# Flash Cards App — Spec

A simple Anki-style flash card app for learning French vocabulary. You train on
cards (French word → English translation), grade yourself, and the app
schedules when you should see each card again using spaced repetition.

## Core concept

- A **card** has a French word/phrase (`key`) and its English translation
  (`value`).
- Training shows the card's **front (English)** first; you recall the
  **French** word, then flip to reveal the back and grade yourself.
  (Card fields are still named `french`/`english` in the data model — the
  front/back display order is purely a frontend concern, see Frontend
  below.)
- Grading updates when the card is due again, using a simple doubling
  interval (not full SM-2/Anki — deliberately simpler).

## Data model

### Card

| Field           | Type      | Notes                                                        |
|-----------------|-----------|---------------------------------------------------------------|
| `user_id`       | string    | Owning user's Cognito `sub` — partition key in DynamoDB. See Multi-tenancy / AWS deployment, below |
| `id`            | string    | Unique identifier (UUID) — sort key in DynamoDB               |
| `french`        | string    | The French word/phrase — shown as the card's **back** (`key`) |
| `english`       | string    | The English translation — shown as the card's **front** (`value`) |
| `interval_days` | int       | Current interval; `0` means "new" / just reset                |
| `due_date`      | date      | Card is due when `due_date <= today` (UTC date, day-granularity) |
| `created_at`    | datetime  | When the card was added                                       |
| `last_reviewed_at` | datetime, nullable | Last time it was graded "correct"                    |
| `times_correct` | int | Lifetime count of Correct grades — for future stats, not scheduling |
| `times_wrong`   | int | Lifetime count of Wrong grades — ditto |
| `last_grade`    | string, nullable | Outcome of the most recent grade ("correct"/"wrong"); only used to detect "Comeback Kid", not shown in the UI |
| `mastered`      | bool | Has this card ever crossed `scheduling.MASTERY_THRESHOLD_DAYS`? Lifetime flag for the "Word Master" achievement family |

`times_correct`/`times_wrong`/`mastered`/`last_grade` **are** cleared by
Admin's "Reset all progress" action, same as `interval_days`/`due_date`/
`last_reviewed_at` — see Open decisions for why (originally meant to
persist as a lifetime record across resets; reversed after that caused
confusing bugs in practice).

The app is genuinely multi-tenant as of the AWS migration (Cognito login,
each user gets their own separate deck/progress) — see Multi-tenancy /
AWS deployment, below, and [Open decisions](#open-decisions-assumptions).

## Scheduling algorithm

Grading only changes the card's schedule when you grade **Correct**. Wrong
does not touch `interval_days` or `due_date` — it only affects the current
training session's queue (see below).

- **Correct**
  - `times_correct += 1`
  - If `interval_days == 0` (new or just-reset card) → set `interval_days = 2`
  - Else → `interval_days = interval_days * 2`
  - `due_date = today + interval_days`
  - `last_reviewed_at = now`
  - Card leaves the current session's queue.
- **Wrong**
  - `times_wrong += 1`
  - `interval_days = 0` (resets progress — next "Correct" restarts at 2 days)
  - `due_date` unchanged for now (card is still "due" until you grade it
    Correct in a session; see below)
  - Card is requeued in the current session (shown again before the session ends).

This means Wrong cards keep reappearing within the same session, possibly
multiple times, until you either grade them Correct or end the session. If
you end the session with ungraded Wrong cards still in the queue, they
simply remain due and will show up again next time you start training.

## Training session flow

1. **Start session**: pull all cards where `due_date <= today` into an
   in-memory queue (order: shuffled, or oldest-due-first — TBD in
   implementation).
2. **Show next card**: display the English word (front).
3. User clicks the card to flip it, revealing the French word (back).
4. User grades: **Wrong / Correct**.
   - Correct → update schedule (see above), remove from queue.
   - Wrong → leave schedule as-is, move card to the back of the queue.
5. Repeat until the queue is empty, or the user stops the session early.

No stats/dashboard in the MVP (cards due count, streaks, etc. are backlog).

## API design

REST-ish API, single resource (`Card`) plus the gamification endpoints
below. Backed by DynamoDB (see Tech stack) — every route requires
authentication and is scoped to the calling user (`user_id` from the
verified Cognito JWT), never a request parameter.

- `POST /cards` — create a card (`french`, `english`)
- `GET /cards` — list all cards
- `GET /cards/due` — list cards currently due (`due_date <= today`)
- `PATCH /cards/{id}` — edit a card's `french`/`english` text
- `DELETE /cards/{id}` — delete a card
- `POST /cards/{id}/grade` — body: `{ "grade": "wrong" | "correct" }`
  — applies the scheduling algorithm above and returns the updated card

Session queue logic (ordering, requeueing) lives in the **frontend**, not the
backend — the backend only tracks each card's persistent schedule state. This
keeps the backend stateless/simple and avoids needing session storage.

## Frontend (React)

Pages:
- **Deck** — combines what were originally two separate tabs (Add Card,
  Manage Cards) into one page: the add-card form pinned at the top (`Front`
  / `Back` fields, front = English, back = French; placeholders "hello"/
  "bonjour"; generic front/back wording rather than "French"/"English" —
  see Open decisions), the Manage list directly below it (edit/delete,
  header shows total card count and how many aren't yet correct this
  session, each row shows English/front first then French/back plus
  lifetime ✓/✗ counts and interval/due date). Adding a card refreshes the
  list underneath automatically. Combined per explicit request — they were
  two thin pages that were almost always used together. The add-card form
  blocks a duplicate: front is checked against every existing card's front
  (English), back against every existing back (French), case-insensitively
  — *not* cross-field, so a legitimate front/back swap between two cards
  isn't flagged. This is a **frontend-only** check against the deck list
  already loaded on the page (no extra request), debounced ~500ms so
  warnings don't flicker mid-keystroke; the Add button disables and an
  inline warning appears under whichever field matched. There is
  deliberately no backend enforcement of this rule (see Open decisions) —
  it's a UX nicety, not a data-integrity guarantee.
- **Train** — the core loop: show English word (front) → click to flip and
  reveal the French word (back) → grade buttons → next card. Shows
  "Session complete" when the queue is empty.

Nav is a floating icon-only pill bar fixed to the bottom of the viewport
(no text labels) — see `DESIGN.md`'s Navigation section for the bar
styling and which emoji maps to which tab.

Auth: Cognito Hosted UI (redirect + PKCE authorization-code flow). On load,
if there's no valid access token, the app redirects to Cognito's login
page; after login, Cognito redirects back with a `code` that's exchanged
for tokens. Every API call attaches `Authorization: Bearer <token>`; a 401
response redirects back to login rather than attempting silent refresh
(access tokens expire in 60 minutes — an idle user gets bounced back to
what's usually an invisible re-auth if their Hosted-UI session cookie is
still live). A logout action lives on the Admin page.

## Tech stack

**AWS, no local/Docker deployment target.** Final architecture:

- **Backend**: FastAPI, packaged for AWS Lambda via `Mangum`
  (`handler = Mangum(app, api_gateway_base_path="/api")`), fronted by
  **API Gateway** (HTTP API) with a
  native JWT authorizer validating **Cognito** tokens before Lambda is
  invoked — no hand-rolled JWT verification in the app.
- **Database**: **DynamoDB**, four tables (`Cards`, `Stats`,
  `Achievements`, `QuestCompletions`), On-Demand billing. See `CLAUDE.md`'s
  Architecture section for the exact key schema and why a live
  SQL-style aggregate query became a set of `Stats` counters instead.
- **Frontend**: React (Vite) built as a static bundle, hosted on **S3 +
  CloudFront** (CloudFront also proxies `/api/*` to API Gateway under the
  same origin, so the frontend's `/api` relative-path convention needs no
  change).
- **Auth**: **Cognito** User Pool + Hosted UI (self-service signup, open by
  default).
- **IaC**: **Terraform**, flat single root module (no nested modules —
  personal project, avoid premature abstraction), no VPC at all (Lambda
  only talks to DynamoDB/Cognito, both over managed endpoints).
- Chosen over two alternatives during planning, for the record: ECS
  Fargate + ALB + RDS Postgres (rejected — real numbers came out around
  $40-48/mo, dominated by the ALB's flat hourly charge, vs. Lambda+API
  Gateway+DynamoDB's effectively-$0/mo at this traffic level) and a single
  EC2 instance running the (now-retired) Docker Compose setup as-is
  (~$11.60/mo, viable, but the user's own stated preference — prior
  experience with Lambda/API Gateway, and "this really feels like a
  project that should be serverless" — settled it in favor of full
  serverless once the DynamoDB port was shown to be more tractable than
  first assessed).

### Multi-tenancy

Genuinely multi-user (not just an auth gate on top of a single-tenant
app) — every table is partitioned by `user_id` (the Cognito `sub` claim).
`Stats` changed from a hardcoded singleton row to one item per user.
`AchievementUnlock`/`DailyQuestCompletion` gained `user_id` as part of
their key. Every card operation addresses `Key={user_id, id}`, which
closes an IDOR class of bug by construction (there's no way to reference
another user's card without already knowing their `user_id`, which only
ever comes from the verified JWT) rather than relying on someone
remembering to add a `WHERE`/filter clause.

## Gamification

Planned to land in stages, each useful on its own: **streak + coins** first,
then achievements, then **daily quests** (this phase), then chests. Coins
have no spend target yet — chests (a later phase) will be the first coin
sink.

### Data model

### Stats (one item per user, keyed by `user_id`)

| Field              | Type          | Notes                                     |
|--------------------|---------------|--------------------------------------------|
| `coins`            | int           | Running total, earned from training        |
| `current_streak`   | int           | Consecutive days with at least one grade    |
| `longest_streak`   | int           | High-water mark of `current_streak`         |
| `last_active_date` | date, nullable| Last UTC date any card was graded           |
| `current_correct_streak` | int     | Consecutive Correct grades; any Wrong resets to 0 |
| `longest_correct_streak` | int     | High-water mark of `current_correct_streak` — used by the "correct in a row" achievement family, never reset by admin actions |
| `session_had_wrong` | bool | Any Wrong since the last session completion (or start of day)? Reset in `sync_session` (new day) and again in `award_session_complete` (fresh check per completion) |
| `flawless_sessions_completed` | int | Lifetime count of sessions completed with `session_had_wrong` still false |
| `largest_session_completed` | int | High-water mark of `session_initial_due` at the moment a session actually completed — for "Marathon" |
| `comebacks` | int | Lifetime count of "graded Wrong, then Correct" on a card's next grade |
| `cards_mastered` | int | Lifetime count of cards that have ever crossed `scheduling.MASTERY_THRESHOLD_DAYS` (64) |
| `trained_before_7am` / `trained_after_11pm` | bool | One-time flags based on local wall-clock time at grading — for Early Bird (4am–7am) / Night Owl (11pm–4am, spans midnight) |
| `quest_date` | date, nullable | Last calendar date the daily-quest fields were synced — mirrors `session_date`'s freeze-once-per-day pattern |
| `quest_cards_added_today` | int | Cards added today via `POST /cards` — backs the "Deck Builder" quest. Incremented only on the actual add action (not derived from `Card.created_at`), reset to 0 on day rollover |
| `quest_correct_today` | int | Correct grades today — backs the "Daily Training" quest, whose target is `min(10, session_initial_due)` so it counts down identically to the Train page's own progress bar. Reset to 0 on day rollover |
| `total_cards` | int | Running count of cards ever created — backs the deck-size achievement family. A `Stats` counter (not a live count of the `Cards` table), since DynamoDB has no `COUNT` query; incremented on `POST /cards`. **Not** reset by "reset all progress" (mirrors the pre-DynamoDB behavior: that action never deleted cards, so this shouldn't drop either) |
| `total_correct` / `total_wrong` | int | Running lifetime counts — back the "lifetime correct answers" achievement family and "First Steps"/"Nobody's Perfect". Replaced a live `SUM(Card.times_correct)`-style aggregate for the same DynamoDB reason; incremented in the same `record_training_activity` call that updates every other per-grade counter. Reset by "reset all progress" (unlike `total_cards`) |

### Streak logic

Runs once per grade (Wrong or Correct both count — any training activity
keeps the streak alive; only Correct earns coins, see below):

- `last_active_date` is `None` → `current_streak = 1`
- `last_active_date == today` → no change (already active today)
- `last_active_date == today - 1 day` → `current_streak += 1`
- otherwise (gap of 2+ days, or first grade after a break) → `current_streak = 1`
- `last_active_date = today`
- `longest_streak = max(longest_streak, current_streak)`

### Coins

- **+1 coin** (`stats.COINS_PER_CORRECT`) on every **Correct** grade. Wrong
  grades earn nothing (no penalty either).
- **Session-complete bonus**: flat **+10 coins** (`stats.SESSION_COMPLETE_BONUS`)
  when the last due card for the day is graded Correct (today's queue
  empties). Previously scaled with the daily streak (`4 + current_streak`);
  simplified to a flat amount.
- **Achievement rewards**: unlocking an achievement also pays out coins —
  10 for the easiest/first tier of a family (or for standalone
  achievements, set explicitly per-achievement), scaling up via
  `achievements.REWARD_BY_TIER_INDEX` for harder tiers (20, 35, 60, 100,
  150, 250, 400). See `check_and_unlock_achievements` — conditions are
  evaluated from a snapshot taken *before* any reward is applied in that
  pass, specifically so one achievement's reward can't spuriously push a
  coin-threshold achievement (e.g. "First Coins") over its target within
  the same check. (Cascading *across separate* calls — e.g. an earlier
  unlock's reward genuinely pushing a coin achievement over target on the
  *next* grade — is expected and fine.)
- Nothing else to spend coins on yet — displayed as a running score. First
  real sink will be chests (later phase).

### Session progress bar

A purple progress bar shown above the card in Train, representing progress
toward today's Daily Training quest (see Daily quests, below) — **not** a
locally-computed fraction of the full due queue. The bar reads
`progress_current`/`progress_target` straight off `GET /quests`' `daily_train`
entry (`percent = progress_current / progress_target`), the same data the
Profile page's Daily Quests box renders, refetched after every grade. This
means the bar counts down from a flat 10 (`TRAIN_TARGET`, see Daily
quests, below), not from the full due count — the two bars are guaranteed
identical since they're driven by the same backend values, not two
separate calculations.

This replaced an earlier version that computed
`percent = (initialDueCount - currentQueueLength) / initialDueCount`
entirely from frontend session-queue state (uncapped by 10) — that
diverged from the Daily Quests bar on any day with more than 10 cards due,
since the two bars used different denominators. Bug reported by the user
("the bar on the daily quest daily training and on the training page are
not the same"); fixed by making Train read the same quest data instead of
computing its own percentage.

Two distinct numbers are shown on this page, deliberately kept visually
separate rather than merged into one, since they answer different
questions and can genuinely diverge on a day with more than 10 cards due:
- **"N card(s) left to review"** (above the bar) — `queue.length`, the
  actual count of unlearned/due cards remaining in today's full session
  (unbounded, can be more than 10).
- **"🎯 Daily goal: X/Y"** (caption under the bar) — the same
  `daily_train` quest values the bar itself uses, i.e. progress toward
  the capped daily target.

An earlier iteration tried collapsing these into one number (making the
"left" text itself `progress_target - progress_current`) to match the bar
exactly — reverted after the user pointed out they actually wanted *both*
pieces of information visible, not one replacing the other.

### Achievements

Definitions live in code (`app/achievements.py`), not the database — each
is a key, title, description, emoji badge (placeholder art for now — real
badges to be designed later), a numeric `target`, and a `current` function
returning the live progress value (not just a boolean) over current
`Stats` + live card aggregates (total cards, sum of `times_correct`/
`times_wrong` across all cards). Unlocked when `current >= target`. Unlocks
are recorded one row per key in `AchievementUnlock` (key + UTC timestamp);
absence of a row means locked. Checked after grading a card, adding a card,
or completing a session — idempotent (already-unlocked keys are skipped).
Unlocks are cleared by Admin's "Reset all progress" action
(`clear_achievements`), and — as of the reversal described in Open
decisions — the underlying stats they check are cleared right along with
them, so a reset actually re-locks things rather than leaving them one
grade away from instantly re-unlocking. Each achievement also pays out
coins on unlock (see Coins, below); coin-based achievements use
`Stats.lifetime_coins_earned` rather than the resettable `coins` balance,
but since both are now reset together, they stay equal to each other in
practice (no coin-spending sink exists yet to make them diverge).

`GET /achievements` includes `progress_current`/`progress_target` per
achievement (current capped at target for a clean "X/Y" display) so the
frontend can show a progress indicator, not just locked/unlocked.

**Tiered families**: streak, correct-answer, coin, and deck-size
achievements each form a `family` (an `AchievementDef.family` string,
`None` for standalone achievements). Rather than listing every tier,
`GET /achievements` collapses each family down to **at most two** entries:
- the highest tier already completed (`unlocked: true`) — its `history`
  lists the earlier completed tiers in that family (key/title/badge/
  `unlocked_at` each). Absent if nothing in the family is unlocked yet.
- the next not-yet-unlocked tier (`unlocked: false`), with its own live
  `progress_current`/`progress_target`. Absent once the whole ladder is
  complete (nothing left to work toward).

So a family with no progress shows one (locked) tile; a family with
partial progress shows two (one completed+colored with history, one
locked+shaded showing what's next); a fully-completed family shows one
(the last tier, unlocked, full history). This lets the UI always show
"what you've done" and "what's next" side by side without the grid
growing unbounded as more tiers get added. Standalone achievements (First
Steps, Session Complete) always have an empty `history` and never pair
with a second tile. `check_and_unlock_achievements` itself is unaffected
by families — it still checks and can unlock every tier independently
(e.g. a big stat jump could unlock two tiers in the same event); the
two-tiles-max collapsing only happens at read-time in `list_achievements`.

Starting list (53 achievement tiers across 10 families/standalones — easy
to extend, just add an `AchievementDef` with the right `family`):

| Badge | Title | Target |
|---|---|---|
| 🌱 | First Steps | ≥1 lifetime grade (correct or wrong) |
| 🙈 | Nobody's Perfect | ≥1 lifetime wrong grade |
| 🌟 | Flawless Session | ≥1 session completed with zero Wrong grades |
| 🔄 | Comeback Kid | ≥1 card graded Wrong then Correct on its next grade |
| 🌅 | Early Bird | Trained 4am–7am (local time), at least once |
| 🦉 | Night Owl | Trained 11pm–4am (local time, spans midnight), at least once |
| 🔥 | Week Warrior → Year of Learning | `longest_streak` (daily login): 7/30/60/100/365 |
| ✅ | Getting Started | 10 lifetime correct answers |
| ✅ | Century | 100 lifetime correct answers |
| ✅ | High Five Hundred | 500 lifetime correct answers |
| 🪙 | First Coins | 10 lifetime coins earned |
| 🪙 | Piggy Bank | 100 lifetime coins earned |
| 🪙 | Treasure Hoard | 500 lifetime coins earned |
| 📚 | First Card | 1 card added |
| 📚 | Building Your Deck | 10 cards added |
| 📚 | Growing Collection | 30 cards added |
| 📚 | Vocabulary Builder | 50 cards added |
| 📚 | Serious Collector | 100 cards added |
| 📚 | Deck Master | 250 cards added |
| 📚 | Lexicon Legend | 500 cards added |
| 🏁 | Session Complete → Session Legend | Sessions completed: 1/5/10/25/50/100/250/500 |
| 🎯 | Hat Trick → Perfection | `longest_correct_streak` (answers in a row, resets on Wrong): 3/5/10/25/50/100 |
| 🎓 | Word Master → Master Linguist | `cards_mastered` (cards that crossed the 64-day interval): 1/5/10/25/50 |
| 🏃 | Quarter Marathon → Iron Learner | `largest_session_completed` (biggest queue ever cleared in one sitting): 25/50/100/200 |

### Daily quests

Definitions live in code (`app/quests.py`), not the database — same shape
as `AchievementDef` (key, title, description, emoji badge, `coin_reward`),
but `target` is a `Callable[[Stats], int]` rather than a fixed number (see
Daily Training below for why), and `current` is a `Callable[[Stats], int]`
scoped to *today* instead of lifetime. **Static for now** (identical every
day) — designed so the set can rotate/change later without a data-model
change, since each quest is just an entry in `DAILY_QUESTS`:

| Badge | Title | Target |
|---|---|---|
| 📚 | Deck Builder | Add 5 cards today |
| 🎯 | Daily Training | Get 10 cards correct today — always 10, not adaptive (see below) |

(Target column above documents the mechanic; the actual `description` shown
in the UI is deliberately much shorter — "Add 5 cards today." /
"Practice 10 cards in Train." — the numeric target/progress is already
visible via the progress bar's "X/Y", so the description doesn't need to
restate it.)

**Daily Training's target is a flat constant, `TRAIN_TARGET` (10)** —
`target` is still typed `Callable[[Stats], int]` (so a future quest could
still be adaptive) but this one ignores its `Stats` argument entirely.
Progress is `quest_correct_today`, a `Stats` counter incremented on every
Correct grade, and the Train page's own progress bar reads this exact
`daily_train` quest data (see Session progress bar, above) — so both bars
count down from the same number and reach 100% at the same moment.

This is the **second** design for this quest's target, not the first.
Originally it was a boolean "complete today's session," then changed to
`max(quest_train_floor, min(10, session_initial_due))` — a countdown
capped at whatever's actually due (plus a floor that grew over time) so
the quest was never unreachable on a light due-count day, since a card
leaves the due queue for the day once graded Correct. **Reverted to a
flat 10 per explicit request** — the adaptive target made day-to-day
difficulty unpredictable, and a flat, always-the-same "practice 10 cards"
was judged more valuable than guaranteed reachability. Accepted trade-off:
on a day with fewer than 10 cards due, this quest can go uncompleted
until more cards are due or added — that's intended, not a bug to fix.
`quest_train_floor` and the `TRAIN_FLOOR_*` constants from the earlier
design were removed entirely (not just unused) since nothing reads them
any more.

Progress resets once per calendar day: `Stats.sync_day` checks
`Stats.quest_date` and resets `quest_cards_added_today`/
`quest_correct_today` on rollover. It also recomputes today's due count in
the same call, so `session_initial_due` (used for the Train page's "N
cards left to review" count and the Marathon achievement, but no longer
for the Daily Training target) is correctly frozen for the day regardless
of whether the Train page, the Profile page, or neither has been opened
yet today. Both quests' progress
is a `Stats` counter incremented only by the actual action that should
count (`record_quest_card_added` from `POST /cards`,
`record_quest_correct_grade` from `POST /cards/{id}/grade` on a Correct
grade) — **not** derived live from existing data like `Card.created_at`.
That was the original design for the "add cards" quest (count of cards
with today's date), and it caused a real bug: any card inserted by other
means with today's timestamp — e.g. the dev `seed_data.py` script, which
bypasses `POST /cards` entirely — silently counted toward the quest. A DB
reseed (needed after this feature's own schema change) planted 25
same-day-timestamped cards and the quest showed as already satisfied on
first load, despite nothing having been added through the app that day.
Fixed by switching to an explicit counter incremented only on the real
add action.

Completion (and its one-time coin reward) is recorded in
`DailyQuestCompletion` — one row per `(quest_key, completed_date)`, the
quest equivalent of `AchievementUnlock` but re-completable every day
instead of once ever. This is what actually gates the reward to "once per
quest per day": progress can keep climbing past the target for the rest
of the day without re-awarding, since a completion row already exists for
today. Checked via `check_and_complete_quests` after adding a card and
after grading a card Correct — same snapshot-then-reward two-phase
pattern as `check_and_unlock_achievements`, for the same reason (a reward
shouldn't spuriously satisfy another quest's condition within the same
check). Cleared by Admin's "Reset all progress" (`clear_quest_completions`,
plus `quest_date`/`quest_cards_added_today`/`quest_correct_today` reset in
`reset_all_stats`) — unlike the deck-size *achievements*, both quests'
progress genuinely goes back to 0 on reset, since both are `Stats`
counters rather than a live card count.

`GET /quests` → list of `{ key, title, description, badge, completed,
progress_current, progress_target, coin_reward }`, one entry per quest (no
family-collapsing needed — there's no tiering, just today's fixed set).

### Leveling (XP + Level)

`Stats` gains `xp` (int, running total) and `level` (int, starts at 1) —
unlike profile identity, this **is** gamification progress, so it's
zeroed by "Reset all progress" (`reset_all_stats`) rather than surviving
like `total_cards`, consistent with the app's established policy that
lifetime-feeling fields do not survive a reset (see Open decisions #5 —
that policy exists precisely because leaving fields like this alone
caused real confusing bugs before).

**XP mirrors coin-earning 1:1** — every action that earns coins earns the
identical amount of XP, via the exact same call sites, no separate event
wiring: a Correct grade (`stats.py`'s `record_training_activity`,
`+COINS_PER_CORRECT`), the session-complete bonus (`award_session_complete`,
`+SESSION_COMPLETE_BONUS`), and achievement/quest coin rewards (an extra
`xp :r` added to the existing `ADD coins :r, lifetime_coins_earned :r`
DynamoDB transaction in `achievements.check_and_unlock_achievements`/
`quests.check_and_complete_quests` — same summed-reward value, same
atomic write, just one more attribute touched).

**Level is purely derived from `xp`**, not tracked incrementally itself —
`app/leveling.py`'s `level_for_xp(xp)` walks `xp_for_level(level)`
(cumulative XP needed to *reach* a level: `100 * (level-1) * level / 2`,
i.e. 100/300/600/1000 XP for levels 2/3/4/5 — each level needs 100 more
XP than the last to reach, same escalating-but-not-exploding shape as the
achievement tiers). This means level-up isn't gated by a completion-row
the way achievement/quest unlocks are (nothing to guard against
double-awarding — a given xp total always derives the same level), so
`leveling.finalize_level(store, user_id, stats)` is a **separate, simple**
step (not folded into the achievement/quest transactions above): called
once per request, *after* every other stats-mutating step regardless of
how many separate xp sources fired, it recomputes level from the final
xp total and, if it went up, awards a flat `LEVEL_UP_COIN_REWARD` (20)
bonus coins per level gained (summed if multiple levels are crossed in
one big xp jump) via one plain `update_item` — safe to call
unconditionally, a no-op returning 0 when xp didn't cross a new
threshold. Called from `POST /cards`, `POST /cards/{id}/grade`, and
`POST /stats/session-complete` — the three routes that can move xp.

No dedicated `GET /level` endpoint — `xp`/`level` ride along on the
existing `GET /stats` (`StatsOut`), same reasoning as profile identity
above (`Stats` already is the one-item-per-user blob).

### Collection (titles, card-colour/font themes, lootboxes)

The "chests" feature flagged as unscoped back in the Achievements phase —
built as one cluster (`app/collection.py`) since titles/themes and
lootboxes aren't meaningfully useful alone: a title you can never obtain
isn't real, and a lootbox with nothing in it isn't real.

**Definitions live in code, not the database** — same pattern as
`AchievementDef`/`QuestDef`. `TitleDef` (key, display name, `rarity`:
common/rare/epic/legendary, display-only) and `ThemeDef` (key, name,
rarity, `colors` — a dict of CSS custom-property overrides applied at the
document root when equipped, see Frontend below — and an optional
`font_display` override) each currently have a small fixed list (11
titles, 7 themes) spanning all four rarities. `LootboxTierDef` defines
three tiers — Bronze (50 coins), Silver (150), Gold (400) — each with a
`REWARD_WEIGHTS` table over four categories (coins/xp/title/theme);
`title`/`theme` are dropped from that tier's roll entirely (not just
given a 0 weight) once nothing new is left to award in that category, so
a near-completionist never wastes a roll. Coin/XP reward amounts scale by
tier (`COIN_REWARD_RANGE`/`XP_REWARD_RANGE`, e.g. bronze 10-30, gold
100-200).

**`Stats` gains**: `owned_titles`/`owned_themes` (key lists),
`equipped_title`/`equipped_theme` (nullable keys, at most one of each
equipped at a time), and `lootbox_bronze`/`lootbox_silver`/`lootbox_gold`
(int inventory counts — chosen as three flat fields over a nested
map/dict, consistent with every other DynamoDB-backed counter in this
app being a flat attribute). This **is** gamification progress (unlike
profile identity), so it's reset by "Reset all progress" — same
reasoning as xp/level (Open decisions #15).

**Acquiring lootboxes**: purchasable with coins (`POST
/collection/lootboxes/{tier}/buy`) *and* earned free — every level-up
grants one Bronze box (`leveling.LEVEL_UP_LOOTBOX_REWARD`, folded into
`finalize_level`'s existing per-level-up `update_item` call rather than a
second write). No achievement-tied box grants yet (a documented
simplification — flag if you want specific achievement milestones to
also grant boxes).

**Opening a box** (`POST /collection/lootboxes/{tier}/open`,
`collection.open_lootbox`) decrements inventory and rolls one reward via
`roll_lootbox_reward`, mutating `Stats` directly and persisted via the
same plain `save_stats` read-modify-write the rest of `stats.py` already
uses — deliberately **not** a `transact_write_items` call the way
achievement/quest unlocks are, since opening a box is a single explicit
user action with nothing to guard against double-processing (unlike
achievement checks, which re-run on every grade and need a completion-row
idempotency guard). A coin or XP reward from a box can cross an
achievement or level threshold, so the route re-runs
`check_and_unlock_achievements`/`finalize_level` afterward and returns
any resulting notices alongside the reward itself
(`LootboxOpenResult.newly_unlocked_achievements`/`newly_leveled_up`).

**Equipping** (`POST /collection/equip`, body `{title?, theme?}` — same
omit-vs-null convention as `PATCH /profile`) requires ownership
(`collection.equip_title`/`equip_theme` raise 400 otherwise); `null`
un-equips. `GET /collection` returns every title/theme definition
annotated with `owned`/`equipped`, plus each lootbox tier's info and
current inventory count — the single source of truth `CollectionPage`
renders directly, no client-side merging needed.

### Celebration popup (achievements, daily quests, and level-ups)

Whenever an achievement is newly unlocked, a daily quest is newly
completed, or the user levels up, the frontend pops a full-screen
celebration: a confetti burst (`canvas-confetti`, ~3KB, no React wrapper —
just called imperatively in a `useEffect`) plus a modal with a heading
("Grats! You earned an achievement!" / "Quest complete!" / "Level up!"),
the badge (large emoji), title, description, and the coin reward earned.
Same modal component for all three — `AchievementUnlockNotice`/
`QuestCompletionNotice`/`LevelUpNotice` all share the identical shape
(`key`/`title`/`description`/`badge`/`coin_reward`), so `CelebrationModal`
just takes a `celebration` object tagged with
`kind: "achievement" | "quest" | "level_up"` to pick the heading text.
`LevelUpNotice`'s `key`/`title`/`description` are synthesized from the new
level number (`f"level_{level}"`, `f"Level {level}!"`) rather than looked
up from a static definitions list the way achievements/quests are, since
a level has no fixed catalog entry to look up.

No new endpoints for this — `check_and_unlock_achievements`,
`check_and_complete_quests`, and `leveling.finalize_level` were already
called as side effects of `POST /cards` and `POST /cards/{id}/grade`
(achievements and leveling also on `POST /stats/session-complete`), but
their return values (lists of newly-unlocked/newly-completed keys, or a
levels-gained count) used to be discarded or nonexistent. Now
`CardOut`/`StatsOut` carry `newly_unlocked_achievements:
list[AchievementUnlockNotice]` and `newly_leveled_up: list[LevelUpNotice]`
(all three endpoints for both) and `CardOut` also carries
`newly_completed_quests: list[QuestCompletionNotice]` (only
`POST /cards` and `POST /cards/{id}/grade` — quests don't complete via
session-complete), populated via `achievements.describe_achievements(keys)`
/ `quests.describe_quests(keys)` / a small inline builder for the
level-up notice — empty on every other call (`GET /cards`,
`PATCH /cards/{id}`, etc.). Deliberately attached to the existing
responses instead of a separate endpoint/polling mechanism, since the
unlock/completion/level-up can only happen exactly when one of those
actions runs — no new round-trip needed, and no risk of missing/
duplicating a notification between requests.

Frontend: `TrainPage` (after grading and after session-complete) and
`DeckPage` (after adding a card) call `onAchievementsUnlocked`,
`onQuestsCompleted`, and `onLeveledUp` callbacks with those fields;
`App.jsx` owns a single global FIFO queue (`celebrationQueue`, mixing all
three kinds) so the popup shows regardless of which tab triggered it, and
multiple simultaneous unlocks/completions/level-ups (e.g. crossing
several deck-size tiers in one add, or an achievement and a quest
completing on the same grade) queue up and show one at a time rather than
overlapping. Popup renders at the `App`
level (`z-50`, covers everything) so it isn't tied to any one page's
lifecycle.

### API

- `GET /stats` → `{ username, avatar_key, equipped_title, equipped_theme,
  xp, level, xp_into_level, xp_for_next_level, coins, current_streak,
  longest_streak, last_active_date, session_initial_due }`. The last two
  `xp_*` fields are computed (`@computed_field` properties on `StatsOut`,
  not stored) straight from `xp`/`level` via `leveling.xp_for_level` — a
  ready-to-use `progress_current`/`progress_target` pair for the Profile
  page's XP bar, same idea as achievements'/quests' progress fields. Also
  freezes `session_initial_due` for the day on first call (see above).
- `PATCH /profile` → `{ username?, avatar_key? }`, returns the updated
  `StatsOut` (see Profile identity, below). Both fields optional and
  independent; omit to leave unchanged, `null` to clear.
- `POST /stats/session-complete` → applies the session-complete bonus,
  returns updated stats. Called once by the frontend exactly when grading a
  card empties the due queue (not on page load with an already-empty queue).
- `CardOut`/`StatsOut` (returned by `POST /cards`, `POST /cards/{id}/grade`,
  `POST /stats/session-complete`) include `newly_unlocked_achievements`
  (empty unless that call unlocked something) — see Achievement-unlock
  celebration, above.
- `POST /reset-all-progress` → the single Admin reset action: **every**
  `Stats` field including the lifetime achievement-tracking ones (via
  `reset_all_stats`), every card's scheduling *and* lifetime counters (via
  `reset_card_progress`, looped over all cards), and every achievement
  unlock (`clear_achievements`). Cards themselves are kept. (Originally
  left the lifetime fields alone so achievements would "survive" a reset —
  reversed, see Open decisions, after real use showed that causes
  confusing bugs.)
- `GET /achievements` → list of achievement entries (families already
  collapsed to at most two tiles, see above) with `unlocked`/`unlocked_at`/
  `progress_current`/`progress_target`/`coin_reward`/`history` per key.
- `GET /quests` → list of today's daily quests with `completed`/
  `progress_current`/`progress_target`/`coin_reward` per key (see Daily
  quests, above). Also syncs the daily reset for the day on first call.
- `GET /collection` → `{ titles, themes, lootboxes }` (see Collection,
  above) — every title/theme definition with `owned`/`equipped`, every
  lootbox tier with its cost and current inventory count.
- `POST /collection/equip` → `{ title?, theme? }`, returns updated
  `StatsOut`. Requires ownership (400 otherwise); `null` un-equips.
- `POST /collection/lootboxes/{tier}/buy` → deducts coins, returns the
  updated `CollectionOut`.
- `POST /collection/lootboxes/{tier}/open` → rolls and applies one
  reward, returns `{ kind, key?, name?, amount?,
  newly_unlocked_achievements, newly_leveled_up }`.
- `DELETE /cards` — deletes every card. Admin-only, destructive.
- No new grading endpoint — `POST /cards/{id}/grade` (existing) now also
  updates `Stats` as a side effect alongside the card's schedule.

### Frontend

A small stats bar (🔥 streak, 🪙 coins) visible across all pages, refreshed
after every grade action in Train, plus the session progress bar described
above shown only on the Train page. A separate **Progress** page (see
below) is the fuller view — streak/coins/session summary, daily quests,
extra stats, and the achievement grid. Chests are a later phase with their
own data model, not designed yet.

### Profile page

Renamed from "Progress" (`ProgressPage.jsx` → `ProfilePage.jsx`) once
username/avatar (Phase 9), leveling (Phase 10), and Collection (Phase 11)
existed to actually justify a "Profile" identity, not just a stats page.
Nav icon unchanged (📈).

New header above everything else: avatar emoji (`avatarEmoji(stats.avatar_key)`
from `avatars.js`) + `stats.username` (falls back to "Your Profile" if
unset) + the equipped title's display name directly beneath it (looked up
from `GET /collection`'s titles list — `StatsOut` only carries the
*key*, `equipped_title`, not the display name; the Profile page is the
one place that needs it, so it isn't worth denormalizing onto `StatsOut`
the way `xp_into_level` was). Absent entirely if no title is equipped.

Then a new **Level card**: "Level *N*" and a purple `ProgressBar` reading
`xp_into_level`/`xp_for_next_level` straight off `GET /stats` (computed
fields, see Leveling above) — same "just render what the backend already
computed" pattern as the Daily Quests bars below it.

Then the streak/coins/card-count/accuracy summary (🔥/🪙/📚/🎯), now a
**5-item** `grid grid-cols-3` (wraps 3-then-2) rather than a single-row
flex, gaining a 🎁 lootbox-count stat (summed across all three tiers from
`GET /collection`) — a plain viewport-width breakpoint (`sm:`) would have
been the wrong tool here, since this app's content column is capped
narrow (~384px) regardless of actual device width (see `DESIGN.md`
Layout), so "make it responsive" has to mean "wraps within a
fixed-width card," not "changes at a screen-size breakpoint that may
never even apply to this column."

Then the existing **Daily Quests** box (one row per `GET /quests` entry
— badge, title, description, a small purple progress bar reusing the
Train page's `ProgressBar` component, "X/Y" progress, and the coin reward
or a ✅ once completed), unchanged, and the achievement grid below — one tile per
`GET /achievements` entry (badge + title), unlocked ones full color, locked
ones dimmed. For a tiered family with partial progress this means **two**
tiles side by side: the highest tier completed (colored) and the next tier
up (dimmed) — the grid still doesn't grow as more tiers get added, since
it's always at most two tiles per family regardless of ladder length.
Clicking a tile opens a popup with the description, a progress indicator
(`progress_current`/`progress_target`, small purple bar reusing the Train
page's `ProgressBar` component), the unlock date/time if unlocked, and —
only on the completed tile of a tiered family — a "Previously completed"
list of earlier tiers already unlocked in that family, each with its own
unlock date/time. Standalone achievements and the "next tier" tile never
show that section (nothing to list).

### Collection page

A new "Collection" tab (5th nav icon, 🎁 — bottom pill bar grows from four
icons to five): a **Lootboxes** card listing all three tiers (name, coin
cost, current inventory count, Buy/Open buttons — Open disabled at 0),
then a **Titles** grid and a **Card colours** grid, both reusing the
achievement grid's visual language (owned tiles full color, unowned
dimmed/grayscale, click to equip — clicking an already-equipped tile
un-equips it). Each theme tile shows a small color swatch (the theme's
`primary` value) alongside its name/rarity so you can preview before
equipping. Opening a box shows a full-screen reveal (icon by reward kind
— 🪙 coins, ⚡ xp, 🏷️ title, 🎨 theme — plus the amount or name won); any
achievement unlock or level-up the reward happened to trigger still queues
through the normal `App.jsx` celebration queue on top of that reveal.

**Applying an equipped theme**: `frontend/src/collectionTheme.js`'s
`applyCollectionTheme(theme)` sets the theme's `colors`/`font_display` as
**inline** CSS custom properties directly on `<html>` (not a class) —
inline styles win the cascade over both the light default `@theme` values
*and* the `html.dark {...}` override block (see `DESIGN.md`'s Dark theme
section), so an equipped theme's accent color reads identically in light
and dark mode; only the untouched neutral background/surface/ink tokens
keep responding to the dark toggle. Applied in two places: once by
`CollectionPage` itself immediately on equip (no round trip needed, the
theme data is already in hand), and once by `App.jsx` on every app load
(fetches `GET /collection` alongside `GET /stats` purely to find the
currently-equipped theme and re-apply it — a brief flash of the default
green before this resolves is an accepted, subtle cosmetic gap, unlike
light/dark's own synchronous pre-paint script in `index.html`, which
exists specifically because *that* flash is much more jarring).

### Profile identity (username + avatar)

`Stats` gains `username`/`avatar_key` (both nullable strings) — permanent
user preferences, not gamification progress, so **not** touched by
"Reset all progress" (same reasoning as `total_cards`; see Rules and
conventions in `CLAUDE.md`). `avatar_key` is a semantic key into a fixed
preset list (`app/profile.py`'s `AVATAR_KEYS`), not a stored image —
explicit choice over user-uploaded avatars, avoiding new S3/moderation
infrastructure for a personal app (see Open decisions #12). The frontend
(`avatars.js`) owns the key→emoji mapping so swapping these for real
custom SVGs later (Phase 16, blocked on artwork) is a rendering change
only. `PATCH /profile` sets either/both fields independently (omit a
field to leave it unchanged, send `null` to clear it); no uniqueness
check on username. Surfaced back to the frontend via the existing
`GET /stats` response (`StatsOut` gained the same two fields) rather than
a separate endpoint, since `Stats` already is the one-item-per-user blob.

### Settings page

A "Settings" tab (renamed from "Admin" — same page, same auth model, just
better named now that it holds profile editing too, not just destructive
actions). No streak/coins/due-count summary shown here (that's the
Profile page's job; showing it twice was redundant):
- **Profile** — username (text input + Save) and avatar (a grid of preset
  emoji, click to select — saves immediately via `PATCH /profile`, no
  separate Save step for the avatar).
- **Appearance** — the Light/Auto/Dark theme toggle (`ThemeToggle.jsx`,
  see `DESIGN.md`'s Dark theme section). No confirm dialog.
- **Change password** — current/new/confirm password fields, calls
  Cognito's `ChangePassword` Identity Provider API **directly from the
  frontend** (`auth.js`'s `changePassword`) with the current access
  token — no new backend endpoint, no Lambda IAM permission. Same "raw
  fetch to a Cognito endpoint, no SDK" style `auth.js` already uses for
  the OAuth token exchange, just a different Cognito endpoint
  (`cognito-idp.<region>.amazonaws.com`, not the Hosted UI domain).
  Requires the app client to actually be allowed to use this API: the
  access token needs the `aws.cognito.signin.user.admin` OAuth scope,
  added to both `login()`'s requested scopes and the app client's
  `allowed_oauth_scopes` in `terraform/cognito.tf` — a real (if small)
  infrastructure change, since a scope isn't retroactive for
  already-issued tokens (existing sessions need to log in again to pick
  it up, which happens naturally within 60 minutes since access tokens
  that short-lived already force frequent re-auth).
- **Reset all progress** — the single full reset (`POST
  /reset-all-progress`, behind a confirm dialog): streak, coins, session
  baseline, every card's scheduling, all achievement unlocks, and all
  daily-quest completions. Previously this was split across
  four separate buttons (reset streak / reset coins / reset all stats /
  reset training progress); collapsed to one since the app doesn't need
  that granularity in practice. Does **not** touch profile identity (see
  above).
- **Log out**.
- **Delete ALL cards** — separate "danger zone" (behind its own confirm
  dialog), most destructive action (actually removes card data, not just
  progress).

Behind the same Cognito auth as every other page/route — scoped to
whichever user is logged in, same as everywhere else. No extra
admin-specific gating (e.g. no separate "admin role") since every user
administers only their own data.

## Future features (explicitly out of scope for now)

- **Pronunciation audio**: play the French word's pronunciation, likely via
  an AI TTS API.
- **AI-generated example sentences**: given the words you already know plus
  X new words you could learn, generate example sentences using only those,
  and let you add the new words to your deck.

These are noted here so the data model/API can be extended later (e.g. an
`audio_url` field, an "example sentences" sub-resource) without needing a
redesign, but no work happens on them until the core loop is solid.

## Open decisions / assumptions

These are reasonable defaults chosen to keep the spec moving — flag any of
these you'd like changed:

1. **Due date granularity**: day-level (UTC), not exact timestamps. A card
   due "in 2 days" becomes due at the start of that UTC date.
2. **Queue order**: not yet decided (shuffled vs oldest-due-first) — will
   decide during implementation, easy to change.
3. **Accounts/auth**: originally deferred ("no accounts in Phase 1,
   decide access control when AWS starts"). Resolved once the AWS
   migration actually started: Cognito Hosted UI, genuinely multi-tenant
   (not just an auth gate) — see Multi-tenancy / AWS deployment, above.
4. **Only two grades (Wrong/Correct)**, no "Hard" — kept deliberately simple.
   If in practice you find Wrong (full reset) too harsh for "I knew it but
   was slow," we can revisit adding Hard later — but starting minimal.
5. **Admin's single "Reset all progress" action is a genuine full reset.**
   Originally, to keep achievements "permanent," it deliberately left the
   lifetime achievement-tracking fields alone (`lifetime_coins_earned`,
   `sessions_completed`, `cards_mastered`, `comebacks`,
   `longest_correct_streak`, the time-of-day flags, per-card
   `times_correct`/`times_wrong`/`mastered`) while still clearing
   `AchievementUnlock` rows. In practice this produced confusing bugs: the
   visible `coins` balance permanently drifted from `lifetime_coins_earned`
   (which achievements actually check against), and achievements based on
   any of those fields re-unlocked the instant *any* new activity
   happened — e.g. "Flawless Session" showing unlocked from just adding a
   card, with no session ever completed — since the numbers backing them
   never actually went back down. **Reversed**: the reset now zeroes every
   `Stats` field and every per-card lifetime counter, not just scheduling
   state. The one remaining, unavoidable exception: deck-size achievements
   (based on `total_cards`) can still show nonzero progress right after a
   reset, because this action doesn't delete cards — only "Delete ALL
   cards" does that, and it's separate and more destructive.
6. **Card front/back reversed from the original design.** Originally
   showed French first (recognition: see French, recall meaning); reversed
   per explicit request to show English first, French on the back
   (production: see English, recall/produce the French). The `Card` model
   still names its columns `french`/`english` (accurate, stable identifiers
   for the actual language of each value) — only the frontend's display
   order changed (`front={english}`/`back={french}` in `TrainPage.jsx`),
   not the database schema. The Add Card form's field labels were changed
   from "French"/"English" to generic "Front"/"Back" wording at the same
   time (matching the flip mechanic's own vocabulary) rather than e.g.
   "English (front)"/"French (back)" — a little less explicit about which
   language goes where, but the "hello"/"bonjour" placeholders carry that
   cue implicitly. Revisit the labels if that's not clear enough in
   practice.
7. **Daily quest set is static, not yet rotating.** "Add 5 cards" and
   "Daily Training" are the same every day — designed so a future
   rotating/random selection is just a change to `DAILY_QUESTS` in
   `app/quests.py`, not a data-model change (see Daily quests, above). The
   training quest's target went through three iterations: first "complete
   today's session" (a boolean, to avoid a light-due-day making a fixed "N
   correct today" unreachable), then `max(quest_train_floor, min(10,
   session_initial_due))` — a numeric countdown, matching the Train page's
   own progress bar exactly, while keeping the same "never unreachable on
   a light day" property since it capped at whatever's actually due — then
   simplified to a flat, always-10 `TRAIN_TARGET` per explicit request
   (see Daily quests, above), trading that reachability guarantee for a
   predictable, unchanging target.
8. **Early Bird / Night Owl time windows don't overlap, and Night Owl spans
   midnight.** Originally Early Bird was "any hour before 7am" and Night
   Owl was "hour ≥ 23" — meaning training right after midnight (e.g.
   00:19) satisfied *neither* the intended "late at night" definition (it's
   clearly still up-late, not "before 7am" in the early-riser sense) *and*
   incorrectly satisfied Early Bird's literal condition instead, so a night
   owl could get mislabeled as an early riser. Fixed: Early Bird is now
   `[4am, 7am)`, Night Owl is `[11pm, 4am)` (spanning midnight via
   `hour >= 23 or hour < 4`) — the two windows are adjacent and
   non-overlapping, and every hour of the day is covered by exactly one of
   {Early Bird, Night Owl, neither}, never both.

   This was **not**, however, the actual cause of the user-reported "Night
   Owl still not unlocking" at 00:18 local time — that turned out to be a
   second, separate bug: the app was running via `docker compose`, and the
   backend **container's clock was UTC, 2 hours behind the host's real
   `Europe/Oslo` time** (`docker exec ... date` showed `22:xx UTC` while
   the host showed `00:xx CEST`). Every local-wall-clock-time check
   (`date.today()` for the daily streak rollover, `datetime.now().hour` for
   Early Bird/Night Owl) was silently computing against the wrong
   timezone — the host-machine dev server (`uvicorn` run directly, not
   containerized) never showed this symptom, which is what made it
   non-obvious at first. Fixed by bind-mounting the host's resolved
   `/etc/localtime` read-only into the backend service in
   `docker-compose.yml` — see that file's comment and `CLAUDE.md`'s Rules
   section. Both fixes were needed for the user's original report to
   fully resolve. (Historical — `docker-compose.yml` no longer exists,
   Docker was retired entirely when the app moved to AWS. Left here
   because the *first* half of this entry, the non-overlapping time
   windows, is still exactly how `stats.py` works today.)
9. **AWS compute/database: Lambda + API Gateway + DynamoDB**, not ECS
   Fargate + ALB + RDS Postgres (the first design considered), not a
   single EC2 instance running the retired Docker Compose setup as-is
   (a real, viable, ~$11.60/mo alternative). Real cost numbers drove this:
   ECS+ALB+RDS worked out to ~$40-48/mo (the ALB's flat hourly charge
   dominates, not the compute), vs. Lambda+API Gateway+DynamoDB landing
   at effectively $0/mo at this app's traffic level. The DynamoDB port was
   initially assessed as "too large/risky" (given ~50 achievement tiers'
   worth of aggregation logic) — that assessment didn't hold up: nearly
   all of `Stats` was already maintained as running counters rather than
   live SQL aggregates, so the actual port was mechanical, not a redesign.
   See `CLAUDE.md`'s Architecture section for the resulting DynamoDB
   schema and the plan referenced there for the full comparison.
10. **Duplicate-card prevention is frontend-only, and same-field (front-vs-
    front, back-vs-back), not cross-field.** Explicit choice when asked:
    cross-field matching (checking a new front against existing *backs*
    too) was rejected because it would wrongly block legitimate front/back
    swaps between two different cards (e.g. one card's back becoming
    another card's front). Backend enforcement was also explicitly
    declined — the already-loaded deck list on the Deck page makes the
    frontend check free (no extra request), and this app has no scenario
    (no bulk import, no multi-device concurrent add) where a
    frontend-only check would meaningfully under-protect. Revisit (add a
    backend check in `cards.create_card`) if either of those assumptions
    stops holding — e.g. a bulk-import feature that bypasses the Deck
    page form.
11. **Pre-built decks are non-owned, browsable practice content — not an
    import-into-your-deck feature.** A dev commits a key/value text file
    to the repo; the app parses it into a deck you can practice against
    without it ever becoming a row in your own `Cards` table. Chosen over
    "one-click bulk-import into your deck" specifically so pre-built
    content never touches real spaced-repetition scheduling. See
    `TASKS.md` Phase 13/14 for the resulting design (static content files
    parsed at Lambda cold-start, same pattern as achievements/quests;
    practice sessions against them are schedule-free).
12. **Avatars are a preset icon set, not user-uploaded images.** No new
    storage infrastructure, no moderation surface — same pattern as the
    existing emoji/achievement-badge system. See `TASKS.md` Phase 9.
13. **Custom SVG icons (nav bar + achievement families) are blocked on the
    user supplying artwork**, not scheduled for active implementation.
    Nav icons and achievement badges are already single, isolated data
    points (`App.jsx`'s nav array, `AchievementDef.badge`), so the
    eventual swap-in is mechanical once art exists. See `TASKS.md`
    Phase 16.
14. **Extra Training / practice sessions (all cards, a labeled subset, or
    a pre-built deck) are entirely schedule-free.** Grading a card there
    never touches `interval_days`/`due_date`/`times_correct`/
    `times_wrong` — consistent with pre-built-deck words having no `Card`
    row at all to mutate in the first place. Assumed (pending
    confirmation) to also mean no coins/streak/quest/achievement credit
    during practice, since that machinery isn't Card-row-independent
    today; a practice round's only feedback is a client-side summary that
    never reaches the backend. See `TASKS.md` Phase 14.
15. **Leveling's XP curve, coin bonus, and reset policy** — three
    assumed numbers/decisions, flag any if you want them changed:
    `LEVEL_XP_STEP = 100` (level *N* needs cumulative `100*(N-1)*N/2`
    XP — 100/300/600/1000 for levels 2-5), `LEVEL_UP_COIN_REWARD = 20`
    flat coins per level gained, and **xp/level reset on "Reset all
    progress"** (chosen over "survives resets" specifically *because* the
    lifetime-fields-survive-resets pattern already caused real bugs once
    — see #5 above — not because leveling is inherently less permanent
    than achievements in spirit). See `TASKS.md` Phase 10 and `app/leveling.py`.
16. **Lootbox tier costs/rewards, and the decision to skip achievement-
    tied box grants for now.** Bronze/Silver/Gold cost 50/150/400 coins;
    reward-category weights and coin/XP ranges scale by tier (see
    Collection, above) — all picked to feel roughly proportional to the
    achievement coin-reward scale (`REWARD_BY_TIER_INDEX`), not derived
    from any formula. Boxes are earned free only via level-ups (one
    Bronze per level) — no specific achievement milestone grants a box
    yet, a deliberate scope cut to ship this phase without also editing
    every achievement tier's reward. Flag any of these numbers, or ask
    for achievement-tied box grants, if the balance feels off in
    practice — all are easy, isolated changes in `app/collection.py`.
17. **Card-colour themes re-tint the whole app's primary accent, not
    individual cards.** "Card colours (select cards)" was read as
    "select which colour scheme to apply," not "assign a colour to a
    specific card" — the equipped theme changes `--color-primary`/
    `-dark`/`-light` globally (buttons, the flip card, nav highlight,
    etc.), the same three tokens dark mode itself overrides. Flag if you
    actually wanted per-card tagging instead — that's a materially
    different feature (closer to Phase 13's per-card labels than a
    theme).
