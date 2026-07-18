# One-time, manually-applied config to create the S3 bucket the main
# terraform/ config's own remote state lives in. Deliberately separate
# from the main config (which can't create the backend it's stored in —
# chicken-and-egg). Uses local state itself; that local state file only
# matters for re-running this bootstrap (e.g. to destroy it later) and
# isn't needed day-to-day once the main config is initialized against the
# bucket it creates.
#
# No DynamoDB lock table — as of Terraform 1.11+, S3 supports native
# state locking via `use_lockfile = true` on the backend block (see
# versions.tf), replacing the older S3+DynamoDB pairing.

terraform {
  required_version = ">= 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

variable "aws_region" {
  type    = string
  default = "eu-north-1"
}

variable "project_name" {
  type    = string
  default = "flash-cards"
}

provider "aws" {
  region = var.aws_region
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.project_name}-tfstate-${random_id.suffix.hex}"
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket                  = aws_s3_bucket.terraform_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "state_bucket" {
  value = aws_s3_bucket.terraform_state.bucket
}
