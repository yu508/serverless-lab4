output "api_url" {
  value = module.api.api_endpoint
}

output "sns_topic_arn" {
  value = module.notifications.topic_arn
}

output "dynamodb_table_name" {
  value = module.database.table_name
}