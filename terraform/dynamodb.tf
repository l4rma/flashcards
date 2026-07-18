# Four tables, one per concern (not single-table design — this app's
# access patterns and scale don't warrant that complexity; see
# CLAUDE.md/SPEC.md for the reasoning). All On-Demand billing — no
# capacity planning needed at this traffic level.

resource "aws_dynamodb_table" "cards" {
  name         = "${var.project_name}-Cards"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "due_date"
    type = "S"
  }

  # Serves GET /cards/due directly (base table's sort key is `id`, not
  # `due_date`, so due-card lookups need this index).
  global_secondary_index {
    name            = "due-index"
    hash_key        = "user_id"
    range_key       = "due_date"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "stats" {
  name         = "${var.project_name}-Stats"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "achievements" {
  name         = "${var.project_name}-Achievements"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "achievement_key"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "achievement_key"
    type = "S"
  }
}

resource "aws_dynamodb_table" "quest_completions" {
  name         = "${var.project_name}-QuestCompletions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "sort_key"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "sort_key"
    type = "S"
  }
}
