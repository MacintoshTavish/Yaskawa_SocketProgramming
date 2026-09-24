"""Strict CSV ingestion: the whole file is checked before playback starts."""
import csv
import math
from pathlib import Path
from tcp_ros_program.protocol import loads_json

REQUIRED_COLUMNS = ['timestamp', 'command_type', 'topic', 'parameters']
OPTIONAL_COLUMNS = ['duration', 'priority', 'description']


class CSVValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('\n'.join(errors))


class CSVCommandParser:
    def __init__(self, filename, encoding='utf-8-sig', *, strict=True):
        self.filename = str(filename)
        self.encoding = encoding
        self.strict = strict
        self.commands = []
        self.errors = []

    def parse(self):
        self.commands, self.errors = [], []
        with open(self.filename, encoding=self.encoding, newline='') as stream:
            # csv.reader keeps quoted multiline fields intact. Comments are records,
            # not blindly removed physical lines inside quoted JSON/string fields.
            reader = csv.reader(stream, strict=True)
            columns = None
            try:
                for row in reader:
                    if not row or not any(v.strip() for v in row):
                        continue
                    if row[0].lstrip().startswith('#'):
                        continue
                    if columns is None:
                        columns = [v.strip() for v in row]
                        self._validate_columns(columns)
                        continue
                    try:
                        if len(row) != len(columns):
                            raise ValueError(f'Expected {len(columns)} columns, found {len(row)}; quote JSON with doubled quotes')
                        command = self._parse_row(dict(zip(columns, row)))
                        command['source'] = f'{Path(self.filename).name}:{reader.line_num}'
                        self.commands.append(command)
                    except (ValueError, TypeError) as exc:
                        self.errors.append(f'{self.filename}:{reader.line_num}: {exc}')
            except csv.Error as exc:
                self.errors.append(f'{self.filename}:{reader.line_num}: {exc}')
            if columns is None:
                raise CSVValidationError([f'{self.filename}: missing header row'])
        if self.errors and self.strict:
            self.commands = []
            raise CSVValidationError(self.errors)
        return list(self.commands)

    def _validate_columns(self, columns):
        missing = set(REQUIRED_COLUMNS) - set(columns)
        unknown = set(columns) - set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
        if missing or unknown or len(columns) != len(set(columns)):
            raise CSVValidationError([f'{self.filename}: invalid header; missing={sorted(missing)}, unknown={sorted(unknown)}, duplicate columns are not allowed'])

    @staticmethod
    def _nonnegative(value, field):
        result = float(value)
        if not math.isfinite(result) or result < 0:
            raise ValueError(f'{field} must be finite and nonnegative')
        return result

    def _parse_row(self, row):
        params = loads_json(row['parameters'])
        if not isinstance(params, dict):
            raise ValueError('parameters must be a JSON object')
        command_type = row['command_type'].strip()
        if not command_type:
            raise ValueError('command_type is required')
        return {
            'timestamp': self._nonnegative(row['timestamp'], 'timestamp'),
            'command_type': command_type,
            'topic': row['topic'].strip(),
            'parameters': params,
            'duration': self._nonnegative(row['duration'], 'duration') if row.get('duration', '').strip() else None,
            'priority': int(row['priority']) if row.get('priority', '').strip() else 0,
            'description': row.get('description', '').strip(),
        }
