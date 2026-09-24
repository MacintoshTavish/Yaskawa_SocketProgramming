"""Pauseable playback against a monotonic clock, with explicit failure status."""
import math
import threading
import time


class CommandScheduler:
    def __init__(self, commands, speed=1.0):
        if isinstance(speed, bool) or not math.isfinite(speed) or speed <= 0:
            raise ValueError('speed must be finite and greater than zero')
        if any(not math.isfinite(c['timestamp']) or c['timestamp'] < 0 for c in commands):
            raise ValueError('timestamps must be finite and nonnegative')
        self.commands = sorted(commands, key=lambda c: (c['timestamp'], -(c.get('priority') or 0)))
        self.speed = speed
        self.total = len(self.commands)
        self.progress = 0
        self.error = None
        self.on_command = None
        self.on_progress = None
        self._thread = None
        self._condition = threading.Condition()
        self._stopped = False
        self._paused_at = None
        self._paused_seconds = 0.0
        self._start_time = None
        self._current_idx = 0

    def start(self):
        with self._condition:
            if self.is_running():
                raise RuntimeError('Playback is already running')
            self._stopped = False
            self._paused_at = None
            self._paused_seconds = 0.0
            self.progress = self._current_idx = 0
            self.error = None
            self._start_time = time.monotonic()
            self._thread = threading.Thread(target=self._run, daemon=True, name='command-playback')
            self._thread.start()
        return self

    def _run(self):
        try:
            for index, command in enumerate(self.commands):
                with self._condition:
                    self._current_idx = index
                    while not self._stopped:
                        if self._paused_at is not None:
                            self._condition.wait()
                            continue
                        elapsed = time.monotonic() - self._start_time - self._paused_seconds
                        remaining = command['timestamp'] / self.speed - elapsed
                        if remaining <= 0:
                            break
                        self._condition.wait(timeout=remaining)
                    if self._stopped:
                        return
                if self.on_command and self.on_command(command) is False:
                    raise RuntimeError(f'Command failed at index {index}')
                self.progress = index + 1
                if self.on_progress:
                    self.on_progress(self.progress, self.total)
            self._current_idx = self.total
        except Exception as exc:
            self.error = exc

    def pause(self):
        with self._condition:
            if self.is_running() and self._paused_at is None:
                self._paused_at = time.monotonic()
            self._condition.notify_all()

    def resume(self):
        with self._condition:
            if self._paused_at is not None:
                self._paused_seconds += time.monotonic() - self._paused_at
                self._paused_at = None
            self._condition.notify_all()

    def stop(self):
        with self._condition:
            self._stopped = True
            self._condition.notify_all()
        self.wait(timeout=2)

    def wait(self, timeout=None):
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout)
        return not self.is_running()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def get_status(self):
        return {'progress': int(100 * self.progress / self.total) if self.total else 100,
                'completed': self.progress, 'current_idx': self._current_idx,
                'total': self.total, 'running': self.is_running(),
                'paused': self._paused_at is not None, 'stopped': self._stopped,
                'error': str(self.error) if self.error else None}
