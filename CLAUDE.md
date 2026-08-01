# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow — read this first

This project is developed spec-driven. Before starting **any** new feature
or change:

1. Read `SPEC.md` (design/architecture) and `TASKS.md` (phased checklist)
   to understand current state and where the work fits. Don't assume —
   check.
2. If the request doesn't fit cleanly into what's already speced, design it
   in `SPEC.md`/`TASKS.md` first (or at least talk through the approach)
   before writing code, the same way prior features in this repo were
   scoped before implementation.

After finishing any change:

3. Update `SPEC.md` and `TASKS.md` to match reality — check off completed
   tasks, add new ones you discover, correct anything the implementation
   ended up doing differently than planned. These files are the source of
   truth for the next session; treat a change as unfinished until they're
   updated.
4. If you land on a new convention, constraint, or gotcha while working
   (not just this-one-time decision) — add it to the **Rules and
   conventions** section below so future sessions don't rediscover it the
   hard way. If it's specifically a real bug that only surfaced after
   deploying (passed tests/review, broke against real AWS) — log it in
   `GOTCHAS.md` too, with the symptom, root cause, and fix, so a similar
   symptom later can be pattern-matched against a past incident instead
   of re-diagnosed from scratch.

## Deployment target: AWS only, no local dev

There is **no local/Docker deployment target for this app** — this was a
deliberate decision (not an oversight): the app runs exclusively on AWS
(Lambda + API Gateway + DynamoDB + Cognito + CloudFront/S3, all via
Terraform), and is developed/iterated on by deploying manually (see
Deployment, below) and testing against the real deployed environment
("testing in prod," since this is a personal single/small-multi-user app
with no uptime SLA). There's no CI/CD pipeline yet — deploys are a person
running the commands below, not a push-triggered pipeline (tracked as an
open item in `TASKS.md`). Do not
reintroduce `docker-compose.yml`, per-service `Dockerfile`s, a local
SQLite backend, or a `uvicorn --reload`/`npm run dev` workflow as if
they're still supported — they were explicitly retired. See the AWS
migration plan (referenced from `SPEC.md`) for the full design rationale.

## Commands

```bash
cd backend
python3 -m pytest                                                    # all tests
python3 -m pytest tests/test_scheduling.py                           # one file
python3 -m pytest tests/test_scheduling.py::test_wrong_resets_interval_to_zero_and_leaves_due_date  # one test
```

Tests run entirely against **moto-mocked DynamoDB** (no real AWS access,
no Docker, no local server) — see `tests/conftest.py`'s `store` fixture.

Dependencies are installed to user site-packages, not a venv — this
machine's Python is Debian's externally-managed-environment and has no
`python3-venv` package:

```bash
pip3 install --user --break-system-packages -r requirements.txt
```

Frontend (`frontend/`) is built with `npm run build` for deployment to S3
— there's no dev-server workflow to run day-to-day anymore (see above).
`npx oxlint .` lints it (no separate config needed beyond what's in
`package.json`). A temporary local `npm run dev` + a throwaway
Playwright harness (mocked auth/API, deleted before finishing — never
committed) is the established way to visually verify frontend/design
changes before shipping, since there's no persistent dev-server workflow
and the real app requires a live Cognito/API round trip.

## Deployment

`terraform/` (flat root module, no nested modules) + `terraform/bootstrap/`
(one-time remote-state setup, separate config — see its file header).
`AWS_PROFILE` needs to point at credentials with real permissions (`aws
sts get-caller-identity` to check) — `default`/other profiles in this
environment may be stale; a working one existed as `debian` as of the
first deployment attempt, but don't assume that name stays valid forever.

```bash
# One-time (creates the Terraform state bucket — no DynamoDB lock table
# needed, S3 does native locking via `use_lockfile` as of Terraform 1.11+):
terraform -chdir=terraform/bootstrap apply
# copy terraform/backend.hcl.example -> backend.hcl with its outputs, then:
cd terraform && terraform init -backend-config=backend.hcl

# Every deploy:
./backend/build_lambda.sh      # rebuilds backend/lambda.zip
terraform -chdir=terraform apply
# copy frontend/.env.example -> .env with `terraform output` values, then:
./frontend/deploy.sh           # npm run build, s3 sync, CloudFront invalidation
```

