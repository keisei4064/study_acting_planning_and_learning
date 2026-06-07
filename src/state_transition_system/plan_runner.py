import state_transition_system.system as stssys
import state_transition_system.problem as stsprob
from typing import TypeVar, Callable, TypeAlias
import enum

StateT = TypeVar("StateT")
DomainT = TypeVar("DomainT")


StateObserver: TypeAlias = Callable[[DomainT], StateT]
ActionPerformer: TypeAlias = Callable[[DomainT, stssys.Action[StateT]], None]


class ExecutionResult(enum.Enum):
    SUCCESS = 0
    FAILURE = 1


def run_plan(
    domain: DomainT,
    pi: stssys.Plan[StateT],
    goal: stsprob.GoalFormula[StateT],
    observer: StateObserver[DomainT, StateT],
    performer: ActionPerformer[DomainT, StateT],
) -> ExecutionResult:
    """Algorithm 2.1. (p.16)"""
    while True:
        s = observer(domain)

        if pi.length == 0:
            return ExecutionResult.SUCCESS if goal(s) else ExecutionResult.FAILURE

        a = pi.actions.pop(0)
        if not a.is_applicable(s):
            return ExecutionResult.FAILURE

        performer(domain, a)


def reactive_execution(
    domain: DomainT,
    pi: stssys.Plan[StateT],
    goal: stsprob.GoalFormula[StateT],
    observer: StateObserver[DomainT, StateT],
    performer: ActionPerformer[DomainT, StateT],
) -> ExecutionResult:
    """Algorithm 2.2. (p.26)"""
    while True:
        s = observer(domain)
        if goal(s):
            return ExecutionResult.SUCCESS

        a: stssys.Action[StateT] | None = None
        for i in range(pi.length, 0, -1):
            suffix_plan = pi.suffix(i - 1)
            expected_state = stssys.transition_by_plan(s, suffix_plan)
            if expected_state is not None and goal(expected_state):
                a = suffix_plan.actions[0]
                break
        if a is None:
            return ExecutionResult.FAILURE

        performer(domain, a)
