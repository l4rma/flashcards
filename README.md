# Flash Cards

See `SPEC.md` for design, `TASKS.md` for the phased build plan, `DESIGN.md`
for the visual style brief.

## Deployment

This app runs on AWS only — FastAPI on Lambda (via Mangum) behind API
Gateway, DynamoDB for storage, Cognito for login, S3 + CloudFront for the
frontend, all provisioned with Terraform. There is no local dev server or
Docker setup — that was a deliberate decision, not an oversight (see
`CLAUDE.md`'s "Deployment target" note and `SPEC.md`'s Tech stack /
Open decisions #9 for why). Iteration happens by deploying via CI/CD and
testing against the real AWS environment.

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
  `cards.py`/`stats.py`/`achievements.py`/`quests.py` (DynamoDB-backed
  business logic), `scheduling.py` (pure spaced-repetition functions, no
  storage dependency), `auth.py` (reads the Cognito claims API Gateway's
  JWT authorizer already verified), `models.py` (plain dataclasses, no
  ORM), `database.py` (the `Store` DynamoDB client wrapper).
- `frontend/` — React + Vite + Tailwind, built as a static bundle for S3.
- `terraform/` — not yet authored (see `TASKS.md` Phase 7).
