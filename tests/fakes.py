"""supabase-py の table API の最小限の偽物。ネットワークも本物の鍵も使わない。"""


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, client):
        self._client = client
        self._op = None
        self._payload = None
        self._on_conflict = None
        self._range = None

    def select(self, columns):
        self._op = "select"
        return self

    def order(self, column):
        return self

    def range(self, start, end):
        self._range = (start, end)
        return self

    def upsert(self, payload, on_conflict=None):
        self._op = "upsert"
        self._payload = payload
        self._on_conflict = on_conflict
        return self

    def delete(self):
        self._op = "delete"
        return self

    def neq(self, column, value):
        return self

    def execute(self):
        client = self._client
        if self._op == "select":
            client.calls.append(("select", self._range))
            if client.fail_reads:
                raise RuntimeError(client.failure_text)
            rows = sorted(client.rows.values(), key=lambda r: (r["type"], r["key"]))
            start, end = self._range
            page = rows[start : end + 1]
            return FakeResponse([{k: r[k] for k in ("type", "key", "value")} for r in page])
        if self._op == "upsert":
            client.calls.append(("upsert", self._payload, self._on_conflict))
            if client.fail_writes:
                raise RuntimeError(client.failure_text)
            for record in self._payload:
                client.rows[(record["type"], record["key"])] = dict(record)
            return FakeResponse(list(self._payload))
        if self._op == "delete":
            client.calls.append(("delete",))
            if client.fail_writes:
                raise RuntimeError(client.failure_text)
            client.rows.clear()
            return FakeResponse([])
        raise AssertionError("unexpected operation")


class FakeClient:
    def __init__(self):
        self.rows = {}
        self.calls = []
        self.tables = []
        self.fail_reads = False
        self.fail_writes = False
        self.failure_text = "boom https://secret-project.supabase.co key=SECRET-KEY-123"

    def table(self, name):
        self.tables.append(name)
        return FakeQuery(self)

    def seed(self, type_, key, value):
        self.rows[(type_, key)] = {"type": type_, "key": key, "value": value, "updated_at": "seed"}

    def count(self, op):
        return sum(1 for call in self.calls if call[0] == op)
