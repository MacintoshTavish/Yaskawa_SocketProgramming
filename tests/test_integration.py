import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from csv_ros_tcp_processor.demo import run_demo
from csv_ros_tcp_processor.main import main
from tcp_ros_program.tcp_server import TCPROSServer


class IntegrationTests(unittest.TestCase):
    def test_built_in_demo_delivers_and_records_every_command(self):
        result = run_demo(speed=50)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['planned'], 5)
        self.assertEqual(result['received'], result['planned'])
        self.assertEqual(result['recorded'], result['planned'])
        self.assertEqual(result['automatic_stops'], 1)

    def test_every_csv_crosses_real_tcp(self):
        for path in (Path(__file__).resolve().parents[1] / 'examples').glob('*.csv'):
            with self.subTest(path=path):
                result = run_demo(path, speed=100)
                self.assertEqual(result['received'], result['planned'])

    def test_dry_run_and_summary_without_connecting(self):
        path = Path(__file__).resolve().parents[1] / 'examples/basic_movement.csv'
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as output:
            summary = Path(tmp) / 'result.json'
            with patch('csv_ros_tcp_processor.main.TCPCommandSender.connect') as connect:
                self.assertEqual(main(['--csv', str(path), '--dry-run', '--summary', str(summary)]), 0)
                connect.assert_not_called()
            self.assertEqual(len(output.getvalue().splitlines()), 3)
            self.assertEqual(json.loads(summary.read_text())['status'], 'validated')

    def test_invalid_input_fails_before_connection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.csv'
            path.write_text('timestamp,command_type,topic,parameters\n0,unknown,,{}\n')
            with patch('csv_ros_tcp_processor.main.TCPCommandSender.connect') as connect:
                with self.assertLogs(level='ERROR'):
                    self.assertEqual(main(['--csv', str(path)]), 1)
                connect.assert_not_called()

    def test_cli_playback_acknowledged_summary(self):
        path = Path(__file__).resolve().parents[1] / 'examples/basic_movement.csv'
        with tempfile.TemporaryDirectory() as tmp, TCPROSServer(port=0) as broker:
            summary = Path(tmp) / 'result.json'
            code = main(['--csv', str(path), '--port', str(broker.port), '--speed', '100', '--summary', str(summary)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(summary.read_text())['completed'], 3)
            self.assertEqual(broker.handler.get_stats()['/cmd_vel'], 3)
