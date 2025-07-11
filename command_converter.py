import logging
from typing import Dict, Any, Optional
from .config import COMMAND_MAPPINGS

# Import ROS message classes from the previous tcp_ros_program package
from tcp_ros_program.ros_messages import (
    TwistMessage, PoseStampedMessage, StringMessage, LaserScanMessage, OdometryMessage, JointStateMessage
)

def convert_command_to_ros(cmd: Dict[str, Any], seq: int = 0, timestamp: Optional[float] = None):
    ctype = cmd['command_type']
    mapping = COMMAND_MAPPINGS.get(ctype)
    if not mapping:
        raise ValueError(f"Unsupported command_type: {ctype}")
    msg_type = mapping['msg_type']
    params = cmd['parameters']
    # Validate required params
    for p in mapping.get('required_params', []):
        if p not in params:
            raise ValueError(f"Missing required parameter '{p}' for command_type '{ctype}'")
    # Map to ROS message
    if msg_type == 'geometry_msgs/Twist':
        return TwistMessage(
            linear_x=params.get('linear_x', 0.0),
            linear_y=params.get('linear_y', 0.0),
            linear_z=params.get('linear_z', 0.0),
            angular_x=params.get('angular_x', 0.0),
            angular_y=params.get('angular_y', 0.0),
            angular_z=params.get('angular_z', 0.0),
        )
    elif msg_type == 'geometry_msgs/PoseStamped':
        position = {
            'x': params.get('x', 0.0),
            'y': params.get('y', 0.0),
            'z': params.get('z', 0.0),
        }
        # Convert yaw to quaternion if present
        orientation = {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
        if 'yaw' in params:
            import math
            yaw = float(params['yaw'])
            orientation['z'] = math.sin(yaw / 2.0)
            orientation['w'] = math.cos(yaw / 2.0)
        return PoseStampedMessage(position, orientation)
    elif msg_type == 'std_msgs/String':
        return StringMessage(params.get('data', ''))
    elif msg_type == 'sensor_msgs/LaserScan':
        return LaserScanMessage(
            ranges=params['ranges'],
            angle_min=params['angle_min'],
            angle_max=params['angle_max'],
            angle_increment=params['angle_increment'],
            time_increment=params['time_increment'],
            scan_time=params['scan_time'],
            range_min=params['range_min'],
            range_max=params['range_max'],
        )
    elif msg_type == 'nav_msgs/Odometry':
        return OdometryMessage(
            pose=params['pose'],
            twist=params['twist'],
        )
    elif msg_type == 'sensor_msgs/JointState':
        return JointStateMessage(
            joint_names=params['joint_names'],
            positions=params['positions'],
            velocities=params.get('velocities', []),
            efforts=params.get('efforts', [])
        )
    else:
        raise ValueError(f"Unsupported ROS message type: {msg_type}") 