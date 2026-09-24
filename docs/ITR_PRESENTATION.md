# Ten-minute ITR presentation outline

Use the final department-approved slide template and certified student/company
information. The technical narrative below follows the actual source and test
results.

| Slide | Time | Main message and supporting visual |
|---|---:|---|
| 1. Project title and context | 0:30 | CSV-Driven Robotics Communication Using TCP, JSON and ROS 2; student and certified training details |
| 2. Problem and objectives | 0:50 | Repeatable commands need validation, message boundaries and observable delivery |
| 3. Architecture | 1:10 | CSV → conversion → scheduler → broker → subscriber/ROS; show the architecture diagram |
| 4. Command representation | 1:00 | One CSV row and its resulting Twist JSON; explain quoting, units and topic mapping |
| 5. TCP protocol and routing | 1:10 | Four-byte prefix, payload, subscriptions and broker acknowledgements |
| 6. Timing and reliability | 1:00 | Monotonic deadlines, speed, pause/resume, duration stops and bounded queues |
| 7. Demonstration | 1:30 | Run yaskawa-demo and show matching planned/received/recorded counts and one JSONL record |
| 8. Verification | 1:10 | Unit tests, actual loopback integration, native ROS test design and representative edge cases |
| 9. Learning and impact | 1:00 | Protocol design, concurrency, testing and the 100-word impact note's main points |
| 10. Conclusion and next steps | 0:40 | Reproducible software pipeline and the separate work needed for controller integration |

Total: 10 minutes. Keep two minutes available for viva, as stated in the supplied
ITR guidelines. Use measured outputs from the exact presentation commit.

## Demo script

```bash
yaskawa-playback --csv examples/basic_movement.csv --dry-run
yaskawa-demo --csv examples/basic_movement.csv --record presentation-demo.jsonl
python -m unittest discover -s tests -v
```

Use a fresh recording filename. A prepared terminal recording is a useful fallback
if the presentation computer lacks the environment. Label it with the actual run
and commit. Only show native ROS output after running the ROS adapter in a real ROS
environment; the basic local demo does not require ROS.

## Viva preparation

**Why add a length prefix to TCP?** TCP delivers bytes, so a send may be split
across reads or combined with another send. The prefix tells the receiver exactly
how many bytes belong to one JSON message.

**Why validate the complete plan before connecting?** A later invalid command should
not be discovered after part of the plan has already been sent.

**Why use a monotonic clock?** Elapsed playback time should not change when the
system's wall clock is adjusted.

**What does publish success prove?** Broker acceptance. It does not establish that
a subscriber processed the data or an actuator moved.

**How does the application handle reconnection?** Connection attempts are bounded.
Explicit reconnection restores subscriptions. Potentially accepted commands are
not automatically replayed.

**Is this native ROS TCPROS or a Yaskawa driver?** No. It is a custom JSON broker
with an optional adapter that creates native ROS 2 publishers.

**What is the role of JointState?** It describes named joint values. A driver may
require trajectory messages or action goals to command a physical arm.

**How can it be extended?** Add a message class, schema validation, tests and any
necessary native conversion; separately integrate a controller-specific driver and
verify that integration with suitable equipment and supervision.
