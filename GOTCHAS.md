# Gotchas

A running log of real bugs hit in this project — specifically the kind
that passed code review, passed tests, and only showed up against real
AWS after deploying. Each entry: what broke, why, how it was found, and
the fix. Add a new entry whenever a bug like this happens; don't edit
old entries except to fix mistakes in them.

This is a companion to `CLAUDE.md`'s "Rules and conventions" section,
not a replacement for it — conventions that shape how code should be
*written* going forward still belong there. This file is specifically
for postmortems: a concrete incident, with a symptom you can pattern-match
against next time something looks similar.

---

## Pronunciation audio: two real-AWS-only bugs neither test suite nor code review could catch

**Date**: 2026-08-01
**Feature**: French pronunciation audio (Amazon Polly + S3/CloudFront cache — see `SPEC.md`'s "Pronunciation audio" section)

**Symptom**: Deployed, backend tests all passing (213/213), oxlint/build
clean, visually verified in a Playwright harness. Tapped the speaker icon
in the real app — icon flashed red (the error state), no sound, no
objects ever appeared in the S3 audio bucket.

**Why the test suite didn't catch it**: both root causes are real-AWS
behaviors that moto (the DynamoDB/S3/Polly mocking library this project's
whole test suite is built on) doesn't simulate:
- moto doesn't enforce IAM authorization at all — a mocked S3 call
  succeeds regardless of what the caller's IAM policy actually allows.
- moto doesn't model per-region service/engine availability — a mocked
  Polly `SynthesizeSpeech` call succeeds for any voice/engine combination
  regardless of region.

Neither gap is a flaw in the tests as written; it's a structural limit of
mocking cloud APIs at all. The lesson isn't "write different tests" —
it's **after deploying a new AWS-integration feature, check CloudWatch
logs for the real Lambda before declaring it done**, not just "user,
please try it and tell me." `aws logs tail /aws/lambda/<name> --since
<window> --format short` (needs `AWS_REGION` set explicitly, or
`--region`) would have surfaced both of these immediately, before ever
asking for a manual retry.

### Bug 1 — `HeadObject` returned 403 instead of 404 for a key that didn't exist yet

**Root cause**: the IAM policy granted `s3:GetObject`/`s3:PutObject` on
`<bucket-arn>/*` (object-level) but not `s3:ListBucket` on
`<bucket-arn>` itself (bucket-level — a genuinely different resource ARN,
no trailing `/*`). This is a documented, non-obvious S3 behavior: without
`ListBucket`, S3 returns `403 Forbidden` instead of `404 Not Found` for a
`HeadObject`/`GetObject` on a missing key, specifically so a caller
without list access can't use a 404-vs-403 timing/response difference to
enumerate what *does* exist in the bucket. The app's cache-check
(`_exists()` in `app/pronunciation.py`) only treated 404 as "not cached
yet" and re-raised anything else — so on a brand-new, empty bucket,
*every single request* hit this and crashed before ever reaching Polly.

**How it was found**: `aws logs tail` on the real Lambda showed the full
traceback ending in `botocore.exceptions.ClientError: An error occurred
(403) when calling the HeadObject operation: Forbidden`. Confirmed the
identity-based policy looked right at a glance, then confirmed the
missing piece with `aws iam simulate-principal-policy` (which *only*
evaluates identity-based policy + org SCPs — a useful reminder that it
does *not* account for resource-based bucket policies, so it can give a
false "allowed" if a bucket policy's explicit Deny is the actual blocker;
that wasn't the case here, but it's worth knowing what the tool does and
doesn't check).

**Fix**: added a third IAM statement — `s3:ListBucket` scoped to the
bucket ARN itself (`terraform/lambda.tf`).

**Pattern to remember**: any time code does a "does this object exist?"
check (`HeadObject`, or `GetObject` wrapped in a not-found catch) against
S3, the IAM policy needs **both** the object-level action (`GetObject`)
**and** `ListBucket` on the bucket. Granting only the object-level action
works fine once the object exists, and works fine in any mock — it only
fails, in a confusing way (403, not 404), for a *genuinely missing*
object against real S3. A cache/existence-check code path is exactly
where that gap bites hardest, since checking for absence is the whole
point.

### Bug 2 — Polly's neural engine isn't available in every region

**Root cause**: this app's Lambda runs in `eu-north-1` (Stockholm). Amazon
Polly's neural engine is only available in a subset of AWS regions, and
`eu-north-1` isn't one of them for French voices — confirmed via
`aws polly describe-voices --language-code fr-FR --region eu-north-1`,
which showed Léa's `SupportedEngines` as `["standard"]` only there (vs.
`["neural", "standard"]` in `eu-west-1`). Every `SynthesizeSpeech` call
with `Engine="neural"` failed with `ValidationException: The selected
engine is not supported in this region`.

**How it was found**: same `aws logs tail` traceback, next request after
fixing Bug 1 (the code got further — past the cache check — before
hitting this).

**Fix**: rather than downgrading to the more robotic standard engine,
pinned the Polly client specifically to `region_name="eu-west-1"`
(`POLLY_REGION` constant in `app/pronunciation.py`) — confirmed with a
direct `aws polly synthesize-speech --region eu-west-1 ...` call that
this actually produces audio before redeploying. S3/DynamoDB/everything
else stays in `eu-north-1`; only the Polly client itself points
elsewhere, since Polly doesn't care where the resulting audio bytes get
stored afterward. Cross-region calls between AWS services are ordinary
and fine — no VPC peering or special networking needed, it's still just
an HTTPS API call, just to a different regional endpoint.

**Pattern to remember**: before picking a specific engine/voice/model tier
for *any* regional AWS AI/ML service (Polly, Transcribe, Comprehend,
Bedrock, etc.), check `describe-*`/`list-*` availability against the
*actual deployment region*, not just "does this feature exist on AWS
somewhere." A feature being real and documented doesn't mean it's in the
region your infra already lives in — and moving the *whole* deployment to
chase one service's regional availability is almost never worth it
compared to just pointing that one client at a different region.
