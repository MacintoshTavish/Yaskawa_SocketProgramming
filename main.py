import argparse
import logging
import sys
from .config import log_level, log_file, playback_speed
from .utils import setup_logging, progress_bar
from .csv_parser import CSVCommandParser
from .command_converter import convert_command_to_ros
from .command_scheduler import CommandScheduler
from .tcp_command_sender import TCPCommandSender

def main():
    parser = argparse.ArgumentParser(description='CSV to ROS TCP Command Processor')
    parser.add_argument('--csv', required=True, help='CSV file(s) with robot commands (comma-separated)')
    parser.add_argument('--server', default=None, help='TCP server host:port (default from config)')
    parser.add_argument('--speed', type=float, default=playback_speed, help='Playback speed (1.0 = real time)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no network)')
    parser.add_argument('--log-level', default=log_level, help='Logging level')
    parser.add_argument('--log-file', default=log_file, help='Log file path')
    args = parser.parse_args()

    setup_logging(args.log_level, args.log_file)
    logging.info('Starting CSV to ROS TCP Command Processor')

    # Parse CSV files
    csv_files = [f.strip() for f in args.csv.split(',')]
    all_commands = []
    for csv_file in csv_files:
        parser = CSVCommandParser(csv_file)
        commands = parser.parse()
        all_commands.extend(commands)
    if not all_commands:
        logging.error('No valid commands found in CSV file(s).')
        sys.exit(1)
    all_commands.sort(key=lambda c: c['timestamp'])

    # TCP sender
    host, port = None, None
    if args.server:
        if ':' in args.server:
            host, port = args.server.split(':')
            port = int(port)
        else:
            host = args.server
    sender_kwargs = {'dry_run': args.dry_run}
    if host is not None:
        sender_kwargs['host'] = host
    if port is not None:
        sender_kwargs['port'] = port
    sender = TCPCommandSender(**sender_kwargs)
    if not args.dry_run:
        try:
            sender.connect()
        except Exception as e:
            logging.error(f'Failed to connect to server: {e}')
            sys.exit(1)

    # Command scheduler
    scheduler = CommandScheduler(all_commands, speed=args.speed)
    total = len(all_commands)

    def on_command(cmd):
        try:
            msg = convert_command_to_ros(cmd)
            sender.send(cmd['topic'], msg)
        except Exception as e:
            logging.error(f'Command conversion/sending failed: {e}')

    def on_progress(progress, total):
        progress_bar(progress, total)

    scheduler.on_command = on_command
    scheduler.on_progress = on_progress

    try:
        scheduler.start()
        while scheduler.is_running():
            pass
    except KeyboardInterrupt:
        logging.info('Interrupted by user. Stopping...')
        scheduler.stop()
    finally:
        sender.disconnect()
        logging.info('Done.')

if __name__ == '__main__':
    main() 