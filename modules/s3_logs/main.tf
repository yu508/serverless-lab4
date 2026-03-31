variable "bucket_name" {
  type = string
}

resource "aws_s3_bucket" "logs" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_versioning" "logs_versioning" {
  bucket = aws_s3_bucket.logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

output "bucket_name" {
  value = aws_s3_bucket.logs.bucket
}

output "bucket_arn" {

  value = aws_s3_bucket.logs.arn
}