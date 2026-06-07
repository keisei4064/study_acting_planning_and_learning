import dataclasses

import state_transition_system.model as sts_model
from typing import Generic, TypeVar, Callable, TypeAlias

StateT = TypeVar("StateT")
DomainT = TypeVar("DomainT")


GoalFormula: TypeAlias = Callable[[StateT], bool]


@dataclasses.dataclass(frozen=True)
class PlanningProblem(Generic[StateT, DomainT]):
    domain: DomainT
    """Σ"""
    initial_state: StateT
    """s0"""
    goal_formula: GoalFormula[StateT]
    """g"""


def is_solution(
    P: PlanningProblem[StateT, DomainT], pi: sts_model.Plan[StateT]
) -> bool:
    final_state = sts_model.transition_by_plan(P.initial_state, pi)
    if final_state is None:
        return False

    return P.goal_formula(final_state)


def is_minimal(P: PlanningProblem[StateT, DomainT], pi: sts_model.Plan[StateT]) -> bool:
    """The solution pi is minimal if no subsequence of pi is also a solution.　(p.16)"""

    for start_index in range(pi.length):
        for end_index in range(start_index, pi.length):
            subplan = pi.subplan(start_index, end_index)
            if is_solution(P, subplan):
                return False

    return True


def is_shortest(
    P: PlanningProblem[StateT, DomainT], pi: sts_model.Plan[StateT]
) -> bool:
    """pi is shortest if there is no sol; pi' such that |pi'| < |pi|"""
    # 判定実装は分からん
    raise NotImplementedError()


def is_optimal(P: PlanningProblem[StateT, DomainT], pi: sts_model.Plan[StateT]) -> bool:
    # 判定実装は分からん
    raise NotImplementedError()
