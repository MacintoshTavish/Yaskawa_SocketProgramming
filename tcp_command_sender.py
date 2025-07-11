import logging
import time
from typing import Any, Dict, Optional
from .config import default_server_host, default_server_port, retry_attempts, retry_delay
from tcp_ros_program.tcp_client import TCPROSClient

class TCPCommandSender:
    def __init__(self, host: str = default_server_host, port: int = default_server_port, dry_run: bool = False):
        self.host = host
        self.port = port
        self.dry_run = dry_run
        self.client: Optional[TCPROSClient] = None
        self.connected = False
        self.logger = logging.getLogger('TCPCommandSender')

    def connect(self):
        if self.dry_run:
            self.logger.info("Dry run mode: not connecting to server.")
            return
        for attempt in range(retry_attempts):
            try:
                self.client = TCPROSClient(self.host, self.port)
                self.client.connect()
                self.connected = True
                self.logger.info(f"Connected to TCP ROS server at {self.host}:{self.port}")
                return
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt+1} failed: {e}")
                time.sleep(retry_delay)
        raise ConnectionError(f"Failed to connect to TCP ROS server at {self.host}:{self.port}")

    def send(self, topic: str, msg: Any):
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would send to {topic}: {msg}")
            return True
        if not self.connected or not self.client:
            self.logger.error("Not connected to server.")
            return False
        try:
            self.client.publish(topic, msg)
            self.logger.info(f"Sent message to {topic}: {msg}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message to {topic}: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.disconnect()
            self.connected = False
            self.logger.info("Disconnected from TCP ROS server.") 