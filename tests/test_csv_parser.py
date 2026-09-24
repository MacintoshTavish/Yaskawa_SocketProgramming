import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from csv_ros_tcp_processor.csv_parser import CSVCommandParser, CSVValidationError


class CSVParserTests(unittest.TestCase):
    def parse_text(self, text, **kwargs):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / 'commands.csv'
        path.write_text(text, encoding='utf-8')
        parser = CSVCommandParser(path, **kwargs)
        return parser, parser.parse()

    def test_valid_json_quoting_comments_bom_and_repeat_parse(self):
        stream = io.StringIO()
        stream.write('\ufeff# Comment before header\n')
        writer = csv.writer(stream)
        writer.writerow(['timestamp', 'command_type', 'topic', 'parameters'])
        writer.writerow([0, 'publish_string', '', json.dumps({'data': 'Hello, "robot"'})])
        stream.write('\n# Another comment\n')
        parser, commands = self.parse_text(stream.getvalue())
        self.assertEqual(commands[0]['parameters']['data'], 'Hello, "robot"')
        self.assertEqual(parser.parse(), commands)
        self.assertEqual(len(parser.commands), 1)

    def test_multiline_description_preserves_comment_like_text(self):
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(['timestamp', 'command_type', 'topic', 'parameters', 'description'])
        writer.writerow([0, 'stop', '/cmd_vel', '{}', 'line 1\n# not a comment\nline 3'])
        _, commands = self.parse_text(stream.getvalue())
        self.assertIn('# not a comment', commands[0]['description'])

    def test_invalid_rows_fail_entire_file(self):
        text = 'timestamp,command_type,topic,parameters\n0,stop,/cmd_vel,{}\nbad,stop,/cmd_vel,{}\n'
        with self.assertRaises(CSVValidationError) as error:
            self.parse_text(text)
        self.assertIn(':3:', str(error.exception))
        parser, commands = self.parse_text(text, strict=False)
        self.assertEqual(len(commands), 1)
        self.assertEqual(len(parser.errors), 1)

    def test_invalid_fields(self):
        for row in ('nan,stop,/cmd_vel,{}', '-1,stop,/cmd_vel,{}', '0,stop,/cmd_vel,[]',
                    '0,stop,/cmd_vel,{},extra', '0,,/cmd_vel,{}', '0,stop,/cmd_vel,"unterminated'):
            with self.subTest(row=row), self.assertRaises(CSVValidationError):
                self.parse_text('timestamp,command_type,topic,parameters\n' + row)

    def test_missing_duplicate_and_unknown_columns(self):
        for header in ('timestamp,command_type,parameters', 'timestamp,command_type,topic,parameters,topic',
                       'timestamp,command_type,topic,parameters,typo'):
            with self.subTest(header=header), self.assertRaises(CSVValidationError):
                self.parse_text(header + '\n')

    def test_all_repository_examples_parse(self):
        for path in (Path(__file__).resolve().parents[1] / 'examples').glob('*.csv'):
            with self.subTest(path=path):
                self.assertGreater(len(CSVCommandParser(path).parse()), 0)
