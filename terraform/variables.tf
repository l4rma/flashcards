variable "aws_region" {
  description = "AWS region to deploy into. Defaults to Stockholm — closest region to the user."
  type        = string
  default     = "eu-north-1"
}

variable "project_name" {
  description = "Short name used as a prefix for resource names."
  type        = string
  default     = "flash-cards"
}

variable "cognito_self_signup_enabled" {
  description = "Whether new users can self-register via the Cognito Hosted UI. Set to false to require admin-created users only (aws cognito-idp admin-create-user)."
  type        = bool
  default     = true
}

variable "lambda_memory_size" {
  description = "Lambda function memory, in MB."
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Lambda function timeout, in seconds."
  type        = number
  default     = 15
}

variable "frontend_urls" {
  description = "Extra Cognito callback/logout URLs beyond the CloudFront URL (which is always included automatically) — e.g. [\"http://localhost:5173/\"] to test a local frontend dev server against the deployed Cognito pool."
  type        = list(string)
  default     = []
}
