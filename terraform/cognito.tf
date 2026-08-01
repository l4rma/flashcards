resource "aws_cognito_user_pool" "this" {
  name = "${var.project_name}-users"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = !var.cognito_self_signup_enabled
  }
}

# Domain prefix must be globally unique across all AWS accounts (shared
# amazoncognito.com namespace) — account id makes this collision-safe
# without needing a custom domain/ACM cert.
resource "aws_cognito_user_pool_domain" "this" {
  domain       = "${var.project_name}-${data.aws_caller_identity.current.account_id}"
  user_pool_id = aws_cognito_user_pool.this.id
}

# Public SPA client — PKCE Authorization Code flow, no client secret.
resource "aws_cognito_user_pool_client" "spa" {
  name         = "${var.project_name}-spa"
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret = false

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  # aws.cognito.signin.user.admin lets the access token call Cognito's
  # Identity Provider API directly (ChangePassword, UpdateUserAttributes,
  # etc.) from the frontend with no backend involvement — see Settings'
  # change-password action, which calls ChangePassword straight from
  # auth.js the same way it already talks to the OAuth endpoints.
  allowed_oauth_scopes         = ["openid", "email", "profile", "aws.cognito.signin.user.admin"]
  supported_identity_providers = ["COGNITO"]

  callback_urls = concat(
    ["https://${aws_cloudfront_distribution.frontend.domain_name}/"],
    var.frontend_urls,
  )
  logout_urls = concat(
    ["https://${aws_cloudfront_distribution.frontend.domain_name}/"],
    var.frontend_urls,
  )

  explicit_auth_flows = ["ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_USER_SRP_AUTH"]

  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 30
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}
