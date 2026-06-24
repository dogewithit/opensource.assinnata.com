# Terragrunt on LocalStack

A small but real network stack built with **Terragrunt**, wiring together the
most widely used registry modules and applied entirely against LocalStack, so it
runs offline with no AWS account and no cost.

> **Terragrunt** tool example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- One AWS provider, declared once in `root.hcl` and shared by every unit (the
  DRY win Terragrunt exists for), generated to point at LocalStack.
- Four units composed through `dependency` blocks, applied in order by
  `terragrunt run --all`:
  - **vpc** reuses `terraform-aws-modules/vpc` (two AZs, public and private subnets).
  - **security-group** reuses `terraform-aws-modules/security-group`.
  - **transit-gateway** reuses `terraform-aws-modules/transit-gateway` and attaches the VPC.
  - **ec2** sources a local `modules/nodes` wrapper that fans
    `terraform-aws-modules/ec2-instance` across a trading node and a market data
    node, the compute that would run the software engineering examples.
- Tests that apply the whole stack and then query LocalStack with boto3 to prove
  the VPC, subnets, security group, transit gateway, attachment and both
  instances are really there.

## Layout

```
root.hcl                     # shared provider + tags, wired to LocalStack
units/
  vpc/                       # terraform-aws-modules/vpc
  security-group/            # terraform-aws-modules/security-group
  transit-gateway/           # terraform-aws-modules/transit-gateway
  ec2/                       # local modules/nodes wrapper
modules/nodes/               # reuses terraform-aws-modules/ec2-instance per node
```

## Run the tests

```bash
make up                      # LocalStack 4.14 with ec2 enabled
make test-terragrunt-localstack
```

Needs `terragrunt` and `terraform` on the PATH. Cross account sharing of the
transit gateway (AWS RAM) is a LocalStack Pro feature, so it is left off.

## Reference

Source: [`examples/terragrunt-localstack`](https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/terragrunt-localstack)
