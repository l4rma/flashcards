#!/usr/bin/env bash
# Builds backend/lambda.zip for deployment — run this before `terraform
# apply` in terraform/ (or after any app/ code change, before re-applying).
#
# boto3/botocore are deliberately excluded from requirements-lambda.txt —
# the Lambda Python runtime already bundles them, so including our own
# copy would only bloat the zip for no benefit.
set -euo pipefail

cd "$(dirname "$0")"

rm -rf build lambda.zip
mkdir -p build

pip3 install \
  --platform manylinux2014_x86_64 \
  --target=build \
  --implementation cp \
  --python-version 3.13 \
  --only-binary=:all: \
  -r requirements-lambda.txt

cp -r app build/

(cd build && zip -r ../lambda.zip . -x '*.pyc' -x '__pycache__/*' -x '*/__pycache__/*')

echo "Built lambda.zip ($(du -h lambda.zip | cut -f1))"
