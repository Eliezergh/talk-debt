import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from talk_debt.stats import StatsStore


class FakeNow:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value


class StatsStoreTests(unittest.TestCase):
    def test_records_loop_and_over_time(self) -> None:
        now = FakeNow(datetime(2026, 6, 16, 12, 0, tzinfo=UTC))
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "stats.json"
            store = StatsStore(path=path, now_fn=now.now)

            session_id = store.start_session()
            store.add_loop(session_id, allocated_seconds=120, consumed_seconds=140)
            store.end_session(session_id)

            session = store.get_session(session_id)

        self.assertIsNotNone(session)
        assert session is not None
        self.assertEqual(len(session.loops), 1)
        loop = session.loops[0]
        self.assertEqual(loop.allocated_seconds, 120)
        self.assertEqual(loop.consumed_seconds, 140)
        self.assertTrue(loop.went_over)
        self.assertEqual(loop.over_seconds, 20)
        self.assertIsNotNone(session.ended_at)

    def test_prunes_sessions_older_than_retention(self) -> None:
        now = FakeNow(datetime(2026, 6, 16, 12, 0, tzinfo=UTC))
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "stats.json"
            store = StatsStore(path=path, now_fn=now.now)

            old_session = store.start_session()
            store.add_loop(old_session, allocated_seconds=120, consumed_seconds=90)
            store.end_session(old_session)

            now.value = now.value + timedelta(days=8)
            recent_session = store.start_session()
            store.add_loop(recent_session, allocated_seconds=120, consumed_seconds=100)

            sessions = store.list_sessions()

        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].session_id, recent_session)


if __name__ == "__main__":
    unittest.main()
