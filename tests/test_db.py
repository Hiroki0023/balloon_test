import datetime
import math

import pytest

import db
from db import DataStoreError, DietStore, InvalidInputError
from fakes import FakeClient

FIXED = datetime.datetime(2026, 9, 26, 1, 2, 3, tzinfo=datetime.timezone.utc)


@pytest.fixture
def client():
    return FakeClient()


@pytest.fixture
def store(client):
    return DietStore(client, clock=lambda: FIXED)


def upserts(client):
    return [call for call in client.calls if call[0] == "upsert"]


# U-01
def test_u01_same_date_twice_keeps_one_row_with_latest_value(store, client):
    store.upsert_log("2026-09-25", 66.0)
    store.upsert_log("2026-09-25", 65.4)
    logs = [r for r in client.rows.values() if r["type"] == "log"]
    assert len(logs) == 1
    assert logs[0]["value"] == "65.4"
    assert all(call[2] == "type,key" for call in upserts(client))
    assert client.tables == ["diet_data", "diet_data"]


# U-02
@pytest.mark.parametrize("bad", [19.9, 200.1, float("nan"), math.inf, -math.inf, "abc", None, ""])
def test_u02_invalid_weight_is_rejected_without_sending(store, client, bad):
    with pytest.raises(InvalidInputError):
        store.upsert_log("2026-09-25", bad)
    assert client.calls == []


# U-03
@pytest.mark.parametrize(
    "given, expected",
    [(66.30000000000001, "66.3"), (66, "66.0"), (20.0, "20.0"), (200.0, "200.0"), (65.25, "65.2"), ("66.5", "66.5")],
)
def test_u03_weight_is_rounded_to_one_decimal(store, client, given, expected):
    store.upsert_log("2026-09-25", given)
    assert upserts(client)[0][1][0]["value"] == expected


# U-04
@pytest.mark.parametrize("bad", ["2026-02-30", "2026/09/25", "", "20260925", "2026-9-5", None, 20260925])
def test_u04_invalid_date_is_rejected(store, client, bad):
    with pytest.raises(InvalidInputError):
        store.upsert_log(bad, 66.0)
    assert client.calls == []


def test_u04_valid_date_is_accepted(store, client):
    store.upsert_log("2026-09-25", 66.0)
    record = upserts(client)[0][1][0]
    assert (record["type"], record["key"], record["value"]) == ("log", "2026-09-25", "66.0")
    assert record["updated_at"] == FIXED.isoformat()


# U-05
def test_u05_four_settings_are_sent_in_one_request(store, client):
    store.upsert_settings(
        {"start_weight": 70.0, "goal": 60.0, "deadline": "2026-12-01", "start_date": "2026-09-26"}
    )
    assert len(upserts(client)) == 1
    payload = upserts(client)[0][1]
    assert {r["key"]: r["value"] for r in payload} == {
        "start_weight": "70.0",
        "goal": "60.0",
        "deadline": "2026-12-01",
        "start_date": "2026-09-26",
    }
    assert all(r["type"] == "setting" for r in payload)


def test_u05_unknown_setting_key_is_rejected_and_nothing_is_sent(store, client):
    with pytest.raises(InvalidInputError):
        store.upsert_settings({"goal": 60.0, "hacker": "x"})
    assert client.calls == []


def test_u05_empty_settings_is_a_noop(store, client):
    store.upsert_settings({})
    assert client.calls == []


# U-06
@pytest.mark.parametrize(
    "items",
    [
        {"start_weight": 19.0},
        {"goal": 201},
        {"goal": "abc"},
        {"deadline": "2026-13-01"},
        {"start_date": "2026/09/26"},
        {"deadline": 20261201},
    ],
)
def test_u06_invalid_setting_values_are_rejected(store, client, items):
    with pytest.raises(InvalidInputError):
        store.upsert_settings(items)
    assert client.calls == []


# U-07
@pytest.mark.parametrize("count, pages", [(0, 1), (999, 1), (1000, 2), (1001, 2), (2500, 3)])
def test_u07_fetch_all_returns_every_row(client, count, pages):
    for i in range(count):
        day = datetime.date(2020, 1, 1) + datetime.timedelta(days=i)
        client.seed("log", day.isoformat(), "60.0")
    rows = DietStore(client).fetch_all()
    assert len(rows) == count
    assert len({(r["type"], r["key"]) for r in rows}) == count
    assert client.count("select") == pages


