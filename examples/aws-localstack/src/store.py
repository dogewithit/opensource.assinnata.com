"""A market-artifact store: raw market JSON in S3, a metadata index in DynamoDB.

Every boto3 client honours AWS_ENDPOINT_URL, so the same code runs against
LocalStack locally and real AWS in production — nothing test-only here.
"""

from __future__ import annotations

import json
import os

import boto3


def _client(service: str):
    return boto3.client(
        service,
        endpoint_url=os.environ.get("AWS_ENDPOINT_URL"),  # None => real AWS
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )


class MarketArtifactStore:
    def __init__(self, bucket: str, table: str, s3=None, ddb=None) -> None:
        self.bucket = bucket
        self.table = table
        self.s3 = s3 or _client("s3")
        self.ddb = ddb or _client("dynamodb")

    def ensure_infra(self) -> None:
        """Create the bucket and table if they don't already exist (idempotent)."""
        existing_buckets = {
            b["Name"] for b in self.s3.list_buckets().get("Buckets", [])
        }
        if self.bucket not in existing_buckets:
            self.s3.create_bucket(Bucket=self.bucket)

        existing_tables = self.ddb.list_tables().get("TableNames", [])
        if self.table not in existing_tables:
            self.ddb.create_table(
                TableName=self.table,
                KeySchema=[{"AttributeName": "market_id", "KeyType": "HASH"}],
                AttributeDefinitions=[
                    {"AttributeName": "market_id", "AttributeType": "S"}
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            self.ddb.get_waiter("table_exists").wait(TableName=self.table)

    def put(self, market_id: str, payload: dict) -> str:
        """Store the payload JSON in S3 and index it in DynamoDB. Returns the key."""
        key = f"markets/{market_id}.json"
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=body)
        self.ddb.put_item(
            TableName=self.table,
            Item={
                "market_id": {"S": market_id},
                "s3_key": {"S": key},
                "size_bytes": {"N": str(len(body))},
            },
        )
        return key

    def get(self, market_id: str) -> dict | None:
        """Resolve the artifact via the DynamoDB index, then read it from S3."""
        item = self.ddb.get_item(
            TableName=self.table, Key={"market_id": {"S": market_id}}
        ).get("Item")
        if not item:
            return None
        key = item["s3_key"]["S"]
        obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        return json.loads(obj["Body"].read())

    def list_ids(self) -> list[str]:
        items = self.ddb.scan(TableName=self.table).get("Items", [])
        return sorted(i["market_id"]["S"] for i in items)
