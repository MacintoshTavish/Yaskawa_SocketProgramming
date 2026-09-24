"""Delivery adapter: a successful send means the broker acknowledged acceptance."""
import logging
from .config import default_server_host, default_server_port, retry_attempts, retry_delay
from tcp_ros_program.tcp_client import TCPROSClient


class TCPCommandSender:
    def __init__(self, host=default_server_host, port=default_server_port, dry_run=False, *, topics=None):
        self.host, self.port = host, port
        self.dry_run = dry_run
        self.topics = topics
        self.client = None
        self.connected = False
        self.logger = logging.getLogger(__name__)

    def connect(self):
        if not self.dry_run:
            self.client = TCPROSClient(self.host, self.port, topics=self.topics,
                                       connect_attempts=retry_attempts, retry_delay=retry_delay)
            self.client.connect()
            self.connected = True
        return self

    def send(self, topic, msg):
        if self.dry_run:
            self.logger.info('[DRY RUN] %s %s', topic, msg.to_dict())
            return True
        if not self.connected or self.client is None:
            raise ConnectionError('Sender is not connected')
        return self.client.publish(topic, msg)

    def disconnect(self):
        if self.client:
            self.client.disconnect()
        self.connected = False
