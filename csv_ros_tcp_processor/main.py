"""Validate and play CSV command files through the companion TCP topic broker."""
import argparse
import json
import logging
import signal
import threading
from pathlib import Path
from .config import default_server_host, default_server_port
from .csv_parser import CSVCommandParser
from .command_converter import prepare_commands
from .command_scheduler import CommandScheduler
from .tcp_command_sender import TCPCommandSender
from .utils import setup_logging
from tcp_ros_program.validation import load_topics


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', required=True, help='Comma-separated CSV files; timestamps share one timeline')
    parser.add_argument('--host', default=default_server_host)
    parser.add_argument('--port', type=int, default=default_server_port)
    parser.add_argument('--server', help='Compatibility option: host:port')
    parser.add_argument('--speed', type=float, default=1.0)
    parser.add_argument('--topics', help='JSON file extending topic/type mappings')
    parser.add_argument('--dry-run', action='store_true', help='Print the validated plan immediately, without network access')
    parser.add_argument('--summary', help='Write execution results as JSON')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    parser.add_argument('--log-file')
    args = parser.parse_args(argv)
    setup_logging(args.log_level, args.log_file)
    sender = scheduler = None
    previous = {}
    cancelled = threading.Event()
    result = {'status': 'failed', 'planned': 0, 'completed': 0, 'dry_run': args.dry_run}
    code = 1
    try:
        host, port = args.host, args.port
        if args.server:
            host, separator, port_text = args.server.partition(':')
            if separator:
                port = int(port_text)
        if not host or not 1 <= port <= 65535:
            raise ValueError('A host and port between 1 and 65535 are required')
        topics = load_topics(args.topics)
        commands = []
        for filename in args.csv.split(','):
            commands.extend(CSVCommandParser(filename.strip()).parse())
        if not commands:
            raise ValueError('The CSV files contain no commands')
        plan = prepare_commands(commands, topics=topics)
        scheduler = CommandScheduler(plan, args.speed)
        result['planned'] = len(plan)
        if args.dry_run:
            for command in plan:
                print(json.dumps({'at_seconds': command['timestamp'] / args.speed,
                                  'command_type': command['command_type'],
                                  'automatic': command.get('automatic', False),
                                  'message': command['message'].to_dict()}, allow_nan=False))
            result['status'] = 'validated'
            code = 0
        else:
            if threading.current_thread() is threading.main_thread():
                for sig in (signal.SIGINT, signal.SIGTERM):
                    previous[sig] = signal.signal(sig, lambda *_: cancelled.set())
            sender = TCPCommandSender(host, port, topics=topics).connect()
            if cancelled.is_set():
                raise KeyboardInterrupt
            scheduler.on_command = lambda command: sender.send(command['topic'], command['message'])
            scheduler.start()
            while not scheduler.wait(timeout=0.1):
                if cancelled.is_set():
                    raise KeyboardInterrupt
            if scheduler.error:
                raise scheduler.error
            result.update(status='completed', completed=scheduler.progress)
            code = 0
    except KeyboardInterrupt:
        result['status'] = 'interrupted'
        code = 130
    except (OSError, ValueError, RuntimeError, ConnectionError, TimeoutError) as exc:
        result['error'] = str(exc)
        logging.error('%s', exc)
    finally:
        if scheduler:
            scheduler.stop()
            result['completed'] = scheduler.progress
        if sender:
            sender.disconnect()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        if args.summary:
            try:
                Path(args.summary).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
            except OSError as exc:
                logging.error('Cannot write summary: %s', exc)
                code = 1
        logging.info('%s: %s/%s commands', result['status'], result['completed'], result['planned'])
    return code


if __name__ == '__main__':
    raise SystemExit(main())
