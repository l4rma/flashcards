output "cloudfront_domain" {
  description = "The app's public URL (frontend + /api/* proxied to the backend)."
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "api_gateway_invoke_url" {
  description = "Direct API Gateway invoke URL (bypasses CloudFront/the /api prefix stripping — mostly useful for debugging)."
  value       = aws_apigatewayv2_api.this.api_endpoint
}

output "cognito_domain" {
  description = "Cognito Hosted UI domain."
  value       = "https://${aws_cognito_user_pool_domain.this.domain}.auth.${var.aws_region}.amazoncognito.com"
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.this.id
}

output "cognito_app_client_id" {
  value = aws_cognito_user_pool_client.spa.id
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  description = "Needed for cache invalidation after deploying new frontend assets (aws cloudfront create-invalidation)."
  value       = aws_cloudfront_distribution.frontend.id
}
