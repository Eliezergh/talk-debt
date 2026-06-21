import json
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
            store.add_loop(
                session_id,
                allocated_seconds=120,
                consumed_seconds=140,
                speaker_name="Alex",
            )
            store.end_session(session_id)

            session = store.get_session(session_id)

        self.assertIsNotNone(session)
        assert session is not None
        self.assertEqual(len(session.loops), 1)
        loop = session.loops[0]
        self.assertEqual(loop.allocated_seconds, 120)
        self.assertEqual(loop.consumed_seconds, 140)
        self.assertEqual(loop.speaker_name, "Alex")
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

    def test_loads_legacy_loops_without_speaker_name(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "stats.json"
            path.write_text(
                json.dumps(
                    {
                        "sessions": [
                            {
                                "session_id": "legacy",
                                "started_at": "2026-06-16T12:00:00+00:00",
                                "loops": [
                                    {
                                        "timestamp": "2026-06-16T12:01:00+00:00",
                                        "allocated_seconds": 120,
                                        "consumed_seconds": 110,
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            store = StatsStore(path=path)

            session = store.get_session("legacy")

        self.assertIsNotNone(session)
        assert session is not None
        self.assertEqual(session.loops[0].speaker_name, "Unassigned")

    def test_load_migrates_from_legacy_location(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            new_path = base / ".talk-debt" / "stats.json"
            legacy_path = base / ".talk_debt_stats.json"
            legacy_path.write_text(
                json.dumps(
                    {
                        "sessions": [
                            {
                                "session_id": "legacy",
                                "started_at": "2026-06-16T12:00:00+00:00",
                                "loops": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            store = StatsStore(path=new_path, legacy_path=legacy_path)

            sessions = store.list_sessions()

            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0].session_id, "legacy")
            self.assertTrue(new_path.exists())
            self.assertFalse(legacy_path.exists())


if __name__ == "__main__":
    unittest.main()