`terraform plan`/`validate` can be run without real AWS mutation at any
time to sanity-check changes — `apply` is the only step that actually
creates/changes real infrastructure and costs money; treat it with the
same care as any other irreversible action (see the general "executing
actions with care" guidance) — confirm with the user before running it,
same as the first deployment.

## Full task workflow: test → commit → push → deploy

When a task explicitly asks to test, commit, push, and/or deploy the
change (not just implement it), do these in order — don't stop after
implementing and call it done:

1. **Test.** Cheap/fast self-check only, scoped to what changed:
   - Backend touched → `python3 -m pytest` (at least the relevant file).
   - Frontend touched → `npx oxlint .`.
   - Don't spin up a dev server or build a throwaway Playwright harness to
     self-verify UI/visual changes unless the task specifically calls for
     that check (see Commands, above) — this project's default is to hand
     visual verification to the user.
2. **Commit.** Stage only the files relevant to the change (not a blanket
   `git add -A`), write a commit message explaining why. Follow the
   general git safety rules (new commit, not `--amend`; no `--no-verify`).
3. **Push.** `git push` to `origin main` — this repo pushes straight to
   main, no PR/branch flow, no CI to gate it (see Source control, below).
4. **Deploy**, matching what actually changed, only after commit+push so
   the deployed artifact matches what's in git:
   - Frontend-only change → `./frontend/deploy.sh` (build, S3 sync,
     CloudFront invalidation).
   - Backend/infra change → `./backend/build_lambda.sh` (if backend
     changed) then `terraform -chdir=terraform apply` — **apply still
     needs explicit user confirmation first**, per the Deployment section
     above; this workflow authorizes running the *sequence*, not skipping
     that specific confirmation.
   - Remember `AWS_PROFILE=debian` (or whatever profile currently has
     working credentials — see Deployment, above) for both.
5. Report the live URL/result back so the user can verify online, rather
   than assuming the task is done once `apply`/`deploy.sh` exits 0.

This whole sequence is manual because there's no CI/CD pipeline yet
(tracked as an open item in `TASKS.md`, Phase 7). Once that exists, "push"
will likely trigger test+deploy automatically and this checklist should
shrink accordingly — don't keep hand-running steps CI already covers once
it's live.

## Source control

Version-controlled and pushed to GitHub: https://github.com/l4rma/flashcards
(private repo, `main` branch, no CI configured — see "no CI/CD pipeline
yet" above). Local repo root was renamed from `flash-cards` to
`flashcards` for naming consistency — AWS resources were deliberately
**not** renamed to match (still `flash-cards-*`: S3 buckets, Cognito
domain, Lambda function, IAM roles), since renaming those forces
recreating uniquely-named resources for no functional benefit. Don't
"fix" that mismatch — it's intentional.

## Architecture

- **Backend**: FastAPI, packaged for Lambda via `Mangum` (`app/main.py`'s
  `handler = Mangum(app, api_gateway_base_path="/api")`), fronted by API
  Gateway (HTTP API) with a native JWT authorizer validating Cognito tokens
  *before* Lambda is ever invoked — `app/auth.py`'s `get_current_user_id`
  only *reads* the already-verified `sub` claim off the raw Lambda event
  (`request.scope["aws.event"]`), it does no cryptographic verification
  itself. The `/api` prefix CloudFront forwards is stripped here (Mangum's
  `api_gateway_base_path`), not via a CloudFront Function — see the
  CloudFront gotchas below for why.
- **Storage: DynamoDB, no SQL, no ORM.** Four tables, one per concern —
  `Cards` (PK `user_id`, SK `id`, GSI `due-index` on `due_date` for
  due-card queries), `Stats` (PK `user_id` only, one item per user),
  `Achievements` (PK `user_id`, SK `achievement_key`), `QuestCompletions`
  (PK `user_id`, SK `"<date>#<quest_key>"`). All On-Demand billing — no
  capacity planning. `app/models.py`'s `Card`/`Stats` are **plain
  dataclasses**, not an ORM — `app/cards.py`/`app/stats.py` convert to/from
  DynamoDB items (dates/datetimes as ISO strings, since DynamoDB has no
  native date type). `scheduling.py`'s pure functions (spaced-repetition
  grading) operate on the `Card` dataclass via plain attribute access,
  completely unaware of storage — this was true before the DynamoDB
  migration too and stayed true after, deliberately.
- **No schema migrations needed for new attributes** (DynamoDB is
  schemaless — old items just lack the field until first written; reads
  use `.get(key, default)`). The one thing DynamoDB genuinely can't do in
  place is a **key-schema change** (unlike SQL's `ALTER TABLE`, this
  requires a new table + backfill) — rare, but not free if it comes up.
- **`stats.py` functions are pure** (`record_training_activity`,
  `award_session_complete`, `reset_all_stats`, etc. take a `Stats` object
  and mutate it in place, no I/O) — only `get_or_create_stats`/`save_stats`
  do I/O. A route fetches `Stats` once, threads the *same* object through
  every mutating call in that request, and saves once — DynamoDB has no
  implicit unit-of-work/session the way an ORM did, so this threading is
  deliberate, not incidental. `achievements.py`/`quests.py`'s reward
  functions (`check_and_unlock_achievements`/`check_and_complete_quests`)
  are the one exception: they persist their own coin reward directly via a
  `transact_write_items` call (see below) *and* mutate the same in-memory
  `Stats` object to match, so the caller never needs to re-fetch.
- **Achievement/quest unlock + coin reward is one atomic DynamoDB
  transaction** (`client.transact_write_items`: one `Put` per newly
  unlocked achievement/quest, `ConditionExpression="attribute_not_exists(...)"`
  as an idempotency guard, plus **exactly one** `Update` with
  `ADD coins :r, lifetime_coins_earned :r` on the `Stats` item, summing
  every simultaneous reward first in application code — a transaction
  can't include two operations on the same item, so multiple
  simultaneous unlocks must be pre-summed, not applied as separate
  `Update`s). Preserves the pre-existing "snapshot every condition before
  applying any reward" invariant (see Rules below) — just moved from a
  SQLAlchemy commit to a DynamoDB transaction.
- **`total_cards`/`total_correct`/`total_wrong` are `Stats` counters**,
  incremented at the same call sites as every other counter (card
  creation; a Correct/Wrong grade) — **not** derived from a live
  SQL-style aggregate over `Cards`, since DynamoDB has no `SUM`/`COUNT`
  query. `total_cards` is deliberately **not** reset by "reset all
  progress" (mirrors the old live-query behavior: that action doesn't
  delete cards, so the count of cards that exist shouldn't drop either).
- Business logic lives in small modules the routes in `main.py` call
  into: `scheduling.py` (spaced-repetition grading, storage-agnostic),
  `cards.py` (Card CRUD against DynamoDB), `stats.py` (gamification —
  streak/coins/session tracking, pure mutations + explicit I/O),
  `achievements.py` (lifetime achievement unlocks — 66 tiers across 26
  families/standalones as of the last count, growing with each new
  feature area), `quests.py` (daily quests — same `Def`/
  `check_and_complete`/`list_*` shape as `achievements.py`, but scoped to
  *today* instead of lifetime, and its `target` is a
  `Callable[[Stats], int]` rather than a fixed number since the training
  quest's target is derived from `session_initial_due`), `leveling.py`
  (XP/level derivation — `finalize_level` must be called *twice* per
  request around achievement/quest checks, see Rules below),
  `collection.py` (titles/card-colour themes/lootboxes), `profile.py`
  (the preset avatar key list + username length limit), and the
  `prebuilt_decks/` package (parses `*.txt` deck files bundled alongside
  it — add a new file, get a new deck, no code change). All
  date-dependent functions take an explicit `today: date | None`
  parameter for testability instead of calling `date.today()` internally.
- `Stats` is **one item per user** (partition key `user_id`) — this app is
  genuinely multi-tenant (Cognito login, each user gets their own separate
  deck/progress), not a single global singleton the way it was before the
  AWS migration.
- **`_get_card_or_404`-style ownership checks are structurally
  guaranteed**, not a `WHERE`-clause discipline problem: every card
  operation addresses `Key={"user_id": user_id, "id": card_id}`, and
  `user_id` only ever comes from the verified JWT, never client input —
  there's no way to reference another user's card without already knowing
  their `user_id`.
- The Train session queue (ordering, requeueing Wrong cards) is
  **frontend-only** state, not persisted server-side. The backend only ever
  tracks each card's durable schedule (`interval_days`/`due_date`) — see
  "Session queue logic" in `SPEC.md`.
- **Frontend**: React + Vite + Tailwind v4 (CSS-based `@theme` config in
  `index.css`, no `tailwind.config.js`). No router — `App.jsx` does manual
  tab-state switching between pages. No component library; styling follows
  the palette/shape/type rules in `DESIGN.md`.
- **Light/dark theme** is a single `html.dark { --color-*: ...; }` override
  block in `index.css` (`theme.js` toggles the class, preference persisted
  in `localStorage`) — since every color already flows through named
  theme tokens, this needed zero `dark:` variants or per-component color
  logic. See `DESIGN.md`'s "Dark theme" section for the palette and why
  this override approach works against Tailwind v4's layered `@theme`
  output.
- Full design rationale for the AWS migration (cost comparisons, schema
  design reasoning, why Lambda+DynamoDB over ECS+RDS or plain EC2) lives in
  `SPEC.md`'s Tech stack / Open decisions sections — this file
  intentionally doesn't repeat all of it.

## Rules and conventions

- **Two real CloudFront/API Gateway gotchas hit during first deployment,
  both worth knowing before touching `terraform/frontend.tf` again:**
  1. **Don't strip the `/api` prefix with a CloudFront Function on
     `viewer-request`.** A `viewer-request` function that rewrites
     `request.uri` (e.g. `/api/cards` → `/cards`) causes CloudFront to
     apply the *rewritten* path when actually routing/caching the request,
     so it stops matching the `/api/*` ordered cache behavior's path
     pattern and silently falls through to the default (S3) behavior on
     every request — no error, just wrong content served, and genuinely
     hard to notice since CloudFront's `get-distribution-config` output
     still shows the (correct-looking, but effectively unused) behavior.
     Strip the prefix on the Lambda side instead: Mangum's
     `api_gateway_base_path="/api"` (see `app/main.py`).
  2. **Don't use `Managed-AllViewer` as the origin request policy for a
     custom (non-S3) origin like API Gateway.** It forwards the viewer's
     own `Host` header verbatim instead of letting CloudFront set it to
     the origin's own domain, and API Gateway's `execute-api` endpoint
     rejects a mismatched `Host` with a generic `403 Forbidden`
     (`ForbiddenException`) — easy to misdiagnose as a routing/behavior
     bug (especially since a `custom_error_response` 403→200 mapping to
     `/index.html` masks it as the frontend loading instead of an error,
     and that mapped response can stay stuck in CloudFront's cache across
     invalidations for a surprisingly long time, which sent this exact
     debugging session down the wrong path first). Use
     `Managed-AllViewerExceptHostHeader` instead — same header forwarding,
     minus this specific footgun.
- Only two grades exist: **Wrong** / **Correct** — no "Hard". Don't
  reintroduce a third grade without updating `SPEC.md`'s explicit "Open
  decisions" note about this.
- Settings' "Reset all progress" (`POST /reset-all-progress`, on the page
  renamed Admin → Settings in the profile-identity phase) resets
  **everything** for the current user *except* `total_cards` and profile
  identity (`username`/`avatar_key`) — every other `Stats` field
  (including everything added since: `xp`/`level`, Collection's
  owned/equipped titles-themes and lootbox inventory, the practice/label
  achievement-tracking flags) and every per-card field
  (`times_correct`/`times_wrong`/`mastered`/`last_grade`/`label`
  included), not just scheduling state. This used to deliberately spare
  lifetime achievement-tracking fields so achievements would "survive" a
  reset — reversed after a real user-reported bug: the visible `coins`
  balance permanently drifted from `lifetime_coins_earned` (which
  achievements actually check), and achievements re-unlocked from a
  single new card/grade right after a reset since their underlying
  numbers never actually went back down (e.g. "Flawless Session" showing
  unlocked with no session ever completed). **Every new Stats field
  added since must default to this same policy (reset) unless it's
  identity, not progress** — `total_cards` and profile identity are the
  only two carve-outs, and both are deliberate, narrow exceptions, not a
  precedent to extend casually. This also must stay scoped to the
  current user only — `clear_achievements`/`clear_quest_completions`/the
  reset-all-progress card loop all filter by `user_id`; a global
  unfiltered delete would wipe every user's data, not just the one who
  clicked reset (this was an actual near-miss caught while adding
  multi-tenancy — the original single-user code had no such filter since
  there was only ever one user).
- In `achievements.check_and_unlock_achievements`
  /`quests.check_and_complete_quests`, always evaluate every
  achievement/quest's condition from a snapshot taken *before* applying
  any coin reward in that same pass — applying rewards mid-loop lets one
  unlock's payout spuriously satisfy another (a coin-threshold achievement
  in particular). This was a real bug once; don't reintroduce it. In the
  DynamoDB implementation this means: compute the full list of
  newly-satisfied conditions first, *then* build and send one
  `transact_write_items` call — never re-read `Stats` mid-loop.
