"""Convert a complete command plan into validated ROS-shaped message objects."""
import math
import time
from .config import COMMAND_MAPPINGS
from tcp_ros_program.config import SUPPORTED_TOPICS
from tcp_ros_program.ros_messages import (Header, TwistMessage, PoseStampedMessage,
                                        StringMessage, LaserScanMessage,
                                        OdometryMessage, JointStateMessage)
from tcp_ros_program.validation import number, validate_message


def convert_command_to_ros(cmd, seq=0, timestamp=None, *, topics=None):
    ctype = cmd['command_type']
    mapping = COMMAND_MAPPINGS.get(ctype)
    if mapping is None:
        raise ValueError(f'Unsupported command_type: {ctype}')
    params = cmd['parameters']
    if not isinstance(params, dict):
        raise ValueError('parameters must be an object')
    missing = set(mapping['required_params']) - params.keys()
    unknown = params.keys() - set(mapping['required_params'] + mapping['optional_params'])
    if missing or unknown:
        raise ValueError(f'{ctype}: missing parameters {sorted(missing)}, unknown parameters {sorted(unknown)}')
    topic = cmd.get('topic') or mapping['default_topic']
    frame_id = params.get('frame_id', 'map' if ctype == 'set_goal' else '')
    if not isinstance(frame_id, str):
        raise ValueError('frame_id must be a string')
    header = Header(mapping['msg_type'], topic, seq, frame_id,
                    time.time() if timestamp is None else timestamp)
    if ctype in ('move', 'rotate', 'stop'):
        for key, value in params.items():
            number(value, key)
        if ctype == 'stop' and any(value != 0 for value in params.values()):
            raise ValueError('stop requires all velocities to be zero')
        msg = TwistMessage(**{key: params.get(key, 0.0) for key in (
            'linear_x', 'linear_y', 'linear_z', 'angular_x', 'angular_y', 'angular_z')}, header=header)
    elif ctype == 'set_goal':
        for key in ('x', 'y', 'z', 'yaw'):
            number(params.get(key, 0.0), key)
        yaw = params.get('yaw', 0.0)
        msg = PoseStampedMessage({k: params.get(k, 0.0) for k in ('x', 'y', 'z')},
                                 {'x': 0.0, 'y': 0.0, 'z': math.sin(yaw / 2), 'w': math.cos(yaw / 2)}, header)
    elif ctype == 'publish_string':
        if not isinstance(params['data'], str):
            raise ValueError('data must be a string')
        msg = StringMessage(params['data'], header)
    elif ctype == 'laser_scan':
        for key, value in params.items():
            if key == 'ranges':
                if not isinstance(value, list):
                    raise ValueError('ranges must be an array')
                for item in value:
                    number(item, 'ranges')
            else:
                number(value, key)
        msg = LaserScanMessage(**params, header=header)
    elif ctype == 'odometry':
        msg = OdometryMessage(**params, header=header)
    else:
        if not isinstance(params['joint_names'], list) or not isinstance(params['positions'], list):
            raise ValueError('joint_names and positions must be arrays')
        if len(params['positions']) != len(params['joint_names']):
            raise ValueError('A joint_position command needs one position per joint')
        for key in ('velocities', 'efforts'):
            if key in params and not isinstance(params[key], list):
                raise ValueError(f'{key} must be an array')
        msg = JointStateMessage(**params, header=header)
    validate_message(msg.to_dict(), SUPPORTED_TOPICS if topics is None else topics)
    return msg


def prepare_commands(commands, *, topics=None):
    """Validate all commands and insert duration stops without overriding later moves.

    Timestamps are seconds from playback start. Higher priorities run first at an
    equal timestamp; input order breaks remaining ties. Duration applies only to
    move/rotate. Other command durations are retained as descriptive metadata.
    """
    plan = []
    errors = []
    for index, original in enumerate(commands):
        command = dict(original)
        try:
            timestamp = number(command['timestamp'], 'timestamp')
            if timestamp < 0:
                raise ValueError('timestamp must be nonnegative')
            duration = command.get('duration')
            if duration is not None and number(duration, 'duration') < 0:
                raise ValueError('duration must be nonnegative')
            priority = command.get('priority') or 0
            if isinstance(priority, bool) or not isinstance(priority, int):
                raise ValueError('priority must be an integer')
            command['priority'] = priority
            msg = convert_command_to_ros(command, seq=index + 1, topics=topics)
            command['topic'] = msg.header.topic
            command['message'] = msg
            plan.append(command)
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            errors.append(f'{command.get("source", f"command {index + 1}")}: {exc}')
    if errors:
        raise ValueError('\n'.join(errors))
    plan.sort(key=lambda c: (c['timestamp'], -c['priority']))
    stops = []
    for index, command in enumerate(plan):
        if command['command_type'] not in ('move', 'rotate') or not command.get('duration'):
            continue
        end = command['timestamp'] + command['duration']
        if not math.isfinite(end):
            raise ValueError('timestamp + duration must be finite')
        later = next((c for c in plan[index + 1:] if c['topic'] == command['topic'] and
                      c['message'].header.msg_type == 'geometry_msgs/Twist'), None)
        if later is not None and later['timestamp'] <= end:
            continue
        stop = dict(command, timestamp=end, command_type='stop', parameters={}, duration=None,
                    description='Duration elapsed: zero velocity', automatic=True)
        stop['message'] = convert_command_to_ros(stop, topics=topics)
        stops.append(stop)
    return sorted(plan + stops, key=lambda c: (c['timestamp'], -c['priority']))
