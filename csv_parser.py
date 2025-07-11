import csv
import logging
from typing import List, Dict, Any, Optional
from .utils import safe_json_loads

REQUIRED_COLUMNS = ['timestamp', 'command_type', 'topic', 'parameters']

class CSVCommandParser:
    def __init__(self, filename: str, encoding: str = 'utf-8'):
        self.filename = filename
        self.encoding = encoding
        self.commands: List[Dict[str, Any]] = []

    def parse(self) -> List[Dict[str, Any]]:
        with open(self.filename, encoding=self.encoding) as f:
            reader = csv.DictReader(self._skip_comments(f))
            self._validate_columns(list(reader.fieldnames) if reader.fieldnames else None)
            for i, row in enumerate(reader):
                if not any(row.values()):
                    continue  # skip empty lines
                try:
                    cmd = self._parse_row(row, i)
                    if cmd:
                        self.commands.append(cmd)
                except Exception as e:
                    logging.error(f"Row {i+2} parse error: {e}")
        return self.commands

    def _skip_comments(self, f):
        for line in f:
            if line.strip().startswith('#') or not line.strip():
                continue
            yield line

    def _validate_columns(self, columns: Optional[List[str]]):
        if not columns:
            raise ValueError("CSV file missing header row.")
        for col in REQUIRED_COLUMNS:
            if col not in columns:
                raise ValueError(f"Missing required column: {col}")

    def _parse_row(self, row: Dict[str, str], row_idx: int) -> Optional[Dict[str, Any]]:
        # Parse and validate each field
        cmd = {}
        try:
            cmd['timestamp'] = float(row['timestamp'])
        except Exception:
            raise ValueError(f"Invalid timestamp: {row['timestamp']}")
        cmd['command_type'] = row['command_type'].strip()
        cmd['topic'] = row['topic'].strip()
        params = safe_json_loads(row['parameters'])
        if params is None:
            raise ValueError(f"Invalid JSON in parameters: {row['parameters']}")
        cmd['parameters'] = params
        # Optional fields
        cmd['duration'] = float(row['duration']) if row.get('duration') else None
        cmd['priority'] = int(row['priority']) if row.get('priority') else None
        cmd['description'] = row.get('description', '').strip() if row.get('description') else ''
        return cmd 