def test_u07_pages_use_contiguous_ranges(client):
    for i in range(2500):
        client.seed("log", (datetime.date(2020, 1, 1) + datetime.timedelta(days=i)).isoformat(), "60.0")
    DietStore(client).fetch_all()
    assert [call[1] for call in client.calls] == [(0, 999), (1000, 1999), (2000, 2999)]


# U-08 / U-09
def test_u08_settings_from_rows_ignores_logs_and_handles_empty():
    rows = [
        {"type": "setting", "key": "goal", "value": "60.0"},
        {"type": "log", "key": "2026-09-25", "value": "66.0"},
    ]
    assert db.settings_from_rows(rows) == {"goal": "60.0"}
    assert db.settings_from_rows([]) == {}


def test_u09_log_from_rows_sorts_by_date_and_returns_floats():
    rows = [
        {"type": "log", "key": "2026-09-26", "value": "65.5"},
        {"type": "setting", "key": "goal", "value": "60.0"},
        {"type": "log", "key": "2026-09-24", "value": "66.0"},
    ]
    out = db.log_from_rows(rows)
    assert list(out.columns) == ["date", "weight"]
    assert out["date"].tolist() == ["2026-09-24", "2026-09-26"]
    assert out["weight"].tolist() == [66.0, 65.5]
    assert out["weight"].dtype == float


def test_u09_log_from_rows_empty_keeps_columns():
    out = db.log_from_rows([{"type": "setting", "key": "goal", "value": "60.0"}])
    assert out.empty
    assert list(out.columns) == ["date", "weight"]


# U-10
def test_u10_read_failure_becomes_datastore_error_without_secrets(client):
    client.fail_reads = True
    with pytest.raises(DataStoreError) as info:
        DietStore(client).fetch_all()
    message = str(info.value)
    assert message == db.MSG_READ_FAILED
    assert "supabase.co" not in message and "SECRET-KEY" not in message
    assert info.value.__cause__ is None


def test_u10_write_failure_becomes_datastore_error_without_secrets(store, client):
    client.fail_writes = True
    with pytest.raises(DataStoreError) as info:
        store.upsert_log("2026-09-25", 66.0)
    assert str(info.value) == db.MSG_WRITE_FAILED
    assert "SECRET-KEY" not in str(info.value)


def test_u10_make_client_failure_does_not_leak_the_key(monkeypatch):
    def boom(url, key):
        raise ValueError(f"bad {url} {key}")

    import sys, types

    fake_module = types.SimpleNamespace(create_client=boom)
    monkeypatch.setitem(sys.modules, "supabase", fake_module)
    with pytest.raises(DataStoreError) as info:
        db.make_client("https://x.supabase.co", "SECRET-KEY-123")
    assert "SECRET-KEY" not in str(info.value) and "supabase.co" not in str(info.value)


# U-11
def test_u11_delete_all_issues_one_delete_on_the_table(store, client):
    client.seed("log", "2026-09-25", "66.0")
    client.seed("setting", "goal", "60.0")
    store.delete_all()
    assert client.count("delete") == 1
    assert client.rows == {}
    assert set(client.tables) == {"diet_data"}


# U-15
def test_u15_missing_secrets_are_reported_by_name_only():
    class Secrets(dict):
        pass

    assert db.missing_secrets(Secrets()) == ["SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
    assert db.missing_secrets(Secrets(SUPABASE_URL="https://x", SUPABASE_SERVICE_KEY="k")) == []
    assert db.missing_secrets(Secrets(SUPABASE_URL="https://x", SUPABASE_SERVICE_KEY="  ")) == ["SUPABASE_SERVICE_KEY"]
    assert db.missing_secrets(Secrets(SUPABASE_URL=123, SUPABASE_SERVICE_KEY="k")) == ["SUPABASE_URL"]
    reported = db.missing_secrets(Secrets(SUPABASE_URL="https://secret-host", SUPABASE_SERVICE_KEY=""))
    assert "secret-host" not in " ".join(reported)


def test_u15_missing_secrets_survives_a_secrets_object_that_raises():
    class Broken:
        def get(self, name):
            raise FileNotFoundError("no secrets file")

    assert db.missing_secrets(Broken()) == ["SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
