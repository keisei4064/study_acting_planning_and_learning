import state_transition_system.system as stsystem


def run_plan(
    system: stsystem.StateTransitionSystem,
    s0: stsystem.State,
    pi: stsystem.Plan,
    goal_states: set[stsystem.State],
) -> bool:
    """Algorithm 2.1."""
    s = s0
    while True:
        # s = observe(s)
        if pi.length == 0:
            return s in goal_states

        a = pi.actions.pop(0)
        if not a.is_applicable(s):
            return False

        s = a.transition(s)
        if s is None:
            return False
