"""本物の Supabase に対する確認（I-11 / I-12 / I-13）。hiroki 本人が自分のPCで実行する。

  python scripts/live_smoke.py

- .streamlit/secrets.toml の SUPABASE_URL / SUPABASE_SERVICE_KEY を読む。鍵は表示しない。
- 触るのはマーカー行（type=log, key=1999-01-01）だけ。全消去は使わない。
- 環境変数 SUPABASE_PUBLIC_KEY（公開用の anon / publishable キー）を渡すと、I-13 も確認する。
  例: SUPABASE_PUBLIC_KEY=... python scripts/live_smoke.py
"""

import os
import pathlib
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import DietStore, TABLE, make_client  # noqa: E402

MARKER_DATE = "1999-01-01"
BAD_ROWS = [
    ("体重 19.9", {"type": "log", "key": MARKER_DATE, "value": "19.9"}),
    ("体重 200.1", {"type": "log", "key": MARKER_DATE, "value": "200.1"}),
    ("体重が数値でない", {"type": "log", "key": MARKER_DATE, "value": "abc"}),
    ("日付の形式が違う", {"type": "log", "key": "1999/01/01", "value": "60.0"}),
    ("未知の type", {"type": "other", "key": "x", "value": "1"}),
]

# PostgreSQL のエラーコード。通信エラーなどを「拒否された」と取り違えないために使う。
CHECK_VIOLATION = "23514"
NOT_NULL_VIOLATION = "23502"
INSUFFICIENT_PRIVILEGE = "42501"

results = []


def report(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))


def error_code(exc):
    return getattr(exc, "code", None)


def delete_marker(client):
    client.table(TABLE).delete().eq("type", "log").eq("key", MARKER_DATE).execute()


def load_secrets():
    path = ROOT / ".streamlit" / "secrets.toml"
    if not path.exists():
        sys.exit(".streamlit/secrets.toml がありません。README の初回セットアップを先に行ってください。")
    with open(path, "rb") as f:
        data = tomllib.load(f)
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY") if not data.get(k)]
    if missing:
        sys.exit("secrets.toml に未設定の項目があります: " + ", ".join(missing))
    return data["SUPABASE_URL"], data["SUPABASE_SERVICE_KEY"]


def check_smoke(client):
    """I-11: 接続 → マーカー行の upsert → 読み出し → その 1 行だけ削除。"""
    store = DietStore(client)
    try:
        store.upsert_log(MARKER_DATE, 20.0)
        rows = [r for r in store.fetch_all() if r["type"] == "log" and r["key"] == MARKER_DATE]
        report("I-11 upsert して読み出せる", len(rows) == 1 and rows[0]["value"] == "20.0")
        store.upsert_log(MARKER_DATE, 20.5)
        rows = [r for r in store.fetch_all() if r["type"] == "log" and r["key"] == MARKER_DATE]
        report("I-11 同じ日付は 1 行のまま上書きされる", len(rows) == 1 and rows[0]["value"] == "20.5")
    finally:
        try:
            delete_marker(client)
        except Exception as exc:
            report("I-11 マーカー行の削除", False, type(exc).__name__)
            return
    remaining = [r for r in store.fetch_all() if r["type"] == "log" and r["key"] == MARKER_DATE]
    report("I-11 マーカー行を削除できた", not remaining)


def check_constraints(client):
    """I-12: 不正な行が DB の制約で拒否される（アプリの検査を通さず直接送る）。"""
    for label, row in BAD_ROWS:
        try:
            client.table(TABLE).insert(row).execute()
        except Exception as exc:
            code = error_code(exc)
            if code in (CHECK_VIOLATION, NOT_NULL_VIOLATION):
                report(f"I-12 拒否される: {label}", True, f"DB の制約 {code}")
            else:
                report(f"I-12 拒否される: {label}", False, f"制約による拒否ではありません（{type(exc).__name__}, code={code}）")
        else:
            report(f"I-12 拒否される: {label}", False, "保存できてしまった")
            try:
                client.table(TABLE).delete().eq("type", row["type"]).eq("key", row["key"]).execute()
            except Exception:
                pass


def check_public_key(url, public_key):
    """I-13: 公開用キーでは Data API から読めも書けもしない。"""
    try:
        public = make_client(url, public_key)
    except Exception as exc:
        report("I-13 公開用キーでクライアントを作れる", False, type(exc).__name__)
        return
    try:
        rows = public.table(TABLE).select("type,key,value").limit(1).execute().data
    except Exception as exc:
        code = error_code(exc)
        report("I-13 公開用キーでは読めない", code == INSUFFICIENT_PRIVILEGE, f"{type(exc).__name__}, code={code}")
    else:
        report("I-13 公開用キーでは読めない", False, f"{len(rows)} 行が返った")
    try:
        public.table(TABLE).insert({"type": "log", "key": MARKER_DATE, "value": "20.0"}).execute()
    except Exception as exc:
        code = error_code(exc)
        report("I-13 公開用キーでは書けない", code == INSUFFICIENT_PRIVILEGE, f"{type(exc).__name__}, code={code}")
    else:
        report("I-13 公開用キーでは書けない", False, "保存できてしまった")


def main():
    url, service_key = load_secrets()
    try:
        client = make_client(url, service_key)
    except Exception as exc:
        print(f"[FAIL] クライアントを作れませんでした - {type(exc).__name__}")
        return 1
    try:
        check_smoke(client)
        check_constraints(client)
    except Exception as exc:
        report("接続・実行", False, type(exc).__name__)
    public_key = os.environ.get("SUPABASE_PUBLIC_KEY")
    if public_key:
        check_public_key(url, public_key)
    else:
        print("[SKIP] I-13: 環境変数 SUPABASE_PUBLIC_KEY が無いため、公開用キーの確認は行っていません。")
    print(f"\n{sum(results)} / {len(results)} 件 PASS")
    return 0 if results and all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
