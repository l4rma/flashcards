terraform {
  # >= 1.11 for the S3 backend's native `use_lockfile` state locking below
  # (replaces the older S3+DynamoDB-lock-table pairing — no DynamoDB table
  # needed at all now).
  required_version = ">= 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Partial config — bucket/key/region filled in at `terraform init` time
  # via `-backend-config=backend.hcl` (see backend.hcl.example), pointing
  # at the bucket the bootstrap/ config creates. Left empty here so this
  # file doesn't hardcode a bucket name that only exists after bootstrap
  # has been applied once. `use_lockfile` is fixed/environment-independent
  # so it's hardcoded here rather than in backend.hcl.
  backend "s3" {
    use_lockfile = true
  }
}
