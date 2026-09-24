"""Self-contained loopback demonstration; no ROS installation or robot required."""
import argparse
import json
import tempfile
import threading
from pathlib import Path
from .command_converter import prepare_commands
from .command_scheduler import CommandScheduler
from .csv_parser import CSVCommandParser
from tcp_ros_program.recording import JSONLRecorder, read_recording
from tcp_ros_program.tcp_client import TCPROSClient
from tcp_ros_program.tcp_server import TCPROSServer


def run_demo(csv_file=None, speed=20.0, record=None):
    commands = CSVCommandParser(csv_file).parse() if csv_file else [
        {'timestamp': 0, 'command_type': 'publish_string', 'topic': '',
         'parameters': {'data': 'Demo started'}},
        {'timestamp': 0.1, 'command_type': 'move', 'topic': '', 'duration': 0.2,
         'parameters': {'linear_x': 0.25, 'angular_z': 0.0}},
        {'timestamp': 0.4, 'command_type': 'joint_position', 'topic': '',
         'parameters': {'joint_names': ['joint_1', 'joint_2'], 'positions': [0.1, -0.1]}},
        {'timestamp': 0.5, 'command_type': 'set_goal', 'topic': '',
         'parameters': {'x': 1.0, 'y': 2.0, 'yaw': 0.5}},
    ]
    plan = prepare_commands(commands)
    if not plan:
        raise ValueError('Demo needs at least one command')
    received, complete = [], threading.Event()

    def collect(message):
        received.append(message.to_dict())
        if len(received) == len(plan):
            complete.set()

    with tempfile.TemporaryDirectory(prefix='yaskawa-demo-') as tmp:
        recording = Path(record) if record else Path(tmp) / 'messages.jsonl'
        if record and recording.exists():
            raise ValueError('Use a new recording path for a demo run')
        with JSONLRecorder(recording) as recorder, TCPROSServer(port=0, recorder=recorder) as broker:
            with TCPROSClient(port=broker.port) as subscriber, TCPROSClient(port=broker.port) as publisher:
                for topic in {command['topic'] for command in plan}:
                    subscriber.subscribe(topic, collect)
                scheduler = CommandScheduler(plan, speed)
                scheduler.on_command = lambda command: publisher.publish(command['topic'], command['message'])
                scheduler.start()
                try:
                    scheduler.wait()
                    if scheduler.error:
                        raise scheduler.error
                    if not complete.wait(5):
                        raise RuntimeError(f'Only received {len(received)}/{len(plan)} messages')
                    stats = broker.get_stats()
                finally:
                    scheduler.stop()
        saved = list(read_recording(recording))
        if len(saved) != len(plan):
            raise RuntimeError('Recording count does not match the command plan')
        return {'status': 'passed', 'planned': len(plan), 'received': len(received),
                'recorded': len(saved), 'automatic_stops': sum(c.get('automatic', False) for c in plan),
                'topics': stats['topics'], 'transport': 'loopback TCP', 'robot_connected': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', help='Use a CSV example instead of the built-in scenario')
    parser.add_argument('--speed', type=float, default=20.0)
    parser.add_argument('--record', help='Save JSONL to a new file')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run_demo(args.csv, args.speed, args.record), indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f'Demo failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
