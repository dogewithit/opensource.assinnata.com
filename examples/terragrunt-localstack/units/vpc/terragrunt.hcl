# Network foundation: a two AZ VPC with public and private subnets.
# Reuses the most widely used VPC module on the Terraform registry.

include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "tfr:///terraform-aws-modules/vpc/aws//.?version=5.21.0"
}

inputs = {
  name = "oss-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  # No NAT gateway: it is not needed for the test stack and NAT is not part of
  # LocalStack's community emulation.
  enable_nat_gateway   = false
  enable_dns_hostnames = true
}
