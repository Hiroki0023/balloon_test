import gate
from gate import Lockout, check_password


# U-12
def test_u12_correct_wrong_and_empty_passwords():
    assert check_password("s3cret-パスワード", "s3cret-パスワード") is True
    assert check_password("wrong", "s3cret") is False
    assert check_password("", "s3cret") is False
    assert check_password(None, "s3cret") is False
    assert check_password("S3CRET", "s3cret") is False


# U-13
def test_u13_unset_expected_password_always_fails_closed():
    for expected in (None, "", "   ", 12345):
        assert check_password("anything", expected) is False
        assert check_password("", expected) is False
        assert check_password(expected, expected) is False


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


# U-14
def test_u14_five_failures_lock_and_even_correct_password_is_refused():
    clock = Clock()
    lock = Lockout(clock=clock)
    for _ in range(4):
        assert lock.attempt("x", "pw") == "bad"
        assert not lock.is_locked()
    assert lock.attempt("x", "pw") == "bad"
    assert lock.is_locked()
    assert lock.attempt("pw", "pw") == "locked"
    assert lock.remaining_seconds() == 60


def test_u14_lock_expires_after_sixty_seconds():
    clock = Clock()
    lock = Lockout(clock=clock)
    for _ in range(5):
        lock.attempt("x", "pw")
    clock.now += 59
    assert lock.attempt("pw", "pw") == "locked"
    assert lock.remaining_seconds() == 1
    clock.now += 1
    assert not lock.is_locked()
    assert lock.attempt("pw", "pw") == "ok"


def test_u14_success_resets_the_failure_counter():
    lock = Lockout(clock=Clock())
    for _ in range(4):
        lock.attempt("x", "pw")
    assert lock.attempt("pw", "pw") == "ok"
    for _ in range(4):
        assert lock.attempt("x", "pw") == "bad"
    assert not lock.is_locked()


def test_u14_failures_after_lock_expiry_start_from_zero():
    clock = Clock()
    lock = Lockout(clock=clock)
    for _ in range(5):
        lock.attempt("x", "pw")
    clock.now += 61
    for _ in range(4):
        assert lock.attempt("x", "pw") == "bad"
    assert not lock.is_locked()


def test_gate_constants_match_design():
    assert gate.LOCK_AFTER_FAILURES == 5
    assert gate.LOCK_SECONDS == 60
