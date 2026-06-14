# AWS market-artifact store (S3 + DynamoDB)

Stores raw market JSON in **S3** and indexes it in **DynamoDB** — the same boto3
code runs against LocalStack locally and real AWS in production (it just reads
`AWS_ENDPOINT_URL`).

> **AWS** tool example for [opensource.assinnata.com](https://opensource.assinnata.com).

## What it demonstrates

- Endpoint-agnostic boto3 (`AWS_ENDPOINT_URL` → LocalStack or AWS, no test-only branches).
- Idempotent infra bootstrap (`create_bucket` / `create_table` only if absent).
- A blob-store + metadata-index pattern: large payloads in S3, queryable keys in DynamoDB.

## Run the tests

```bash
make up                  # LocalStack 4.14
make test-aws-localstack
```

## Reference

Source: [`examples/aws-localstack`](https://github.com/dogewithit/opensource.assinnata.com/tree/main/examples/aws-localstack)
· boto3: <https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>
· LocalStack: <https://docs.localstack.cloud>
