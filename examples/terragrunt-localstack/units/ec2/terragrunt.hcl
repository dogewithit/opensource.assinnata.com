# The compute that would run the software engineering examples: one node for the
# trading services, one for the market data platform. Sources a small local
# wrapper module (modules/nodes) that fans the registry ec2-instance module out
# across both nodes, and depends on the VPC and the security group.

include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "${get_terragrunt_dir()}/../../modules/nodes"
}

dependency "vpc" {
  config_path = "../vpc"

  mock_outputs = {
    private_subnets = ["subnet-mock-a", "subnet-mock-b"]
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "sg" {
  config_path = "../security-group"

  mock_outputs = {
    security_group_id = "sg-mock"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  # LocalStack mocks the instance, so any well formed AMI id is accepted.
  ami                = "ami-12345678"
  instance_type      = "t3.micro"
  security_group_ids = [dependency.sg.outputs.security_group_id]

  nodes = {
    "oss-trading-node"    = { subnet_id = dependency.vpc.outputs.private_subnets[0] }
    "oss-marketdata-node" = { subnet_id = dependency.vpc.outputs.private_subnets[1] }
  }
}
