"""日本時間（JST, UTC+9）の日付。Community Cloud のサーバは UTC のことがあるため、date.today() を使わない。

日本は夏時間が無いので固定オフセットで足りる（tzdata に依存しない）。
"""

import datetime

JST = datetime.timezone(datetime.timedelta(hours=9), "JST")


def today_jst(now=None):
    """JST の今日の日付。now はタイムゾーン付きの datetime（テスト用）。"""
    if now is None:
        now = datetime.datetime.now(JST)
    elif now.tzinfo is None:
        raise ValueError("now にはタイムゾーン付きの datetime を渡してください。")
    return now.astimezone(JST).date()
