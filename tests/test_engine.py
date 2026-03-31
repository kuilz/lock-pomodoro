import unittest

from lock_pomodoro.engine import LONG_BREAK, SHORT_BREAK, WORK, PomodoroConfig, PomodoroEngine


class PomodoroEngineTests(unittest.TestCase):
    def test_round_progression_uses_short_and_long_breaks(self) -> None:
        now = 1000.0
        engine = PomodoroEngine(
            PomodoroConfig(
                work_minutes=1,
                cycles_per_round=3,
                short_break_minutes=1,
                long_break_minutes=2,
                lock_enabled=True,
            )
        )
        engine.start(now)

        result = engine.tick(now + 60)
        self.assertEqual(result.completed_phase, WORK)
        self.assertEqual(result.work_completion_count, 1)
        self.assertEqual(result.snapshot.phase, SHORT_BREAK)
        self.assertEqual(result.snapshot.current_cycle, 1)

        result = engine.tick(now + 120)
        self.assertEqual(result.snapshot.phase, WORK)
        self.assertEqual(result.snapshot.current_cycle, 2)

        result = engine.tick(now + 180)
        self.assertEqual(result.snapshot.phase, SHORT_BREAK)
        self.assertEqual(result.snapshot.current_cycle, 2)

        result = engine.tick(now + 240)
        self.assertEqual(result.snapshot.phase, WORK)
        self.assertEqual(result.snapshot.current_cycle, 3)

        result = engine.tick(now + 300)
        self.assertEqual(result.snapshot.phase, LONG_BREAK)
        self.assertEqual(result.snapshot.current_cycle, 3)

        result = engine.tick(now + 420)
        self.assertEqual(result.snapshot.phase, WORK)
        self.assertEqual(result.snapshot.current_cycle, 1)

    def test_lock_flag_only_applies_to_work_completion(self) -> None:
        now = 1000.0
        engine = PomodoroEngine(
            PomodoroConfig(
                work_minutes=1,
                cycles_per_round=2,
                short_break_minutes=1,
                long_break_minutes=1,
                lock_enabled=False,
            )
        )
        engine.start(now)

        result = engine.tick(now + 60)
        self.assertEqual(result.work_completion_count, 0)
        self.assertEqual(result.snapshot.phase, SHORT_BREAK)

        result = engine.tick(now + 120)
        self.assertEqual(result.work_completion_count, 0)
        self.assertEqual(result.snapshot.phase, WORK)

    def test_pause_and_reset_preserve_expected_state(self) -> None:
        now = 1000.0
        engine = PomodoroEngine(
            PomodoroConfig(work_minutes=2, cycles_per_round=2, short_break_minutes=1, long_break_minutes=1)
        )
        engine.start(now)
        engine.tick(now + 30)

        paused = engine.pause(now + 30)
        self.assertFalse(paused.is_running)
        self.assertEqual(paused.remaining_seconds, 90)

        reset = engine.reset(now + 30)
        self.assertFalse(reset.is_running)
        self.assertEqual(reset.phase, WORK)
        self.assertEqual(reset.current_cycle, 1)
        self.assertEqual(reset.remaining_seconds, 120)

    def test_fractional_minutes_are_supported(self) -> None:
        now = 1000.0
        engine = PomodoroEngine(
            PomodoroConfig(
                work_minutes=0.5,
                cycles_per_round=2,
                short_break_minutes=0.25,
                long_break_minutes=1.5,
            )
        )

        self.assertEqual(engine.snapshot().remaining_seconds, 30)
        engine.start(now)

        result = engine.tick(now + 30)
        self.assertEqual(result.completed_phase, WORK)
        self.assertEqual(result.work_completion_count, 1)
        self.assertEqual(result.snapshot.phase, SHORT_BREAK)
        self.assertEqual(result.snapshot.remaining_seconds, 15)

    def test_large_elapsed_time_counts_multiple_work_completions(self) -> None:
        now = 1000.0
        engine = PomodoroEngine(
            PomodoroConfig(
                work_minutes=1,
                cycles_per_round=2,
                short_break_minutes=1,
                long_break_minutes=1,
                lock_enabled=True,
            )
        )
        engine.start(now)

        result = engine.tick(now + 240)

        self.assertEqual(result.work_completion_count, 2)
        self.assertEqual(result.snapshot.phase, WORK)
        self.assertEqual(result.snapshot.current_cycle, 1)

    def test_snapshot_uses_phase_deadline_while_running(self) -> None:
        now = 1000.0
        engine = PomodoroEngine(PomodoroConfig(work_minutes=1))
        engine.start(now)

        snapshot = engine.snapshot(now + 12.2)

        self.assertEqual(snapshot.remaining_seconds, 48)

    def test_fractional_minutes_must_still_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            PomodoroConfig(work_minutes=0.0).validate()


if __name__ == "__main__":
    unittest.main()
