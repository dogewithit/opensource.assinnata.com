"""Assert the Terragrunt stack really stood up on LocalStack.

The `stack` fixture applies every unit once; these tests then query LocalStack
directly with boto3 to prove each piece exists and is wired together.
"""

from __future__ import annotations

import pytest

VPC_NAME = "oss-vpc"
PRIVATE_CIDRS = {"10.0.1.0/24", "10.0.2.0/24"}
PUBLIC_CIDRS = {"10.0.101.0/24", "10.0.102.0/24"}
NODE_NAMES = {"oss-trading-node", "oss-marketdata-node"}


def _vpc_id(ec2) -> str:
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "tag:Name", "Values": [VPC_NAME]}])["Vpcs"]
    assert vpcs, "VPC oss-vpc not found"
    return vpcs[0]["VpcId"]


def _subnets(ec2):
    vid = _vpc_id(ec2)
    return ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vid]}])["Subnets"]


def _instances(ec2):
    res = ec2.describe_instances(
        Filters=[{"Name": "tag:Name", "Values": list(NODE_NAMES)}]
    )["Reservations"]
    return [i for r in res for i in r["Instances"] if i["State"]["Name"] == "running"]


def test_vpc_created(ec2):
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "tag:Name", "Values": [VPC_NAME]}])["Vpcs"]
    assert len(vpcs) == 1
    assert vpcs[0]["CidrBlock"] == "10.0.0.0/16"


def test_private_and_public_subnets(ec2):
    cidrs = {s["CidrBlock"] for s in _subnets(ec2)}
    assert PRIVATE_CIDRS <= cidrs, f"missing private subnets in {cidrs}"
    assert PUBLIC_CIDRS <= cidrs, f"missing public subnets in {cidrs}"


def test_security_group_exists(ec2):
    sgs = [
        g
        for g in ec2.describe_security_groups()["SecurityGroups"]
        if g["GroupName"].startswith("oss-app-sg")
    ]
    assert len(sgs) == 1, "expected exactly one oss-app-sg"


def test_security_group_rules(ec2):
    sg = next(
        g
        for g in ec2.describe_security_groups()["SecurityGroups"]
        if g["GroupName"].startswith("oss-app-sg")
    )
    # both declared ingress rules are present: https (443) and all-icmp
    ports = {p.get("FromPort") for p in sg["IpPermissions"]}
    protocols = {p.get("IpProtocol") for p in sg["IpPermissions"]}
    assert 443 in ports, f"https ingress missing, ports={ports}"
    assert "icmp" in protocols, f"icmp ingress missing, protocols={protocols}"
    assert len(sg["IpPermissions"]) >= 2, "expected at least two ingress rules"
    # egress allows all
    assert sg["IpPermissionsEgress"], "no egress rule"


def test_transit_gateway_available(ec2):
    tgws = [
        t
        for t in ec2.describe_transit_gateways()["TransitGateways"]
        if t["State"] != "deleted"
    ]
    assert tgws, "no transit gateway"
    assert any(t["State"] == "available" for t in tgws)


def test_tgw_attached_to_vpc(ec2):
    vid = _vpc_id(ec2)
    atts = [
        a
        for a in ec2.describe_transit_gateway_vpc_attachments()[
            "TransitGatewayVpcAttachments"
        ]
        if a.get("VpcId") == vid and a["State"] != "deleted"
    ]
    assert atts, "VPC is not attached to a transit gateway"
    assert atts[0]["State"] == "available"


def test_two_nodes_running(ec2):
    nodes = _instances(ec2)
    names = {
        t["Value"]
        for i in nodes
        for t in i.get("Tags", [])
        if t["Key"] == "Name"
    }
    assert names == NODE_NAMES, f"expected {NODE_NAMES}, got {names}"
    assert all(i["InstanceType"] == "t3.micro" for i in nodes)


def test_nodes_run_in_private_subnets(ec2):
    private_ids = {
        s["SubnetId"] for s in _subnets(ec2) if s["CidrBlock"] in PRIVATE_CIDRS
    }
    for i in _instances(ec2):
        assert i["SubnetId"] in private_ids, "a node is not in a private subnet"