- **boto3 DynamoDB resource client vs plain client — don't reuse
  `resource.meta.client` for `transact_write_items`.** A `boto3.resource("dynamodb")`
  registers serialization hooks on its own client that transform
  Python-native values into DynamoDB's AttributeValue format for
  Table-level calls (`put_item`/`get_item`/`query`). `transact_write_items`
  is a raw client-level call that needs *already*-low-level AttributeValue
  dicts (built here via `database.serialize_item`) — reusing
  `resource.meta.client` for it double-serializes every value (e.g. a
  string becomes `{"M": {"S": {"S": "value"}}}` instead of `{"S": "value"}`),
  which DynamoDB (and moto) reject with a `TransactionCanceledException`
  whose cancellation reasons just say `TypeError` with no further detail —
  genuinely confusing to debug from the error alone. Fixed by giving
  `Store` (`app/database.py`) a **separate**, plain `boto3.client("dynamodb")`
  for this specific call. If a `transact_write_items` call ever fails with
  an opaque `TypeError` cancellation reason again, check this first before
  assuming the item contents are wrong.
- **`leveling.finalize_level` must be called twice per request, not
  once** — once right after the routine stats mutation (so an
  achievement condition reading `stats.level` sees the *current* level,
  not one from before this request's xp gain), and once again after
  achievements/quests are checked (to catch a level-up triggered by
  *their* reward xp, which the first call couldn't have seen yet). This
  was a real bug: calling it only once, after achievement checks (which
  seemed natural — level derives from xp, and achievement/quest rewards
  add xp too), meant a level-based achievement condition always
  evaluated a stale level, delaying that unlock by one action. Caught by
  a genuinely failing test, not a user report. `_finalize_level` in
  `app/main.py` is a safe no-op when xp hasn't crossed a new threshold,
  so calling it twice costs nothing when nothing changed — every route
  that can move xp (`POST /cards`, `POST /cards/{id}/grade`,
  `POST /stats/session-complete`, `POST /collection/lootboxes/{tier}/open`,
  `POST /practice/completed`) follows this same before-*and*-after
  pattern; don't add a new xp-moving route with only one call.
- Don't add browser-based TTS/pronunciation (Web Speech API) again on this
  machine — confirmed dead end (Chromium-based browsers here expose zero
  voices to it even with `espeak-ng`/`speech-dispatcher` installed at the OS
  level). Any future pronunciation feature must generate audio server-side.
- This user prefers: make the fix, run a fast/cheap self-check (backend
  pytest), then hand off for manual testing — don't chain long diagnostic
  sessions to self-verify frontend/UI changes.
