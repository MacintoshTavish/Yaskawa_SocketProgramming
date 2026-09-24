import threading
import time
import unittest
from csv_ros_tcp_processor.command_scheduler import CommandScheduler


class SchedulerTests(unittest.TestCase):
    def test_speed_scales_all_deadlines_once(self):
        for speed in (0.5, 2.0):
            with self.subTest(speed=speed):
                times = []
                scheduler = CommandScheduler([{'timestamp': t} for t in (0, 0.08, 0.16)], speed)
                scheduler.on_command = lambda _: times.append(time.monotonic())
                start = time.monotonic()
                scheduler.start()
                self.assertTrue(scheduler.wait(2))
                self.assertIsNone(scheduler.error)
                self.assertGreaterEqual(times[-1] - start, 0.16 / speed - 0.01)
                self.assertLess(times[-1] - start, 0.16 / speed + 0.2)

    def test_first_timestamp_is_delay_from_playback_start(self):
        event = threading.Event()
        scheduler = CommandScheduler([{'timestamp': 0.12}])
        scheduler.on_command = lambda _: event.set()
        scheduler.start()
        self.addCleanup(scheduler.stop)
        self.assertFalse(event.wait(0.05))
        self.assertTrue(event.wait(1))

    def test_pause_preserves_remaining_time(self):
        event = threading.Event()
        scheduler = CommandScheduler([{'timestamp': 0.16}])
        scheduler.on_command = lambda _: event.set()
        scheduler.start()
        self.addCleanup(scheduler.stop)
        time.sleep(0.03)
        scheduler.pause()
        self.assertFalse(event.wait(0.2))
        scheduler.resume()
        self.assertFalse(event.wait(0.05))
        self.assertTrue(event.wait(1))
        self.assertTrue(scheduler.wait(1))

    def test_stop_while_paused_and_restart(self):
        scheduler = CommandScheduler([{'timestamp': 100}])
        scheduler.start()
        scheduler.pause()
        scheduler.stop()
        self.assertFalse(scheduler.is_running())
        self.assertEqual(scheduler.progress, 0)
        scheduler.commands = [{'timestamp': 0}]
        scheduler.start()
        self.assertTrue(scheduler.wait(1))
        self.assertEqual(scheduler.progress, 1)

    def test_callback_failure_stops_and_reports(self):
        scheduler = CommandScheduler([{'timestamp': 0}, {'timestamp': 0}])
        scheduler.on_command = lambda _: False
        scheduler.start()
        scheduler.wait(1)
        self.assertIsInstance(scheduler.error, RuntimeError)
        self.assertEqual(scheduler.progress, 0)

    def test_rejects_invalid_speed(self):
        for speed in (0, -1, float('nan'), float('inf'), True):
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                CommandScheduler([], speed)
