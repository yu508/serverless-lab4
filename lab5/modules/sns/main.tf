variable "topic_name" {
  type = string
}

variable "subscriber_email" {
  type = string
}

resource "aws_sns_topic" "main" {
  name = var.topic_name
}

resource "aws_sns_topic_subscription" "email_sub" {
  topic_arn = aws_sns_topic.main.arn
  protocol  = "email"
  endpoint  = var.subscriber_email
}

output "topic_arn" {
  value = aws_sns_topic.main.arn
}