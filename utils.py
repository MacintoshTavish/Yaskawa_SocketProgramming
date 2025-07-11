import logging
import sys
import time
from typing import Optional

def setup_logging(log_level: str, log_file: Optional[str] = None):
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=handlers
    )

def progress_bar(current: int, total: int, bar_length: int = 40):
    percent = float(current) / total if total else 0
    arrow = '-' * int(round(percent * bar_length) - 1) + '>' if percent > 0 else ''
    spaces = ' ' * (bar_length - len(arrow))
    sys.stdout.write(f'\rProgress: [{arrow}{spaces}] {int(percent * 100)}%')
    sys.stdout.flush()
    if current == total:
        print()

def safe_json_loads(s: str):
    import json
    try:
        return json.loads(s)
    except Exception as e:
        logging.error(f"JSON parse error: {e} in string: {s}")
        return None

def sleep_with_interrupt(seconds: float):
    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        pass 