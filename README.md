# state-machine-utils

A finite state machine that rejects impossible transitions. The machine is constructed from a list of `(source, event, target, action)` tuples; calling `trigger(event)` looks up the current state and event, moves to the target, and invokes the action. If no transition matches, a `TransitionError` is raised and the state is left untouched.

```python
from state_machine_utils import StateMachine, TransitionError, StateError

def log_pause():
    print("paused")

machine = StateMachine(
    transitions=[
        ("idle", "start", "running", None),
        ("running", "pause", "paused", log_pause),
        ("running", "finish", "done", None),
        ("paused", "resume", "running", None),
    ],
    initial_state="idle",
)

print(machine.state)            # idle
machine.trigger("start")       # moves to running
print(machine.state)            # running
machine.trigger("pause")        # moves to paused, prints "paused"

try:
    machine.trigger("finish")   # no such transition from "paused"
except TransitionError:
    pass

machine.reset()                 # back to idle
```

## Why this exists

The point is to make illegal states unrepresentable at runtime: any event that has no matching transition from the current state raises immediately, and the state is never left in a half-moved condition. This catches ordering bugs (firing an event at the wrong time) at the call site rather than letting them propagate as mysterious downstream behaviour.

The trade-off is that the machine is fully explicit. There is no glob matching, no wildcard transitions, no inheritance between states. If the same event can fire from several states, you write one tuple per state. This is deliberate: ambiguity in a state machine is where the bugs live, and a compact syntax that hides the ambiguity is worse than a verbose one that does not.

## Construction and the running flag

`StateMachine(transitions, initial_state=None)` accepts an iterable of four-tuples `(source, event, target, action)`. The `action` may be `None` if no side effect is wanted. If `initial_state` is provided, the machine starts in that state (the `running` property is `True`); if it is omitted, the machine is not running until `reset()` is called. The two `ValueError` subclasses serve distinct purposes: `StateError` is raised when the machine is asked to transition while not running, and `TransitionError` is raised when it is running but the event has no matching transition.

Duplicate `(source, event)` keys are rejected at construction time, because two rules for the same state and event would make the outcome depend on iteration order. The error message reports both conflicting tuples and their indices so the offending entry is easy to locate.

## Awkward edges

The `state` attribute is a plain instance variable and is intentionally assignable. Forcing transitions through `trigger` alone is good discipline, but in practice machines sometimes need to be coerced (for error recovery, for replaying a checkpoint, or in tests). Rather than provide a separate `force_state` method with its own policy, the attribute is left writable. If you want encapsulation, wrap the machine.

A machine with `initial_state=None` is not running; calling `trigger` on it raises `StateError`, not `TransitionError`. The distinction is that the machine has not been told where to start, so the failure is one of configuration, not of transition logic.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

