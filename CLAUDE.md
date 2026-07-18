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
   hard way.

## Deployment target: AWS only, no local dev

There is **no local/Docker deployment target for this app** — this was a
deliberate decision (not an oversight): the app runs exclusively on AWS
(Lambda + API Gateway + DynamoDB + Cognito + CloudFront/S3, all via
Terraform), and is developed/iterated on by deploying via CI/CD and
testing against the real deployed environment ("testing in prod," since
this is a personal single/small-multi-user app with no uptime SLA). Do not
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
  `achievements.py` (lifetime achievement unlocks), `quests.py` (daily
  quests — same `Def`/`check_and_complete`/`list_*` shape as
  `achievements.py`, but scoped to *today* instead of lifetime, and its
  `target` is a `Callable[[Stats], int]` rather than a fixed number since
  the training quest's target is derived from `session_initial_due`). All
  date-dependent functions take an explicit `today: date | None` parameter
  for testability instead of calling `date.today()` internally.
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
- Admin's "Reset all progress" (`POST /reset-all-progress`) resets
  **everything** for the current user — every `Stats` field except
  `total_cards`, and every per-card field
  (`times_correct`/`times_wrong`/`mastered`/`last_grade` included), not
  just scheduling state. This used to deliberately spare lifetime
  achievement-tracking fields so achievements would "survive" a reset —
  reversed after a real user-reported bug: the visible `coins` balance
  permanently drifted from `lifetime_coins_earned` (which achievements
  actually check), and achievements re-unlocked from a single new
  card/grade right after a reset since their underlying numbers never
  actually went back down (e.g. "Flawless Session" showing unlocked with
  no session ever completed). Don't reintroduce the "lifetime fields
  survive resets" pattern — deck-size achievements (`total_cards`) are the
  one remaining, unavoidable exception (cards aren't deleted by this
  action, only by the separate "Delete ALL cards"). This also must stay
  scoped to the current user only — `clear_achievements`/
  `clear_quest_completions`/the reset-all-progress card loop all filter by
  `user_id`; a global unfiltered delete would wipe every user's data, not
  just the one who clicked reset (this was an actual near-miss caught
  while adding multi-tenancy — the original single-user code had no such
  filter since there was only ever one user).
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
- Don't add browser-based TTS/pronunciation (Web Speech API) again on this
  machine — confirmed dead end (Chromium-based browsers here expose zero
  voices to it even with `espeak-ng`/`speech-dispatcher` installed at the OS
  level). Any future pronunciation feature must generate audio server-side.
- This user prefers: make the fix, run a fast/cheap self-check (backend
  pytest), then hand off for manual testing — don't chain long diagnostic
  sessions to self-verify frontend/UI changes.
