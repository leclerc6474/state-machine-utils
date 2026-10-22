"""A finite state machine that rejects impossible transitions."""


class TransitionError(ValueError):
    """Raised when an event has no matching transition from the current state."""


class StateError(ValueError):
    """Raised when the machine is asked to transition while it is not running."""


class StateMachine:
    def __init__(self, transitions, initial_state=None):
        # Storing the original tuple keeps the construction order visible in error
        # messages; reordering the pairs would otherwise silently change which
        # duplicate is reported.
        self._transitions = tuple(transitions)
        seen = {}
        for idx, (src, event, dst, action) in enumerate(self._transitions):
            key = (src, event)
            if key in seen:
                prev_idx = seen[key]
                prev_src, prev_event, prev_dst, _ = self._transitions[prev_idx]
                raise ValueError(
                    "Duplicate transition "
                    f"({prev_src!r}, {prev_event!r}, {prev_dst!r}) "
                    f"at index {prev_idx} conflicts with "
                    f"({src!r}, {event!r}, {dst!r}) at index {idx}"
                )
            seen[key] = idx
        self._by_source = {}
        for idx, (src, event, dst, action) in enumerate(self._transitions):
            self._by_source.setdefault(src, {})[event] = (dst, action)
        self.initial_state = initial_state
        self.state = None
        if initial_state is not None:
            self.reset()

    def reset(self):
        if self.initial_state is None:
            raise StateError("cannot reset: no initial_state was configured")
        self.state = self.initial_state

    @property
    def running(self):
        return self.state is not None

    def trigger(self, event, *args, **kwargs):
        if self.state is None:
            raise StateError("machine is not running; call reset() first")
        table = self._by_source.get(self.state)
        if table is None or event not in table:
            raise TransitionError(
                f"no transition for event {event!r} from state {self.state!r}"
            )
        dst, action = table[event]
        self.state = dst
        if action is not None:
            action(*args, **kwargs)
        return dst
