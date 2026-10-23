import unittest

from state_machine_utils import StateMachine, TransitionError, StateError


def no_action(*a, **k):
    pass


class TestStateMachine(unittest.TestCase):
    def setUp(self):
        self.transitions = [
            ("idle", "start", "running", no_action),
            ("running", "pause", "paused", no_action),
            ("paused", "resume", "running", no_action),
            ("running", "finish", "done", no_action),
        ]

    def test_initial_state_running(self):
        m = StateMachine(self.transitions, initial_state="idle")
        self.assertTrue(m.running)
        self.assertEqual(m.state, "idle")

    def test_reset(self):
        m = StateMachine(self.transitions, initial_state="idle")
        m.trigger("start")
        self.assertEqual(m.state, "running")
        m.reset()
        self.assertEqual(m.state, "idle")

    def test_reset_without_initial_raises(self):
        m = StateMachine(self.transitions)
        with self.assertRaises(StateError):
            m.reset()

    def test_transition_changes_state(self):
        m = StateMachine(self.transitions, initial_state="idle")
        result = m.trigger("start")
        self.assertEqual(result, "running")
        self.assertEqual(m.state, "running")

    def test_impossible_transition_raises(self):
        m = StateMachine(self.transitions, initial_state="idle")
        with self.assertRaises(TransitionError) as ctx:
            m.trigger("pause")
        self.assertIn("pause", str(ctx.exception))
        self.assertIn("idle", str(ctx.exception))
        self.assertEqual(m.state, "idle")

    def test_trigger_when_not_running_raises(self):
        m = StateMachine(self.transitions)
        with self.assertRaises(StateError):
            m.trigger("start")

    def test_action_receives_args(self):
        received = []

        def action(*a, **k):
            received.append((a, k))

        m = StateMachine([("idle", "go", "done", action)], initial_state="idle")
        m.trigger("go", 1, 2, key="value")
        self.assertEqual(received, [((1, 2), {"key": "value"})])

    def test_action_with_none(self):
        m = StateMachine([("idle", "go", "done", None)], initial_state="idle")
        result = m.trigger("go")
        self.assertEqual(result, "done")

    def test_duplicate_transition_raises(self):
        with self.assertRaises(ValueError) as ctx:
            StateMachine([
                ("idle", "go", "done", no_action),
                ("idle", "go", "other", no_action),
            ])
        msg = str(ctx.exception)
        self.assertIn("Duplicate transition", msg)
        self.assertIn("'idle'", msg)
        self.assertIn("'go'", msg)
        self.assertIn("index 0", msg)
        self.assertIn("index 1", msg)

    def test_same_event_different_states(self):
        m = StateMachine([
            ("a", "flip", "b", no_action),
            ("b", "flip", "a", no_action),
        ], initial_state="a")
        self.assertEqual(m.trigger("flip"), "b")
        self.assertEqual(m.trigger("flip"), "a")

    def test_full_lifecycle(self):
        m = StateMachine(self.transitions, initial_state="idle")
        m.trigger("start")
        m.trigger("pause")
        m.trigger("resume")
        m.trigger("finish")
        self.assertEqual(m.state, "done")

    def test_transition_after_terminal_state_raises(self):
        m = StateMachine(self.transitions, initial_state="idle")
        m.trigger("start")
        m.trigger("finish")
        with self.assertRaises(TransitionError):
            m.trigger("start")

    def test_empty_transitions(self):
        m = StateMachine([], initial_state="idle")
        self.assertTrue(m.running)
        with self.assertRaises(TransitionError):
            m.trigger("anything")

    def test_state_property_is_assignable(self):
        m = StateMachine(self.transitions, initial_state="idle")
        m.state = "done"
        self.assertEqual(m.state, "done")


if __name__ == "__main__":
    unittest.main()
