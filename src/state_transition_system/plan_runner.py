import state_transition_system.system as stssys
import state_transition_system.problem as stsprob
from typing import TypeVar, Callable, TypeAlias


StateT = TypeVar("StateT")
DomainT = TypeVar("DomainT")


StatePercepter: TypeAlias = Callable[[DomainT, StateT], StateT]


def run_plan(
    domain: DomainT,
    s0: StateT,
    pi: stssys.Plan[StateT],
    goal: stsprob.GoalFormula[StateT],
    percepter: StatePercepter[DomainT, StateT],
) -> bool:
    """Algorithm 2.1."""
    s = s0
    while True:
        s = percepter(domain, s)

        if pi.length == 0:
            return goal(s)

        a = pi.actions.pop(0)
        if not a.is_applicable(s):
            return False

        s = a.transition(s)
        if s is None:
            return False
