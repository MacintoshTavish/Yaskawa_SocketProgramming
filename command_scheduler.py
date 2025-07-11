import threading
import time
import logging
from typing import List, Dict, Any, Callable, Optional

class CommandScheduler:
    def __init__(self, commands: List[Dict[str, Any]], speed: float = 1.0):
        self.commands = sorted(commands, key=lambda c: c['timestamp'])
        self.speed = speed
        self._thread = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self.progress = 0
        self.total = len(self.commands)
        self.on_command: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_progress: Optional[Callable[[int, int], None]] = None
        self._start_time = None
        self._current_idx = 0
        self._lock = threading.Lock()

    def start(self):
        self._stop_event.clear()
        self._pause_event.set()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self._start_time = time.time()
        base_time = self.commands[0]['timestamp'] if self.commands else 0.0
        for idx, cmd in enumerate(self.commands):
            with self._lock:
                if self._stop_event.is_set():
                    break
                self._current_idx = idx
            # Wait for the right time
            now = time.time()
            elapsed = (now - self._start_time) * self.speed
            wait_time = max(0.0, (cmd['timestamp'] - base_time) / self.speed - elapsed)
            if wait_time > 0:
                self._wait_with_pause(wait_time)
            if self._stop_event.is_set():
                break
            if self.on_command:
                self.on_command(cmd)
            self.progress = idx + 1
            if self.on_progress:
                self.on_progress(self.progress, self.total)
        self._current_idx = self.total

    def _wait_with_pause(self, seconds):
        end_time = time.time() + seconds
        while time.time() < end_time:
            if self._stop_event.is_set():
                break
            while not self._pause_event.is_set():
                time.sleep(0.1)
            time.sleep(0.01)

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()
        if self._thread:
            self._thread.join(timeout=1)

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def get_status(self):
        return {
            'progress': int(100 * self.progress / self.total) if self.total else 100,
            'current_idx': self._current_idx,
            'total': self.total,
            'running': self.is_running(),
        } 