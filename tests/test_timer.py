import unittest

from talk_debt.timer import TalkDebtTimer, format_signed_mmss


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def now(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class TalkDebtTimerTests(unittest.TestCase):
    def test_formats_signed_mmss(self) -> None:
        self.assertEqual(format_signed_mmss(125), "02:05")
        self.assertEqual(format_signed_mmss(-15), "-00:15")

    def test_counts_down_and_into_debt(self) -> None:
        clock = FakeClock()
        timer = TalkDebtTimer(duration_seconds=2, _time_fn=clock.now)
        timer.start()

        self.assertEqual(timer.signed_remaining_seconds(), 2)
        clock.advance(2.2)
        self.assertEqual(timer.signed_remaining_seconds(), -1)

    def test_pause_and_resume(self) -> None:
        clock = FakeClock()
        timer = TalkDebtTimer(duration_seconds=10, _time_fn=clock.now)
        timer.start()
        clock.advance(3.0)
        timer.pause()
        clock.advance(5.0)
        self.assertEqual(timer.signed_remaining_seconds(), 7)
        timer.start()
        clock.advance(2.0)
        self.assertEqual(timer.signed_remaining_seconds(), 5)

    def test_next_speaker_restarts_running_timer(self) -> None:
        clock = FakeClock()
        timer = TalkDebtTimer(duration_seconds=30, _time_fn=clock.now)
        timer.start()
        clock.advance(10.0)
        timer.next_speaker()
        self.assertTrue(timer.is_running)
        self.assertEqual(timer.signed_remaining_seconds(), 30)

    def test_set_duration_resets(self) -> None:
        clock = FakeClock()
        timer = TalkDebtTimer(duration_seconds=30, _time_fn=clock.now)
        timer.start()
        clock.advance(10.0)
        timer.set_duration(60)
        self.assertFalse(timer.is_running)
        self.assertEqual(timer.signed_remaining_seconds(), 60)


if __name__ == "__main__":
    unittest.main()
