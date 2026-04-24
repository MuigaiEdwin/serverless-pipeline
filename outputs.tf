output "kinesis_stream_name" {
  description = "Name of the Kinesis Data Stream"
  value       = module.kinesis.stream_name
}

output "kinesis_stream_arn" {
  description = "ARN of the Kinesis Data Stream"
  value       = module.kinesis.stream_arn
}

output "lambda_function_name" {
  description = "Name of the Lambda processor function"
  value       = module.lambda.function_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = module.dynamodb.table_name
}

output "lambda_log_group" {
  description = "CloudWatch log group for Lambda"
  value       = "/aws/lambda/${module.lambda.function_name}"
}
