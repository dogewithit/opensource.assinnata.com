"""S3 + DynamoDB round-trip tests against LocalStack."""


def test_put_get_roundtrip(store):
    payload = {"question": "BTC > $100k?", "yes": "0.62", "no": "0.38"}
    key = store.put("BTC-100K-2026", payload)

    assert key == "markets/BTC-100K-2026.json"
    assert store.get("BTC-100K-2026") == payload


def test_get_missing_returns_none(store):
    assert store.get("does-not-exist") is None


def test_list_ids(store):
    store.put("AAA", {"v": 1})
    store.put("BBB", {"v": 2})
    assert store.list_ids() == ["AAA", "BBB"]


def test_overwrite_updates_payload(store):
    store.put("AAA", {"v": 1})
    store.put("AAA", {"v": 2})
    assert store.get("AAA") == {"v": 2}
    assert store.list_ids() == ["AAA"]  # not duplicated


def test_ensure_infra_is_idempotent(store):
    # calling again must not raise even though bucket/table already exist
    store.ensure_infra()
    store.ensure_infra()
