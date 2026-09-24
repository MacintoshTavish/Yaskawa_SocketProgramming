import math
import unittest
from pathlib import Path
from csv_ros_tcp_processor.command_converter import convert_command_to_ros, prepare_commands
from csv_ros_tcp_processor.csv_parser import CSVCommandParser


def command(kind='move', timestamp=0, duration=None, params=None, **kwargs):
    return dict(command_type=kind, timestamp=timestamp, duration=duration,
                parameters={'linear_x': 1.0, 'angular_z': 0.0} if params is None else params,
                **kwargs)


class ConversionTests(unittest.TestCase):
    def test_every_example_preflights(self):
        for path in (Path(__file__).resolve().parents[1] / 'examples').glob('*.csv'):
            with self.subTest(path=path):
                plan = prepare_commands(CSVCommandParser(path).parse())
                self.assertTrue(plan)
                self.assertTrue(all(c['message'].header.topic == c['topic'] for c in plan))

    def test_goal_yaw_frame_sequence_timestamp(self):
        msg = convert_command_to_ros(command('set_goal', params={'x': 1, 'y': 2, 'yaw': math.pi, 'frame_id': 'world'}), seq=7, timestamp=123)
        self.assertAlmostEqual(msg.orientation['z'], 1)
        self.assertEqual(msg.header.frame_id, 'world')
        self.assertEqual(msg.header.seq, 7)
        self.assertEqual(msg.header.timestamp, 123)
        self.assertEqual(msg.header.topic, '/move_base_simple/goal')

    def test_rejects_invalid_command_semantics(self):
        invalid = [command('unknown'), command(params={'linear_x': True, 'angular_z': 0}),
                   command(params={'linear_x': float('inf'), 'angular_z': 0}),
                   command(params={'linear_x': 1, 'angular_z': 0, 'typo': 1}),
                   command('stop', params={'linear_x': 1}),
                   command('joint_position', params={'joint_names': ['a', 'b'], 'positions': [1]}),
                   command('publish_string', params={'data': 123}),
                   command(topic='/chatter')]
        for item in invalid:
            with self.subTest(command=item), self.assertRaises(ValueError):
                prepare_commands([item])

    def test_duration_generates_stop_only_when_not_superseded(self):
        plan = prepare_commands([command(duration=2)])
        self.assertEqual([c['timestamp'] for c in plan], [0, 2])
        self.assertEqual(plan[-1]['command_type'], 'stop')
        self.assertEqual(plan[-1]['message'].linear['x'], 0)
        plan = prepare_commands([command(duration=3), command(timestamp=1, duration=1)])
        self.assertEqual([c['timestamp'] for c in plan], [0, 1, 2])
        self.assertEqual(len([c for c in plan if c.get('automatic')]), 1)

    def test_equal_timestamp_priorities_and_stable_order(self):
        plan = prepare_commands([command(priority=1, description='first'),
                                 command(priority=2, description='second'),
                                 command(priority=1, description='third')])
        self.assertEqual([c['description'] for c in plan], ['second', 'first', 'third'])

    def test_preflight_aggregates_errors(self):
        with self.assertRaises(ValueError) as error:
            prepare_commands([command('bad', source='a.csv:2'), command('also_bad', source='b.csv:3')])
        self.assertIn('a.csv:2', str(error.exception))
        self.assertIn('b.csv:3', str(error.exception))
