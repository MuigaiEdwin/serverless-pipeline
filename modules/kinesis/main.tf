resource "aws_kinesis_stream" "this" {
  name             = var.stream_name
  shard_count      = var.shard_count
  retention_period = 24 # hours — free tier max

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = {
    Name = var.stream_name
  }
}
