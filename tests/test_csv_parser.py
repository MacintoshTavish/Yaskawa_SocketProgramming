import unittest
import tempfile
import os
from csv_ros_tcp_processor.csv_parser import CSVCommandParser

class TestCSVCommandParser(unittest.TestCase):
    def setUp(self):
        self.valid_csv = (
            'timestamp,command_type,topic,parameters,duration,priority,description\n'
            '0.0,move,/cmd_vel,"{\"linear_x\": 1.0, \"angular_z\": 0.0}",2.0,1,Move forward\n'
            '2.0,rotate,/cmd_vel,"{\"linear_x\": 0.0, \"angular_z\": 0.5}",1.5,1,Turn right\n'
            '# This is a comment\n'
            '\n'
            '3.5,stop,/cmd_vel,"{\"linear_x\": 0.0, \"angular_z\": 0.0}",0.1,2,Stop robot\n'
        )
        self.invalid_csv = (
            'timestamp,command_type,topic,parameters\n'
            'bad,move,/cmd_vel,"{\"linear_x\": 1.0, \"angular_z\": 0.0}"\n'
        )

    def test_valid_csv(self):
        with tempfile.NamedTemporaryFile('w+', delete=False) as f:
            f.write(self.valid_csv)
            fname = f.name
        parser = CSVCommandParser(fname)
        commands = parser.parse()
        os.unlink(fname)
        self.assertEqual(len(commands), 3)
        self.assertEqual(commands[0]['command_type'], 'move')
        self.assertEqual(commands[1]['command_type'], 'rotate')
        self.assertEqual(commands[2]['command_type'], 'stop')

    def test_invalid_csv(self):
        with tempfile.NamedTemporaryFile('w+', delete=False) as f:
            f.write(self.invalid_csv)
            fname = f.name
        parser = CSVCommandParser(fname)
        commands = parser.parse()
        os.unlink(fname)
        self.assertEqual(len(commands), 0)

    def test_missing_column(self):
        bad_csv = 'timestamp,command_type,parameters\n0.0,move,"{\"linear_x\": 1.0}"\n'
        with tempfile.NamedTemporaryFile('w+', delete=False) as f:
            f.write(bad_csv)
            fname = f.name
        parser = CSVCommandParser(fname)
        with self.assertRaises(ValueError):
            parser.parse()
        os.unlink(fname)

if __name__ == '__main__':
    unittest.main() 