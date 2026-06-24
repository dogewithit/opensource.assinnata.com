# Transit gateway with the VPC attached, the hub other VPCs or accounts would
# peer into. Reuses the registry transit-gateway module.

include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "tfr:///terraform-aws-modules/transit-gateway/aws//.?version=2.13.1"
}

dependency "vpc" {
  config_path = "../vpc"

  mock_outputs = {
    vpc_id          = "vpc-mock"
    private_subnets = ["subnet-mock-a", "subnet-mock-b"]
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  name        = "oss-tgw"
  description = "Transit gateway for the trading VPC"

  # RAM cross account sharing is a LocalStack Pro feature, so keep it off and let
  # the module create only the gateway, its route table and the attachment.
  share_tgw                             = false
  enable_auto_accept_shared_attachments = true

  vpc_attachments = {
    trading = {
      vpc_id     = dependency.vpc.outputs.vpc_id
      subnet_ids = dependency.vpc.outputs.private_subnets
    }
  }
}
