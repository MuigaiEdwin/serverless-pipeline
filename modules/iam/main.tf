
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "${var.project_name}-lambda-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}


data "aws_iam_policy_document" "kinesis_read" {
  statement {
    sid    = "KinesisRead"
    effect = "Allow"

    actions = [
      "kinesis:GetRecords",
      "kinesis:GetShardIterator",
      "kinesis:DescribeStream",
      "kinesis:DescribeStreamSummary",
      "kinesis:ListShards",
      "kinesis:ListStreams",
    ]

    resources = [var.kinesis_arn]
  }
}

resource "aws_iam_policy" "kinesis_read" {
  name   = "${var.project_name}-kinesis-read-${var.environment}"
  policy = data.aws_iam_policy_document.kinesis_read.json
}

resource "aws_iam_role_policy_attachment" "kinesis_read" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.kinesis_read.arn
}


data "aws_iam_policy_document" "dynamodb_write" {
  statement {
    sid     = "DynamoDBWrite"
    effect  = "Allow"
    actions = ["dynamodb:PutItem"]

    resources = [var.dynamodb_arn]
  }
}

resource "aws_iam_policy" "dynamodb_write" {
  name   = "${var.project_name}-dynamodb-write-${var.environment}"
  policy = data.aws_iam_policy_document.dynamodb_write.json
}

resource "aws_iam_role_policy_attachment" "dynamodb_write" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_write.arn
}


resource "aws_iam_role_policy_attachment" "lambda_basic_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
