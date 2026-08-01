# Pronunciation-audio cache (Amazon Polly output, mp3 files keyed by a
# hash of the French text — see backend/app/pronunciation.py). Private
# bucket + CloudFront Origin Access Control, same shape as
# aws_s3_bucket.frontend in frontend.tf — the actual CloudFront origin/
# behavior wiring lives there too, alongside the one distribution this
# app already has (see frontend.tf's own comment on why /api/* shares
# that distribution instead of getting a separate one).
resource "aws_s3_bucket" "audio" {
  bucket = "${var.project_name}-audio-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "audio" {
  bucket                  = aws_s3_bucket.audio.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "audio" {
  name                              = "${var.project_name}-audio-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_s3_bucket_policy" "audio" {
  bucket = aws_s3_bucket.audio.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontServicePrincipal"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.audio.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
        }
      }
    }]
  })
}
