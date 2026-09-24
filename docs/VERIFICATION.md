# Verification record

Local verification: 24 September 2026, macOS arm64, Python 3.13.5.

## Python application

Both repositories were installed together in a fresh virtual environment:

```bash
python -m pip install -e ../Yaskawa_json_to_ros -e ../Yaskawa_SocketProgramming
python -m unittest discover -s tests -v
```

The playback suite passes **23 tests**, covering CSV syntax and schema validation,
all example files, conversion, default topics, quaternion conversion, duration
stops, stable priority ordering, speed scaling, pause/resume, cancellation, error
propagation, dry run and summaries. Integration tests start actual local TCP
brokers and verify delivery and recording for every example CSV.

The companion broker suite passes **28 tests**. Its native ROS 2 suite is provided for a sourced ROS environment; native ROS
execution was not available in this session. The core suite runs without ROS.

The built-in demo verifies **5 planned / 5 received / 5 recorded** messages,
including one generated duration stop. Example plans contain 3 basic movement,
4 joint-position, 3 navigation and 3 sensor/status messages.

## Reproduction and evidence

```bash
yaskawa-demo
yaskawa-demo --csv examples/basic_movement.csv
yaskawa-demo --csv examples/joint_positions.csv
yaskawa-demo --csv examples/navigation_sequence.csv
yaskawa-demo --csv examples/sensor_commands.csv
```

The `ci/github-actions.yml` template defines package installation and testing on
Linux and Windows using Python 3.10, 3.12 and 3.13. It is not active: the available
GitHub credential cannot create workflow files. A workflow-capable credential can
activate it by copying it to `.github/workflows/ci.yml`. All documented local network runs
used loopback and OS-assigned ports; no physical robot was operated.
