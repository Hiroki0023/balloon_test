"""単一パスワードによる画面ゲート。

比較とロックアウトは Streamlit に依存しない純粋なロジック。require_password() だけが Streamlit を使う。
"""

import hmac
import math
import threading
import time

LOCK_AFTER_FAILURES = 5
LOCK_SECONDS = 60


def check_password(entered, expected):
    """入力が期待値と一致するか。期待値が未設定・空・空白のみなら常に False（閉じる側に倒す）。"""
    if not isinstance(expected, str) or not expected.strip():
        return False
    if not isinstance(entered, str) or entered == "":
        return False
    return hmac.compare_digest(entered.encode("utf-8"), expected.encode("utf-8"))


class Lockout:
    """連続失敗が続いたら一定時間ロックする。ロック中は正しいパスワードも受け付けない。"""

    def __init__(self, max_failures=LOCK_AFTER_FAILURES, lock_seconds=LOCK_SECONDS, clock=time.monotonic):
        self._max_failures = max_failures
        self._lock_seconds = lock_seconds
        self._clock = clock
        self._failures = 0
        self._locked_until = None
        self._mutex = threading.Lock()

    def _locked(self):
        if self._locked_until is None:
            return False
        if self._clock() >= self._locked_until:
            self._locked_until = None
            return False
        return True

    def is_locked(self):
        with self._mutex:
            return self._locked()

    def remaining_seconds(self):
        with self._mutex:
            if not self._locked():
                return 0
            return max(1, math.ceil(self._locked_until - self._clock()))

    def attempt(self, entered, expected):
        """'ok'（成功）／'locked'（ロック中）／'bad'（不一致）のいずれかを返す。"""
        with self._mutex:
            if self._locked():
                return "locked"
            if check_password(entered, expected):
                self._failures = 0
                return "ok"
            self._failures += 1
            if self._failures >= self._max_failures:
                self._failures = 0
                self._locked_until = self._clock() + self._lock_seconds
            return "bad"


def require_password():
    """認証済みでなければログイン欄だけを出して st.stop() する。set_page_config の直後に呼ぶ。"""
    import streamlit as st

    try:
        expected = st.secrets.get("APP_PASSWORD")
    except Exception:
        expected = None
    if not isinstance(expected, str) or not expected.strip():
        st.error("パスワードが設定されていないため、アプリを開始できません。管理者（本人）が APP_PASSWORD を設定してください。")
        st.stop()

    if st.session_state.get("authed") is True:
        return

    lockout = _shared_lockout()
    with st.form("login"):
        entered = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")

    if submitted:
        result = lockout.attempt(entered, expected)
        if result == "ok":
            st.session_state["authed"] = True
            st.rerun()
        elif result == "locked":
            st.error(f"試行回数が多すぎます。{lockout.remaining_seconds()} 秒後にもう一度お試しください。")
        else:
            st.error("パスワードが違います。")
    st.stop()


def _shared_lockout():
    import streamlit as st

    @st.cache_resource
    def _make():
        return Lockout()

    return _make()
