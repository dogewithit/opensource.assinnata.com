# A thin wrapper that turns a map of nodes into EC2 instances, each built from
# the registry ec2-instance module. This is the "collect a module and reuse it"
# pattern: one well known module, instantiated once per node via for_each.

module "instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "5.8.0"

  for_each = var.nodes

  name                   = each.key
  ami                    = var.ami
  instance_type          = var.instance_type
  subnet_id              = each.value.subnet_id
  vpc_security_group_ids = var.security_group_ids

  tags = merge(var.tags, { Role = each.key })
}
