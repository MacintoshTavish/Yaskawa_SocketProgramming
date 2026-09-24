"""Logging helpers for the command-line application."""
import logging
import sys


def setup_logging(log_level, log_file=None):
    handlers = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    logging.basicConfig(level=getattr(logging, log_level.upper()),
                        format='%(levelname)s %(name)s: %(message)s', handlers=handlers)
