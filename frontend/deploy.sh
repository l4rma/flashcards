#!/usr/bin/env bash
# Builds the frontend and deploys it to S3 + invalidates CloudFront.
# Run after `terraform apply` (reads its outputs) and after populating
# frontend/.env with the Cognito values (see .env.example).
set -euo pipefail

cd "$(dirname "$0")"

TF_DIR="../terraform"
BUCKET=$(terraform -chdir="$TF_DIR" output -raw frontend_bucket)
DISTRIBUTION_ID=$(terraform -chdir="$TF_DIR" output -raw cloudfront_distribution_id)
DOMAIN=$(terraform -chdir="$TF_DIR" output -raw cloudfront_domain)

npm run build

aws s3 sync dist/ "s3://${BUCKET}" --delete

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths '/*' > /dev/null

echo "Deployed to ${DOMAIN}"
