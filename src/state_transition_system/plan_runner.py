import state_transition_system.state_transition_model as stsstm
import state_transition_system.problem as stsprob
from typing import TypeVar, Callable, TypeAlias
import enum

StateT = TypeVar("StateT")
DomainT = TypeVar("DomainT")


StateObserver: TypeAlias = Callable[[DomainT], StateT]
ActionPerformer: TypeAlias = Callable[[DomainT, stsstm.Action[StateT]], None]


class ExecutionResult(enum.Enum):
    SUCCESS = 0
    FAILURE = 1


def run_plan(
    domain: DomainT,
    pi: stsstm.Plan[StateT],
    goal: stsprob.GoalFormula[StateT],
    observer: StateObserver[DomainT, StateT],
    performer: ActionPerformer[DomainT, StateT],
) -> ExecutionResult:
    """Algorithm 2.1. : Run-Plan (p.16)"""
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
    pi: stsstm.Plan[StateT],
    goal: stsprob.GoalFormula[StateT],
    observer: StateObserver[DomainT, StateT],
    performer: ActionPerformer[DomainT, StateT],
) -> ExecutionResult:
    """Algorithm 2.2. : Reactive-Execution (p.26)"""
    while True:
        s = observer(domain)
        if goal(s):
            return ExecutionResult.SUCCESS

        a: stsstm.Action[StateT] | None = None
        for i in range(pi.length, 0, -1):
            suffix_plan = pi.suffix(i - 1)
            expected_state = stsstm.transition_by_plan(s, suffix_plan)
            if expected_state is not None and goal(expected_state):
                a = suffix_plan.actions[0]
                break
        if a is None:
            return ExecutionResult.FAILURE

        performer(domain, a)


LookAhead: TypeAlias = Callable[
    [DomainT, StateT, stsprob.GoalFormula[StateT]], stsstm.Plan[StateT] | None
]


def run_lookahead(
    domain: DomainT,
    goal: stsprob.GoalFormula[StateT],
    look_ahead: LookAhead[DomainT, StateT],
    observer: StateObserver[DomainT, StateT],
    performer: ActionPerformer[DomainT, StateT],
):
    """Algorithm 2.3. : Run-Lookahead (p.26)"""
    while True:
        s = observer(domain)
        if goal(s):
            return ExecutionResult.SUCCESS

        pi = look_ahead(domain, s, goal)
        if pi is None or pi.length == 0:
            return ExecutionResult.FAILURE

        a = pi.actions.pop(0)
        performer(domain, a)


Simulator: TypeAlias = Callable[
    [DomainT, StateT, stsprob.GoalFormula[StateT], stsstm.Plan[StateT]], ExecutionResult
]


def run_lazy_lookahead(
    domain: DomainT,
    goal: stsprob.GoalFormula[StateT],
    look_ahead: LookAhead[DomainT, StateT],
    simulator: Simulator[DomainT, StateT],
    observer: StateObserver[DomainT, StateT],
    performer: ActionPerformer[DomainT, StateT],
):
    """Algorithm 2.4. : Run-Lazy-Lookahead (p.27)"""
    pi = stsstm.Plan[StateT]([])
    while True:
        s = observer(domain)
        if goal(s):
            return ExecutionResult.SUCCESS

        if pi.length == 0 or simulator(domain, s, goal, pi) == ExecutionResult.FAILURE:
            pi = look_ahead(domain, s, goal)
            if pi is None or pi.length == 0:
                return ExecutionResult.FAILURE

        a = pi.actions.pop(0)
        performer(domain, a)
