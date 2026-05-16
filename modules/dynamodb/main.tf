resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST" # on-demand — no provisioned WCU charges during dev

  hash_key  = "record_id"
  range_key = "ingested_at"

  attribute {
    name = "record_id"
    type = "S"
  }

  attribute {
    name = "ingested_at"
    type = "S"
  }

  # Point-in-time recovery — good practice, no extra cost
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = var.table_name
  }
}
