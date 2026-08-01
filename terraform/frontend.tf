resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project_name}-frontend-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_name}-frontend-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  origin {
    domain_name = replace(aws_apigatewayv2_api.this.api_endpoint, "https://", "")
    origin_id   = "api-gateway"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Pronunciation-audio cache (see audio.tf) — a second, separate private
  # S3 bucket + OAC on this same distribution, same reasoning as sharing
  # one distribution for /api/* instead of standing up a second one.
  origin {
    domain_name              = aws_s3_bucket.audio.bucket_regional_domain_name
    origin_id                = "s3-audio"
    origin_access_control_id = aws_cloudfront_origin_access_control.audio.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_optimized.id
  }

  # The `/api` prefix is NOT stripped here — a CloudFront Function
  # (viewer-request) that rewrites the URI was tried first and caused a
  # genuine, hard-to-diagnose bug: CloudFront re-evaluates cache-behavior/
  # origin selection using the function's rewritten path for the actual
  # request, so `/api/cards` -> `/cards` no longer matched this `/api/*`
  # pattern and silently fell through to the default (S3) behavior on
  # every request (a documented CloudFront gotcha — origin-request, which
  # runs after behavior selection, would avoid it, but that event type
  # needs Lambda@Edge, not CloudFront Functions). Fixed by leaving the
  # full `/api/cards` path untouched here and stripping the prefix on the
  # Lambda side instead, via Mangum's `api_gateway_base_path="/api"`
  # (see backend/app/main.py).
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "https-only"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_disabled.id
    # Managed-AllViewer (not used here) forwards the viewer's own Host
    # header verbatim, which API Gateway's execute-api endpoint rejects
    # with a generic 403 Forbidden (Host doesn't match its own domain) —
    # a real, previously-hit bug. This policy forwards everything else but
    # lets CloudFront set Host to the origin's own domain instead.
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id
  }

  # Audio object keys are stored in S3 *with* the "audio/" prefix (see
  # pronunciation.py's _s3_key) specifically so this behavior can forward
  # requests to S3 completely unrewritten — same lesson as the /api/*
  # comment above, applied by matching the object's location to the
  # requested path instead of rewriting the path. caching_optimized (not
  # caching_disabled like /api/*) since these objects are immutable once
  # written (content-hash filenames) — this is what actually delivers
  # edge caching instead of a repeated S3 GetObject per play.
  ordered_cache_behavior {
    path_pattern           = "/audio/*"
    target_origin_id       = "s3-audio"
    viewer_protocol_policy = "https-only"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_optimized.id
  }

  # SPA fallback — this app doesn't use client-side URL routing today (tab
  # state in App.jsx), but this is harmless and future-proofs against
  # adding one later. Real 404s from the frontend build itself won't occur
  # since it's a single index.html + hashed assets.
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontServicePrincipal"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
        }
      }
    }]
  })
}
