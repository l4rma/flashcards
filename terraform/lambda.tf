data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${var.project_name}-lambda-exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Least-privilege: exactly the 4 table ARNs (+ the Cards table's GSI,
# which needs its own ARN for Query) and exactly the operations the app
# actually calls (see cards.py/stats.py/achievements.py/quests.py) — no
# wildcard table access.
data "aws_iam_policy_document" "lambda_dynamodb" {
  statement {
    sid = "TableAccess"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:TransactWriteItems",
    ]
    resources = [
      aws_dynamodb_table.cards.arn,
      "${aws_dynamodb_table.cards.arn}/index/*",
      aws_dynamodb_table.stats.arn,
      aws_dynamodb_table.achievements.arn,
      aws_dynamodb_table.quest_completions.arn,
    ]
  }
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name   = "${var.project_name}-lambda-dynamodb"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_dynamodb.json
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}-api"
  retention_in_days = 14
}

# The zip is built by backend/build_lambda.sh (pip-installs
# requirements-lambda.txt for the Lambda Python/manylinux target, then
# copies app/ in) — not by Terraform itself. Run that script before
# `terraform apply`; see TASKS.md Phase 7 / README.md.
resource "aws_lambda_function" "api" {
  function_name    = "${var.project_name}-api"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "app.main.handler"
  runtime          = "python3.13"
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  filename         = "${path.module}/../backend/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../backend/lambda.zip")

  environment {
    variables = {
      CARDS_TABLE             = aws_dynamodb_table.cards.name
      STATS_TABLE              = aws_dynamodb_table.stats.name
      ACHIEVEMENTS_TABLE       = aws_dynamodb_table.achievements.name
      QUEST_COMPLETIONS_TABLE  = aws_dynamodb_table.quest_completions.name
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}
