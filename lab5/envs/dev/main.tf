provider "aws" {
  region = "eu-central-1"
}

locals {
  prefix = "rybchak-yuliia-16"
}

module "database" {
  source     = "../../modules/dynamodb"
  table_name = "${local.prefix}-orders"
}

module "notifications" {
  source           = "../../modules/sns"
  topic_name       = "${local.prefix}-topic"
  subscriber_email = "yuliia.rybchak.oi.2022@lpnu.ua"
}

module "logs_bucket" {
  source      = "../../modules/s3_logs"
  bucket_name = "rybchak-yuliia-lab5-16-logs"
}

module "backend" {
  source              = "../../modules/lambda"
  function_name       = "${local.prefix}-api-handler"
  source_file         = "${path.root}/../../src/app.py"
  dynamodb_table_arn  = module.database.table_arn
  dynamodb_table_name = module.database.table_name
  sns_topic_arn       = module.notifications.topic_arn
  log_bucket_name     = module.logs_bucket.bucket_name
  log_bucket_arn      = module.logs_bucket.bucket_arn
}

module "api" {
  source               = "../../modules/api_gateway"
  api_name             = "${local.prefix}-http-api"
  lambda_invoke_arn    = module.backend.invoke_arn
  lambda_function_name = module.backend.function_name
}