terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "serverless-pipeline"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

#  Kinesis Data Stream 
module "kinesis" {
  source      = "./modules/kinesis"
  stream_name = "${var.project_name}-stream"
  shard_count = 1
  environment = var.environment
}

module "dynamodb" {
  source      = "./modules/dynamodb"
  table_name  = "${var.project_name}-records"
  environment = var.environment
}


module "iam" {
  source       = "./modules/iam"
  project_name = var.project_name
  environment  = var.environment
  kinesis_arn  = module.kinesis.stream_arn
  dynamodb_arn = module.dynamodb.table_arn
}


module "lambda" {
  source             = "./modules/lambda"
  function_name      = "${var.project_name}-processor"
  lambda_role_arn    = module.iam.lambda_role_arn
  kinesis_stream_arn = module.kinesis.stream_arn
  dynamodb_table     = module.dynamodb.table_name
  environment        = var.environment
}
