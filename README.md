# Flash Cards

Live at https://d3kfmju6qasf0s.cloudfront.net. Source at
https://github.com/l4rma/flashcards (private).

See `SPEC.md` for design, `TASKS.md` for the phased build plan, `DESIGN.md`
for the visual style brief.

## Deployment

This app runs on AWS only — FastAPI on Lambda (via Mangum) behind API
Gateway, DynamoDB for storage, Cognito for login, S3 + CloudFront for the
frontend, all provisioned with Terraform. There is no local dev server or
Docker setup — that was a deliberate decision, not an oversight (see
`CLAUDE.md`'s "Deployment target" note and `SPEC.md`'s Tech stack /
Open decisions #9 for why). Iteration happens by deploying manually
against the real AWS environment ("testing in prod" — see `CLAUDE.md`'s
Deployment section for the exact commands); there's no CI/CD pipeline yet
(tracked in `TASKS.md`).

## Running tests

```bash
cd backend
pip3 install --user --break-system-packages -r requirements.txt  # first time
python3 -m pytest
```

Tests run entirely against **moto-mocked DynamoDB** — no AWS credentials,
no network access, no real infrastructure needed.

## Repo layout

- `backend/app/` — FastAPI app. `main.py` (routes + the Lambda `handler`),
  `cards.py`/`stats.py`/`achievements.py`/`quests.py`/`leveling.py`/
  `collection.py` (DynamoDB-backed business logic), `scheduling.py` (pure
  spaced-repetition functions, no storage dependency), `prebuilt_decks/`
  (parses the `*.txt` deck files bundled alongside it — add a file, get a
  deck), `profile.py` (avatar/username constraints), `auth.py` (reads the
  Cognito claims API Gateway's JWT authorizer already verified),
  `models.py` (plain dataclasses, no ORM), `database.py` (the `Store`
  DynamoDB client wrapper).
- `frontend/` — React + Vite + Tailwind, built as a static bundle for S3.
- `terraform/` — flat root module provisioning all of the above (DynamoDB,
  Lambda, API Gateway, Cognito, S3/CloudFront) + `terraform/bootstrap/`
  (one-time remote-state setup). See `CLAUDE.md`'s Deployment section for
  the apply commands.
