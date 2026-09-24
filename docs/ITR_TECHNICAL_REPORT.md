# CSV-Driven Robotics Communication Using TCP, JSON and ROS 2

Technical report material for the Industrial Training Report (ITR), School of
Computer Engineering, Manipal Institute of Technology. This chapter documents the
repository implementation and reproducible software results. Institutional front
matter, internship dates and certified training details belong in the final report
from the student's official records.

## Abstract

Robotics applications often need a repeatable way to describe commands, exchange
structured data and observe the resulting message flow. This project provides a
Python system that reads timestamped commands from CSV, validates their syntax and
meaning, converts them into robotics message objects and sends them through a TCP
topic broker. The broker uses length-prefixed JSON frames, typed subscriptions,
acknowledgements and bounded queues. Accepted messages can be recorded as JSONL.
An optional adapter publishes selected data into a native ROS 2 graph. A local demo
combines both repositories and verifies message delivery without requiring robot
hardware. Automated tests exercise serialization, malformed input, network framing,
concurrent clients, timing and complete CSV playback. The project demonstrates
application protocols, modular software design and evidence-based verification.

## 1. Introduction and problem statement

A command script is useful only when its timing, payload and destination are
unambiguous. CSV is convenient for authoring a sequence, but a raw row does not
identify whether a parameter is valid for a particular robotics message. TCP
provides an ordered byte stream, but it does not preserve application message
boundaries. A receiver must therefore reconstruct frames, validate contents and
route each message to the intended consumer.

The objective is to build a reproducible communication pipeline that separates
command authoring, validation, scheduling, transport and middleware integration.
A local execution mode makes these concepts demonstrable during a presentation
without relying on access to a physical controller. The implementation is related
to robotics software development; it does not claim native Yaskawa controller
compatibility or proof of physical robot operation.

## 2. Objectives and scope

The main objectives are to accept a readable command plan, reject invalid input
before sending, preserve explicit timing and topic information, deliver typed
messages to subscribers, capture accepted traffic and expose a controlled path
into ROS 2. Reproducible installation and automated verification support maintenance
and technical evaluation.

Supported commands are move, rotate, stop, set-goal, publish-string, laser-scan,
odometry and joint-position. The communication library contains seven message
representations; six can be converted into native ROS 2 messages. Image support is
metadata-only. Motion planning, collision avoidance, hardware interlocks, controller
protocols and safety certification are outside the implemented software boundary.

## 3. System design

The system consists of two companion repositories. `Yaskawa_SocketProgramming`
provides the CSV application. `Yaskawa_json_to_ros` provides message models and the
TCP broker. The application depends on the broker package, ensuring that both ends
share the same schema and topic configuration.

The data path is CSV → parser → whole-plan validation → message conversion →
monotonic scheduler → TCP client → topic broker → subscriber or ROS 2 adapter.
A parallel recording path stores accepted envelopes. The architecture diagram in
`ARCHITECTURE.md` can be used as a figure in the final report.

Each wire frame has a four-byte network-order length prefix followed by a UTF-8
JSON object. The envelope header carries message type, topic, Unix timestamp,
sequence number and coordinate frame. Its payload contains the type-specific data.
Subscriptions and acknowledgements are small control frames on the same connection.
The protocol definition is published in the companion repository.

## 4. Implementation

### 4.1 Input validation and conversion

The parser uses Python's CSV reader so quoted commas and multiline fields are
handled correctly. JSON parameters are decoded strictly. The parser records source
locations and reports invalid rows. Conversion then checks required and unknown
parameters, finite numeric values, topic/type compatibility and structured payloads.
A malformed plan fails before a network connection is opened.

Twist commands create linear and angular vectors. A set-goal command combines a
position with a yaw-derived quaternion, using sin(yaw/2) and cos(yaw/2) for the z
and w components. Joint-position commands require unique names and matching position
arrays. Shared validation prevents the CSV layer and network layer from accepting
different shapes for the same message type.

### 4.2 Timing and command lifecycle

The scheduler measures elapsed time with a monotonic clock. A command timestamp is
relative to playback start, and its deadline is divided by the playback speed.
Pause time is excluded from elapsed playback time. A threading Condition provides
interruptible waits and avoids continuously polling the CPU.

For a positive move/rotate duration, the plan includes a later zero-velocity command.
A subsequent Twist command on the same topic supersedes an earlier duration timer.
This prevents a stale stop from interrupting a newer command. Other durations remain
metadata and do not imply a trajectory or a completed navigation goal.

### 4.3 TCP communication and concurrency

A broker accept thread creates reader and writer workers for each client. Outgoing
frames use bounded queues, so a slow reader cannot block writes to every client.
The client serializes each complete outgoing frame under a lock. Its listener
handles acknowledgements while a separate dispatcher invokes user callbacks.

Subscription registration is acknowledged before the client continues. A successful
publish means the broker accepted the message, not that a robot executed it. Lost
acknowledgements leave delivery uncertain, so motion commands are not automatically
resent. Connection attempts are bounded and shutdown wakes pending requests.

### 4.4 Recording and observability

