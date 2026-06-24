# Root Terragrunt configuration.
#
# Every unit under units/ includes this file, so the AWS provider is declared
# once here and shared everywhere (the DRY win Terragrunt is built for). The
# provider points at LocalStack so the whole stack applies offline, with no real
# AWS account and no cost.

locals {
  region   = "us-east-1"
  endpoint = "http://localhost:4566"

  common_tags = {
    Project = "opensource.assinnata.com"
    Managed = "terragrunt"
    Env     = "localstack"
  }
}

# Generate the AWS provider into every unit. The endpoints block sends every
# call to LocalStack; the skip_* flags stop the provider reaching out to the
# real AWS metadata and STS endpoints.
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region                      = "${local.region}"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    ec2                      = "${local.endpoint}"
    sts                      = "${local.endpoint}"
    s3                       = "${local.endpoint}"
    iam                      = "${local.endpoint}"
    ram                      = "${local.endpoint}"
    resourcegroupstaggingapi = "${local.endpoint}"
  }
}
EOF
}

# Shared inputs. Terragrunt passes these as TF_VAR_* env vars, so a unit whose
# module does not declare one simply ignores it.
inputs = {
  tags = local.common_tags
}
