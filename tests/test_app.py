"""結合テスト I-01〜I-09, I-15 と JST（AppTest＋偽ストア）。本物の Supabase・鍵は使わない。"""

import datetime
import pathlib

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import db
import jst
from fakes import FakeClient

PASSWORD = "test-password-not-real"
APP = str(pathlib.Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def fake(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(db, "make_client", lambda url, key: client)
    st.cache_resource.clear()
    st.cache_data.clear()
    yield client
    st.cache_resource.clear()
    st.cache_data.clear()


def new_app(password=PASSWORD, authed=False):
    at = AppTest.from_file(APP, default_timeout=30)
    if password is not None:
        at.secrets["APP_PASSWORD"] = password
    at.secrets["SUPABASE_URL"] = "https://example.invalid"
    at.secrets["SUPABASE_SERVICE_KEY"] = "fake-key-not-real"
    if authed:
        at.session_state["authed"] = True
    return at


def login(at, password=PASSWORD):
    at.text_input[0].set_value(password)
    at.button[0].click()
    return at.run()


def texts(elements):
    return [e.value for e in elements]


def click(at, label):
    matches = [b for b in at.button if b.label == label]
    assert matches, f"button {label!r} not found: {[b.label for b in at.button]}"
    matches[0].click()
    return at.run()


# I-01
def test_i01_unauthenticated_shows_only_login_and_touches_no_db(fake):
    at = new_app().run()
    assert not at.exception
    assert len(at.text_input) == 1
    assert len(at.title) == 0 and len(at.header) == 0
    assert len(at.sidebar.button) == 0 and len(at.sidebar.checkbox) == 0
    assert fake.calls == [] and fake.tables == []


# I-02
def test_i02_wrong_password_shows_error_and_no_body(fake):
    at = new_app().run()
    at = login(at, "wrong")
    assert any("パスワードが違います" in v for v in texts(at.error))
    assert len(at.title) == 0 and len(at.header) == 0
    assert fake.calls == []


def test_i02_five_wrong_passwords_lock_even_the_right_one(fake):
    at = new_app().run()
    for _ in range(5):
        at = login(at, "wrong")
    at = login(at, PASSWORD)
    assert any("試行回数が多すぎます" in v for v in texts(at.error))
    assert len(at.title) == 0
    assert fake.calls == []


# I-03
def test_i03_correct_password_opens_app_and_guides_first_setup(fake):
    at = new_app().run()
    at = login(at)
    assert not at.exception
    assert at.session_state["authed"] is True
    assert len(at.title) == 1
    assert any("まず①で目標プランを保存してください" in v for v in texts(at.info))
    assert fake.count("upsert") == 0 and fake.count("delete") == 0
    assert fake.count("select") >= 1


# I-04
def test_i04_missing_password_setting_refuses_to_start(fake):
    at = new_app(password=None).run()
    assert any("APP_PASSWORD" in v for v in texts(at.error))
    assert len(at.text_input) == 0 and len(at.title) == 0
    assert fake.calls == []


def test_i04_blank_password_setting_refuses_to_start(fake):
    at = new_app(password="   ").run()
    assert any("APP_PASSWORD" in v for v in texts(at.error))
    assert len(at.title) == 0 and fake.calls == []


def test_missing_supabase_secrets_are_reported_by_name(fake):
    at = AppTest.from_file(APP, default_timeout=30)
    at.secrets["APP_PASSWORD"] = PASSWORD
    at.session_state["authed"] = True
    at.run()
    errors = " ".join(texts(at.error))
    assert "SUPABASE_URL" in errors and "SUPABASE_SERVICE_KEY" in errors
    assert fake.calls == []


# I-05
def test_i05_saving_goal_writes_four_settings_and_shows_plan(fake):
    at = new_app(authed=True).run()
    at.number_input[0].set_value(70.0)
    at.number_input[1].set_value(60.0)
    at.date_input[0].set_value(datetime.date.today() + datetime.timedelta(days=60))
    at = click(at, "目標プランを保存")
    assert not at.exception
    settings = {k: r["value"] for (t, k), r in fake.rows.items() if t == "setting"}
    assert set(settings) == {"start_weight", "goal", "deadline", "start_date"}
    assert settings["start_weight"] == "70.0" and settings["goal"] == "60.0"
    assert fake.count("upsert") == 1
    assert not any("まず①で目標プランを保存してください" in v for v in texts(at.info))
    assert len(at.dataframe) >= 1


# I-06
def test_i06_record_weight_twice_same_day_keeps_one_row(fake, monkeypatch):
    monkeypatch.setattr(jst, "today_jst", lambda now=None: datetime.date(2026, 9, 26))
    at = new_app(authed=True).run()
    at.number_input[-1].set_value(66.0)
    at = click(at, "この日の体重を記録")
    assert not at.exception
    assert any("体重を記録しました" in v for v in texts(at.success))
    at.number_input[-1].set_value(65.4)
    at = click(at, "この日の体重を記録")
    logs = {k: r["value"] for (t, k), r in fake.rows.items() if t == "log"}
    assert logs == {"2026-09-26": "65.4"}


# I-07
def test_i07_write_failure_shows_error_and_no_success(fake):
    fake.fail_writes = True
    at = new_app(authed=True).run()
    at = click(at, "この日の体重を記録")
    assert any(db.MSG_WRITE_FAILED in v for v in texts(at.error))
    assert not any("体重を記録しました" in v for v in texts(at.success))
    assert "flash_message" not in at.session_state
    assert fake.rows == {}
    assert all("SECRET-KEY" not in v and "supabase.co" not in v for v in texts(at.error))


# I-08
def test_i08_read_failure_stops_rendering_instead_of_showing_an_empty_plan(fake):
    fake.fail_reads = True
    at = new_app(authed=True).run()
    assert any(db.MSG_READ_FAILED in v for v in texts(at.error))
    assert len(at.header) == 0 and len(at.dataframe) == 0
    assert not any("まず①で目標プランを保存してください" in v for v in texts(at.info))
    assert all("SECRET-KEY" not in v and "supabase.co" not in v for v in texts(at.error))


# I-09
def test_i09_reads_are_cached_and_writes_invalidate_the_cache(fake):
    at = new_app(authed=True).run()
    after_first = fake.count("select")
    assert after_first == 1
    at.run()
    assert fake.count("select") == after_first
    at = click(at, "この日の体重を記録")
    assert fake.count("upsert") == 1
    assert fake.count("select") == after_first + 1
    assert len(at.dataframe) >= 1 or any(True for _ in at.header)
    assert any(
        r["type"] == "log" for r in fake.rows.values()
    )


# I-15
def test_i15_reset_requires_the_confirmation_checkbox(fake):
    fake.seed("setting", "goal", "60.0")
    fake.seed("log", "2026-09-25", "66.0")
    at = new_app(authed=True).run()
    at.sidebar.button[0].click()
    at.run()
    assert fake.count("delete") == 0 and len(fake.rows) == 2
    assert any("先にチェックを入れてください" in w.value for w in at.sidebar.warning)


def test_i15_reset_with_confirmation_deletes_and_rearms_the_checkbox(fake):
    fake.seed("setting", "goal", "60.0")
    fake.seed("log", "2026-09-25", "66.0")
    at = new_app(authed=True).run()
    at.sidebar.checkbox[0].check()
    at.run()
    assert fake.count("delete") == 0
    at.sidebar.button[0].click()
    at.run()
    assert fake.count("delete") == 1 and fake.rows == {}
    assert at.sidebar.checkbox[0].value is False
    at.sidebar.button[0].click()
    at.run()
    assert fake.count("delete") == 1


def test_i15_reset_is_not_reachable_without_login(fake):
    fake.seed("log", "2026-09-25", "66.0")
    at = new_app().run()
    assert len(at.sidebar.button) == 0
    assert fake.count("delete") == 0 and len(fake.rows) == 1


# Q-05: 日付は日本時間
def test_q05_default_record_date_and_start_date_follow_jst(fake, monkeypatch):
    monkeypatch.setattr(jst, "today_jst", lambda now=None: datetime.date(2030, 1, 2))
    at = new_app(authed=True).run()
    assert at.date_input(key="record_date").value == datetime.date(2030, 1, 2)
    at = click(at, "目標プランを保存")
    assert fake.rows[("setting", "start_date")]["value"] == "2030-01-02"
