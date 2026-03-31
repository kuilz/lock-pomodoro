from __future__ import annotations

from dataclasses import dataclass


WORK = "work"
SHORT_BREAK = "short_break"
LONG_BREAK = "long_break"

PHASE_LABELS = {
    WORK: "Work",
    SHORT_BREAK: "Short Break",
    LONG_BREAK: "Long Break",
}


@dataclass(frozen=True)
class PomodoroConfig:
    work_minutes: float = 25
    cycles_per_round: int = 4
    short_break_minutes: float = 5
    long_break_minutes: float = 15
    lock_enabled: bool = True

    def validate(self) -> None:
        minute_values = {
            "work_minutes": self.work_minutes,
            "short_break_minutes": self.short_break_minutes,
            "long_break_minutes": self.long_break_minutes,
        }
        for name, value in minute_values.items():
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{name} must be a positive number")

        if not isinstance(self.cycles_per_round, int) or self.cycles_per_round <= 0:
            raise ValueError("cycles_per_round must be a positive integer")


@dataclass(frozen=True)
class EngineSnapshot:
    phase: str
    phase_label: str
    remaining_seconds: int
    current_cycle: int
    cycles_per_round: int
    is_running: bool


@dataclass(frozen=True)
class TickResult:
    snapshot: EngineSnapshot
    phase_changed: bool
    completed_phase: str | None
    should_lock: bool


class PomodoroEngine:
    def __init__(self, config: PomodoroConfig) -> None:
        config.validate()
        self.config = config
        self._phase = WORK
        self._current_cycle = 1
        self._remaining_seconds = self._duration_for_phase(WORK)
        self._is_running = False

    def start(self) -> EngineSnapshot:
        self._is_running = True
        return self.snapshot()

    def pause(self) -> EngineSnapshot:
        self._is_running = False
        return self.snapshot()

    def reset(self) -> EngineSnapshot:
        self._phase = WORK
        self._current_cycle = 1
        self._remaining_seconds = self._duration_for_phase(WORK)
        self._is_running = False
        return self.snapshot()

    def snapshot(self) -> EngineSnapshot:
        return EngineSnapshot(
            phase=self._phase,
            phase_label=PHASE_LABELS[self._phase],
            remaining_seconds=self._remaining_seconds,
            current_cycle=self._current_cycle,
            cycles_per_round=self.config.cycles_per_round,
            is_running=self._is_running,
        )

    def tick(self, elapsed_seconds: int = 1) -> TickResult:
        if elapsed_seconds <= 0 or not self._is_running:
            return TickResult(
                snapshot=self.snapshot(),
                phase_changed=False,
                completed_phase=None,
                should_lock=False,
            )

        phase_changed = False
        completed_phase: str | None = None
        should_lock = False

        remaining = elapsed_seconds
        while remaining > 0:
            if remaining < self._remaining_seconds:
                self._remaining_seconds -= remaining
                remaining = 0
                continue

            remaining -= self._remaining_seconds
            completed_phase = self._phase
            if completed_phase == WORK and self.config.lock_enabled:
                should_lock = True
            self._advance_phase()
            phase_changed = True

        return TickResult(
            snapshot=self.snapshot(),
            phase_changed=phase_changed,
            completed_phase=completed_phase,
            should_lock=should_lock,
        )

    def _advance_phase(self) -> None:
        if self._phase == WORK:
            if self._current_cycle < self.config.cycles_per_round:
                self._phase = SHORT_BREAK
            else:
                self._phase = LONG_BREAK
        elif self._phase == SHORT_BREAK:
            self._current_cycle += 1
            self._phase = WORK
        else:
            self._current_cycle = 1
            self._phase = WORK

        self._remaining_seconds = self._duration_for_phase(self._phase)

    def _duration_for_phase(self, phase: str) -> int:
        if phase == WORK:
            return max(1, round(self.config.work_minutes * 60))
        if phase == SHORT_BREAK:
            return max(1, round(self.config.short_break_minutes * 60))
        return max(1, round(self.config.long_break_minutes * 60))
