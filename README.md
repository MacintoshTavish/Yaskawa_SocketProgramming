# Yaskawa CSV command playback

Validate timestamped CSV instructions, convert them into typed robotics messages,
play them over a TCP topic broker, and record a reproducible local demonstration.
The companion [JSON broker](https://github.com/MacintoshTavish/Yaskawa_json_to_ros)
provides the transport and an optional ROS 2 publishing adapter.

Python 3.10+ is required. The core runtime uses the Python standard library.

## Install both repositories

```bash
git clone https://github.com/MacintoshTavish/Yaskawa_json_to_ros.git
git clone https://github.com/MacintoshTavish/Yaskawa_SocketProgramming.git
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ./Yaskawa_json_to_ros -e ./Yaskawa_SocketProgramming
cd Yaskawa_SocketProgramming
```

On Windows activate with `.venv\Scripts\activate`. These packages are installed
from the checkouts; a PyPI release is not required.

## Run the complete local demo

```bash
yaskawa-demo
yaskawa-demo --csv examples/basic_movement.csv --record demo-messages.jsonl
```

The demo starts a broker on an OS-assigned loopback port, registers subscribers,
plays the commands, verifies receipt and the recording count, and shuts everything
down. It does not connect to a robot. A JSON result reports the observed counts.

## Validate and play a CSV

```bash
# Full validation and immediate JSON preview, with no network access:
yaskawa-playback --csv examples/basic_movement.csv --dry-run --summary validation.json

# Terminal 1:
yaskawa-broker --mode server --record messages.jsonl
# Terminal 2 (optional observer):
yaskawa-broker --mode subscribe --topic /cmd_vel
# Terminal 3:
yaskawa-playback --csv examples/basic_movement.csv --speed 1 --summary result.json
```

Use `--host`, `--port` or the legacy `--server host:port` to select the broker.
`--topics topics.json` extends the topic/type map; pass the same map to the broker.
Module entry points also work: `python -m csv_ros_tcp_processor` and
`python -m csv_ros_tcp_processor.demo`.

## Features

- Strict CSV and message validation before any connection or command is sent.
- Eight command types: move, rotate, stop, set_goal, publish_string, laser_scan,
  odometry and joint_position.
- Monotonic timing, playback speed, stable priority ordering, pause/resume/stop API.
- Duration-based zero-velocity messages for move/rotate commands.
- Bounded connection retries and broker acknowledgements; errors stop playback.
- Dry run, machine-readable summaries, loopback demo and JSONL recordings.
- Unit, network integration and cross-repository tests, plus a CI workflow template.

See [CSV format](docs/CSV_FORMAT.md), [architecture](docs/ARCHITECTURE.md),
[verification](docs/VERIFICATION.md) and [ITR technical material](docs/ITR_TECHNICAL_REPORT.md).


## Tests

```bash
python -m unittest discover -s tests -v
```

## Scope

This is a software communication and simulation project. Its custom JSON protocol
is not native ROS TCPROS, a Yaskawa controller protocol, a motion planner, or an
emergency-stop system. ROS 2 output requires the companion adapter and a sourced
ROS installation. JointState describes joint state; mapping it to an arm command
topic does not create a trajectory controller. All bundled motion examples are
for the local demo. Controller-specific integration requires a separate driver.
