# CSV command format

Required header: `timestamp,command_type,topic,parameters`.
Optional columns: `duration,priority,description`. Unknown/duplicate columns and
malformed rows are errors. UTF-8 with an optional BOM is supported. Blank records
and records starting with `#` are skipped; quoted multiline fields stay intact.

`parameters` is a JSON object inside a CSV field. Use doubled CSV quotes:

```csv
timestamp,command_type,topic,parameters,duration,priority,description
0.0,move,/cmd_vel,"{""linear_x"":0.25,""angular_z"":0.0}",2.0,1,Forward in local demo
2.0,stop,/cmd_vel,{},,2,Zero velocity
```

Generate CSV with `csv.writer` and parameters with `json.dumps` instead of manually
escaping nested quotes. JSON backslash escaping alone does not quote a CSV field.

## Commands

| Command | Required JSON keys | Default topic |
|---|---|---|
| move | linear_x, angular_z | /cmd_vel |
| rotate | angular_z | /cmd_vel |
| stop | none; supplied velocity values must all be zero | /cmd_vel |
| set_goal | x, y | /move_base_simple/goal |
| publish_string | data (string) | /robot_status |
| laser_scan | ranges, angle_min, angle_max, angle_increment, time_increment, scan_time, range_min, range_max | /scan |
| odometry | pose, twist | /odom |
| joint_position | joint_names, positions | /arm_controller/command |

Move/rotate/stop accept the six components `linear_x/y/z` and `angular_x/y/z`.
Missing optional components are zero. Set-goal accepts `z`, `yaw` and `frame_id`;
yaw is in radians and becomes a unit quaternion. Its default frame is `map`.
Joint-position accepts optional `velocities` and `efforts`; arrays must match the
joint count or be empty. Odometry uses pose `{position,orientation}` and twist
`{linear,angular}`. See the examples for complete payloads.

Empty topic fields choose the command's default. Explicit topics must map to the
same message type. Numeric values must be finite; booleans, NaN and Infinity are
not accepted as movement parameters. Positions/angles use the units expected by
the consuming ROS graph, conventionally metres and radians. No unit conversion
or controller-specific limit checking is performed.

## Timing and ordering

Timestamps are nonnegative seconds from playback start. A first timestamp of 2.0
waits two seconds at speed 1.0. A speed of 2.0 halves scheduled delays. All files
passed through `--csv a.csv,b.csv` share one timeline, then commands are sorted by
timestamp, descending priority and stable input order. Priority controls ordering
at equal timestamps; it does not preempt an earlier command or change final state.

A positive `duration` on move/rotate inserts a zero-velocity command at
`timestamp + duration`. A subsequent Twist on that topic at or before expiry
supersedes the timer so a stale stop does not interrupt the newer command. Duration
on other command types is descriptive metadata: it does not interpolate joints,
wait for goals or delay later commands. Omitted/zero motion durations generate no
stop; include explicit stops in such plans.

Pause/resume freezes the schedule's elapsed time and shifts future deadlines. It
does not stop a physical actuator or retract an already sent command. `stop()`
ends future scheduling; a callback already in progress may finish. Playback waits
for broker acknowledgements, so a slow network can make messages late. This is
best-effort timed playback, not a real-time controller.

## Validation and failures

The CLI parses and converts the complete plan before opening a socket. Invalid
input rejects the entire run with source file/row information. Library users can
request `CSVCommandParser(..., strict=False)` for an import-preview workflow, then
inspect `.errors`; the CLI always uses strict mode.

The CLI exits 0 for a completed run or valid dry run, 1 for validation/connection/
delivery failures, 2 for argparse usage errors, and 130 for interruption. A summary
contains status, planned count, completed/acknowledged count, dry-run state and any
error. A dry run validates but executes zero commands. Failure stops subsequent
commands; it does not claim that the last command was never received.
