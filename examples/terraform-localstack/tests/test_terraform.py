"""Assert that `terraform apply` actually created the resources in LocalStack."""

import os

import boto3


def _client(service: str):
    return boto3.client(
        service,
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )


def test_s3_bucket_created(applied_stack):
    buckets = {b["Name"] for b in _client("s3").list_buckets()["Buckets"]}
    assert "tf-market-artifacts" in buckets


def test_dynamodb_table_created(applied_stack):
    tables = _client("dynamodb").list_tables()["TableNames"]
    assert "tf-markets" in tables


def test_dynamodb_key_schema(applied_stack):
    desc = _client("dynamodb").describe_table(TableName="tf-markets")["Table"]
    keys = {k["AttributeName"]: k["KeyType"] for k in desc["KeySchema"]}
    assert keys == {"market_id": "HASH"}
