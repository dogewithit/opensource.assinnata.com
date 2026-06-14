terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# tflocal injects the LocalStack endpoints via an auto-generated override file.
# The skip_* flags keep the AWS provider from calling real AWS metadata/STS.
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true
}

resource "aws_s3_bucket" "artifacts" {
  bucket = "tf-market-artifacts"
}

resource "aws_dynamodb_table" "markets" {
  name         = "tf-markets"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "market_id"

  attribute {
    name = "market_id"
    type = "S"
  }
}

output "bucket_name" {
  value = aws_s3_bucket.artifacts.bucket
}

output "table_name" {
  value = aws_dynamodb_table.markets.name
}
