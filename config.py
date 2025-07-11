"""
Configuration for CSV to ROS TCP Command Processor
"""

# TCP server connection
default_server_host = 'localhost'
default_server_port = 8888

# Timing
playback_speed = 1.0  # 1.0 = real time
max_queue_size = 1000

# Logging
log_level = 'INFO'
log_file = 'csv_ros_tcp_processor.log'

# Validation
validate_parameters = True

# Error handling
retry_attempts = 3
retry_delay = 2.0  # seconds

# Supported command mappings
COMMAND_MAPPINGS = {
    'move': {
        'msg_type': 'geometry_msgs/Twist',
        'default_topic': '/cmd_vel',
        'required_params': ['linear_x', 'angular_z'],
        'optional_params': ['linear_y', 'angular_x', 'angular_y']
    },
    'rotate': {
        'msg_type': 'geometry_msgs/Twist',
        'default_topic': '/cmd_vel',
        'required_params': ['angular_z'],
        'optional_params': ['linear_x', 'linear_y']
    },
    'stop': {
        'msg_type': 'geometry_msgs/Twist',
        'default_topic': '/cmd_vel',
        'required_params': [],
        'optional_params': ['linear_x', 'angular_z', 'linear_y', 'angular_x', 'angular_y']
    },
    'set_goal': {
        'msg_type': 'geometry_msgs/PoseStamped',
        'default_topic': '/move_base_simple/goal',
        'required_params': ['x', 'y'],
        'optional_params': ['z', 'yaw', 'frame_id']
    },
    'publish_string': {
        'msg_type': 'std_msgs/String',
        'default_topic': '/robot_status',
        'required_params': ['data'],
        'optional_params': []
    },
    'laser_scan': {
        'msg_type': 'sensor_msgs/LaserScan',
        'default_topic': '/scan',
        'required_params': ['ranges', 'angle_min', 'angle_max', 'angle_increment', 'time_increment', 'scan_time', 'range_min', 'range_max'],
        'optional_params': []
    },
    'odometry': {
        'msg_type': 'nav_msgs/Odometry',
        'default_topic': '/odom',
        'required_params': ['pose', 'twist'],
        'optional_params': []
    },
    'joint_position': {
        'msg_type': 'sensor_msgs/JointState',
        'default_topic': '/arm_controller/command',
        'required_params': ['joint_names', 'positions'],
        'optional_params': ['velocities', 'efforts']
    }
} 