The optional recorder appends one validated envelope per JSONL line and flushes
accepted writes. A reader restores typed objects for inspection. Broker topic
counters, rejected-message counters, callback errors and playback summaries expose
the observed behavior. The local demo checks that planned, received and recorded
counts agree.

### 4.5 ROS 2 adapter

The optional adapter creates native ROS 2 publishers only for an explicit topic
map. Example destinations are placed under `/itr_demo/`. It converts vectors,
quaternions, timestamps and joint arrays into the corresponding ROS classes.
Odometry covariance is not carried by this wire format; native arrays retain their
defaults. Image metadata is not enough to form a native image and is not bridged.
A JointState payload represents state, not a complete motion trajectory.

## 5. Verification methodology and results

Verification has three layers: isolated unit tests, real loopback TCP integration,
and native ROS 2 conversion/delivery tests in a ROS environment. Python tests use
the standard-library unittest framework. Each local broker uses an OS-assigned
port, avoiding interference with a running application.

The test cases include fragmented and coalesced frames, malformed JSON and UTF-8,
oversize payloads, partial-frame timeout, duplicate callback prevention, concurrent
publishers, reconnection, recording, strict CSV validation and scheduling at multiple
speeds. Every bundled CSV is passed through a real TCP broker and subscriber.
`VERIFICATION.md` records actual test counts and commands; a CI workflow template defines further platform and native ROS checks.

The default demonstration produces five accepted, received and recorded messages,
including an automatically inserted stop. These are software communication results.
They are not measurements of actuator accuracy, network latency in a factory,
energy savings or physical robot reliability. Such claims require separate
experiments and recorded equipment details.

## 6. Engineering decisions and lessons

Separating parser, scheduler, transport and middleware conversion made it possible
to test behavior at each boundary. Whole-plan validation avoids partial execution
caused by a later malformed row. Explicit framing addresses TCP's stream semantics.
Monotonic timing avoids wall-clock adjustments. Bounded queues define a clear
response to slow consumers. Acknowledgements improve observability while requiring
careful distinction between message acceptance and physical execution.

Packaging and automated test commands make the project repeatable beyond the original
workstation. Technical documentation explains both the behavior and its limits,
which is necessary for others to assess and extend a robotics communication system.

## 7. Conclusion

The repositories form a runnable, tested software pipeline from structured command
files to topic-based messaging and optional ROS 2 output. The local demo makes the
main functionality reproducible, and the tests provide evidence for framing,
validation, timing and delivery behavior. The design creates a practical foundation
for future controller-specific integration while keeping the current results tied
to software experiments that can be repeated.

## Environmental and societal impact — 100 words

This project supports responsible robotics development by allowing communication
workflows to be tested without repeatedly operating physical equipment. Local
simulation and command validation can reduce avoidable trial runs, material waste,
and equipment wear when integrated into a supervised engineering process. Clear
logging improves traceability and helps learners understand failures before deployment.
The software also encourages reusable interfaces and accessible technical education
through documented examples and automated tests. However, environmental benefits
depend on actual deployment practices and were not measured here. Human supervision,
appropriate safety systems, and transparent reporting remain essential when adapting
this communication prototype for industrial or educational use.

## References

1. Project source: https://github.com/MacintoshTavish/Yaskawa_SocketProgramming
2. Companion source: https://github.com/MacintoshTavish/Yaskawa_json_to_ros
3. Python socket documentation: https://docs.python.org/3/library/socket.html
4. Python CSV documentation: https://docs.python.org/3/library/csv.html
5. Python threading documentation: https://docs.python.org/3/library/threading.html
6. ROS 2 common interfaces: https://github.com/ros2/common_interfaces/tree/jazzy
7. ROS 2 Python examples: https://github.com/ros2/examples/tree/jazzy/rclpy
8. Supplied institutional document: ITR 2026 Guidelines (1).docx, School of Computer
   Engineering, Manipal Institute of Technology.

## Final report assembly notes

Use the department's prescribed report template when available. Add the student's
registration number, section, exact certified training dates, company identity,
supervisor details and required certificates from official records. Distinguish
original internship contributions from later repository improvements. Do not present
software simulation as hardware testing or assume these commits establish attendance.

The supplied guidelines require the plagiarism report after the references, with a
similarity index no greater than 20%; run an actual check on the final assembled
report rather than assigning a score. They also require NBA and IET mapping. The
generic NBA values supplied are PO1–PO11: 2, 2, 2, 1.67, 1.8, 1, 2, 1.67, 1.5,
1.67, 1.17; PSO1–PSO3: 2, 2, 2. Use the official programme definitions and the
referenced departmental IET table rather than inventing an accreditation mapping.

The final report filename is `Regno_Name_section_ITR_report.PDF`; certificate and
offer-letter filenames use the corresponding `_ITR_certificate.PDF` and
`_ITR_offerletter.PDF` suffixes. The guidelines specify a ten-minute presentation
followed by two minutes of viva. Their stated evaluation window is 31 August to
26 September 2026. Submission paperwork and academic acceptance are separate from
repository verification.
