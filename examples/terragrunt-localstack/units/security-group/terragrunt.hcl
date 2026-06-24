# Application tier security group for the trading nodes.
# Reuses the registry security-group module and depends on the VPC unit.

include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "tfr:///terraform-aws-modules/security-group/aws//.?version=5.3.1"
}

dependency "vpc" {
  config_path = "../vpc"

  # Mock values let `validate` and `plan` run before the VPC is applied.
  mock_outputs = {
    vpc_id = "vpc-mock"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  name        = "oss-app-sg"
  description = "App tier for the trading and market data nodes"
  vpc_id      = dependency.vpc.outputs.vpc_id

  ingress_cidr_blocks = ["10.0.0.0/16"]
  # https for the services, plus icmp so nodes can be reached inside the VPC.
  ingress_rules = ["https-443-tcp", "all-icmp"]
  egress_rules  = ["all-all"]
}
