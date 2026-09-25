"""Supabase(Postgres) へのデータアクセス層。Streamlit には依存しない。

テーブルは diet_data(type, key, value, updated_at)、主キーは (type, key)。
type は 'setting'（設定）か 'log'（日々の体重）。
"""

import datetime
import logging
import math
import re

import pandas as pd

TABLE = "diet_data"
PAGE_SIZE = 1000  # PostgREST が 1 回に返す行数の上限に合わせる

SETTING_KEYS = ("start_weight", "goal", "deadline", "start_date")
_WEIGHT_SETTING_KEYS = ("start_weight", "goal")
_DATE_SETTING_KEYS = ("deadline", "start_date")

WEIGHT_MIN = 20.0
WEIGHT_MAX = 200.0

REQUIRED_SECRETS = ("SUPABASE_URL", "SUPABASE_SERVICE_KEY")

MSG_READ_FAILED = "データベースに接続できませんでした。時間をおいて再度お試しください。"
MSG_WRITE_FAILED = "データベースに保存できませんでした。時間をおいて再度お試しください。"

_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_MAX_PAGES = 10_000

logger = logging.getLogger(__name__)


class DataStoreError(Exception):
    """DB との通信・保存に失敗した。メッセージは固定文で、URL や鍵を含めない。"""


class InvalidInputError(ValueError):
    """保存しようとした値が仕様の範囲外。DB へは送らない。"""


def make_client(url, key):
    """supabase-py のクライアントを作る。テストでは差し替えるため、import は遅延させる。"""
    try:
        from supabase import create_client

        return create_client(url, key)
    except ImportError as exc:
        logger.error(
            "supabase パッケージを読み込めません（%s）。streamlit を起動する Python に "
            "`pip install -r requirements.txt` を実行してください。",
            type(exc).__name__,
        )
        raise DataStoreError(MSG_READ_FAILED) from None
    except Exception as exc:
        logger.error("supabase client creation failed: %s", type(exc).__name__)
        raise DataStoreError(MSG_READ_FAILED) from None


def missing_secrets(secrets):
    """必須の secrets のうち、未設定・空・文字列でないものの名前を返す（値は返さない）。"""
    missing = []
    for name in REQUIRED_SECRETS:
        try:
            value = secrets.get(name)
        except Exception:
            value = None
        if not isinstance(value, str) or not value.strip():
            missing.append(name)
    return missing


def normalize_weight(value):
    """体重を 20.0〜200.0 の範囲で検査し、小数 1 桁の文字列にして返す。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise InvalidInputError("体重は数値で指定してください。") from None
    if not math.isfinite(number):
        raise InvalidInputError("体重は有限の数値で指定してください。")
    rounded = round(number, 1)
    if not WEIGHT_MIN <= rounded <= WEIGHT_MAX:
        raise InvalidInputError(f"体重は {WEIGHT_MIN:.0f}〜{WEIGHT_MAX:.0f}kg の範囲で指定してください。")
    return f"{rounded:.1f}"


def normalize_date(value):
    """YYYY-MM-DD の文字列で、暦として正しい日付だけを通す。"""
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        raise InvalidInputError("日付は YYYY-MM-DD の形式で指定してください。")
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        raise InvalidInputError("存在しない日付です。") from None
    return value


def _validate_settings(items):
    if not isinstance(items, dict):
        raise InvalidInputError("設定は辞書で指定してください。")
    validated = {}
    for key, value in items.items():
        if key not in SETTING_KEYS:
            raise InvalidInputError("未対応の設定項目です。")
        if key in _WEIGHT_SETTING_KEYS:
            validated[key] = normalize_weight(value)
        else:
            validated[key] = normalize_date(value)
    return validated


class DietStore:
    def __init__(self, client, clock=None):
        self._client = client
        self._clock = clock or (lambda: datetime.datetime.now(datetime.timezone.utc))

    def _table(self):
        return self._client.table(TABLE)

    def _stamp(self):
        return self._clock().isoformat()

    def _run(self, build, message):
        try:
            return build().execute()
        except Exception as exc:
            logger.error("datastore request failed: %s (code=%s)", type(exc).__name__, getattr(exc, "code", None))
            raise DataStoreError(message) from None

    def fetch_all(self):
        """全行を 1,000 件ずつ最後まで取得して、{'type','key','value'} の辞書のリストで返す。"""
        rows = []
        start = 0
        for _ in range(_MAX_PAGES):
            end = start + PAGE_SIZE - 1
            response = self._run(
                lambda: self._table()
                .select("type,key,value")
                .order("type")
                .order("key")
                .range(start, end),
                MSG_READ_FAILED,
            )
            page = list(response.data or [])
            rows.extend(page)
            if len(page) < PAGE_SIZE:
                return rows
            start += PAGE_SIZE
        raise DataStoreError(MSG_READ_FAILED)

    def _upsert(self, records):
        stamp = self._stamp()
        payload = [dict(record, updated_at=stamp) for record in records]
        self._run(lambda: self._table().upsert(payload, on_conflict="type,key"), MSG_WRITE_FAILED)

    def upsert_settings(self, items):
        """設定を 1 リクエストでまとめて保存する。1 つでも不正なら何も送らない。"""
        validated = _validate_settings(items)
        if not validated:
            return
        self._upsert({"type": "setting", "key": key, "value": value} for key, value in validated.items())

    def upsert_log(self, date_str, weight):
        """1 日分の体重を保存する。同じ日付は上書き（1 日 1 行）。"""
        record = {
            "type": "log",
            "key": normalize_date(date_str),
            "value": normalize_weight(weight),
        }
        self._upsert([record])

    def delete_all(self):
        """diet_data の全行を削除する（リセット用）。"""
        self._run(lambda: self._table().delete().neq("type", ""), MSG_WRITE_FAILED)


def settings_from_rows(rows):
    """type == 'setting' の行から {key: value(str)} の辞書を作る。"""
    return {row["key"]: row["value"] for row in rows if row.get("type") == "setting"}


def log_from_rows(rows):
    """type == 'log' の行から date(str)/weight(float) の表を作る。日付昇順。空なら列だけの空表。"""
    logs = [row for row in rows if row.get("type") == "log"]
    if not logs:
        return pd.DataFrame(columns=["date", "weight"])
    out = pd.DataFrame(
        {
            "date": [str(row["key"]) for row in logs],
            "weight": [float(row["value"]) for row in logs],
        }
    )
    return out.sort_values("date").reset_index(drop=True)
