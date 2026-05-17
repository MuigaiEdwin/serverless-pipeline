locals {
  lambda_src_path = "${path.root}/lambda_src"
  zip_output_path = "${path.root}/lambda_src/handler.zip"
}


data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = local.lambda_src_path
  output_path = local.zip_output_path
  excludes    = ["handler.zip", "__pycache__", "*.pyc"]
}

resource "aws_lambda_function" "processor" {
  function_name    = var.function_name
  role             = var.lambda_role_arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 30
  memory_size      = 128 # minimum — keeps costs at zero under free tier

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table
      ENVIRONMENT    = var.environment
      LOG_LEVEL      = "INFO"
    }
  }

  tags = {
    Name = var.function_name
  }
}


resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 7 # keep logs for 7 days — within free tier 5GB/month
}


resource "aws_lambda_event_source_mapping" "kinesis_trigger" {
  event_source_arn               = var.kinesis_stream_arn
  function_name                  = aws_lambda_function.processor.arn
  starting_position              = "LATEST"
  batch_size                     = 100
  bisect_batch_on_function_error = true

  depends_on = [aws_lambda_function.processor]
}
