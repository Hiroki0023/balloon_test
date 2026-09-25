import datetime

import pytest

from jst import JST, today_jst

UTC = datetime.timezone.utc


# U-16 (Q-05: 日付は日本時間)
def test_u16_utc_evening_is_already_next_day_in_japan():
    now = datetime.datetime(2026, 9, 25, 15, 30, tzinfo=UTC)  # JST 2026-09-26 00:30
    assert today_jst(now) == datetime.date(2026, 9, 26)


def test_u16_boundaries():
    assert today_jst(datetime.datetime(2026, 9, 25, 14, 59, 59, tzinfo=UTC)) == datetime.date(2026, 9, 25)
    assert today_jst(datetime.datetime(2026, 9, 25, 15, 0, 0, tzinfo=UTC)) == datetime.date(2026, 9, 26)


def test_u16_year_boundary():
    assert today_jst(datetime.datetime(2026, 12, 31, 15, 0, tzinfo=UTC)) == datetime.date(2027, 1, 1)


def test_u16_jst_aware_input_is_kept():
    assert today_jst(datetime.datetime(2026, 9, 26, 0, 5, tzinfo=JST)) == datetime.date(2026, 9, 26)


def test_u16_naive_datetime_is_refused():
    with pytest.raises(ValueError):
        today_jst(datetime.datetime(2026, 9, 26, 0, 5))


def test_u16_default_returns_a_date():
    assert isinstance(today_jst(), datetime.date)
