# Terraform against LocalStack (tflocal)

Provisions an S3 bucket and a DynamoDB table with **Terraform**, applied against
LocalStack via `tflocal`, then asserts the resources really exist with boto3.

> **Terraform** tool example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- Real `terraform apply` against LocalStack — not a mock, not a dry plan.
- `tflocal` endpoint injection + path-style S3 (`S3_HOSTNAME=localhost` to stay
  offline-friendly).
- A test that applies in an isolated temp dir, verifies state via boto3, and
  always `destroy`s afterwards.

## Run the tests

```bash
make up                      # LocalStack 4.14
make test-terraform-localstack
```

First run downloads the AWS provider (~tens of MB), so expect ~1 min.

## Reference

Source: [`examples/terraform-localstack`](https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/terraform-localstack)
· tflocal: <https://docs.localstack.cloud/user-guide/integrations/terraform/>
