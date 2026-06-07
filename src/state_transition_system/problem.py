import dataclasses

import state_transition_system.system as stssys
from typing import Generic, TypeVar, Callable

StateT = TypeVar("StateT")
DomainT = TypeVar("DomainT")


@dataclasses.dataclass(frozen=True)
class PlanningProblem(Generic[StateT, DomainT]):
    domain: DomainT
    """Σ"""
    initial_state: StateT
    """s0"""
    goal_formula: Callable[[StateT], bool]
    """g"""


def is_solution(P: PlanningProblem[StateT, DomainT], pi: stssys.Plan[StateT]) -> bool:
    final_state = stssys.transition_by_plan(P.initial_state, pi)
    if final_state is None:
        return False

    return P.goal_formula(final_state)


def is_minimal(P: PlanningProblem[StateT, DomainT], pi: stssys.Plan[StateT]) -> bool:
    """The solution pi is minimal if no subsequence of pi is also a solution.　(p.16)"""

    for start_index in range(pi.length):
        for end_index in range(start_index, pi.length):
            subplan = pi.subplan(start_index, end_index)
            if is_solution(P, subplan):
                return False

    return True


def is_shortest(P: PlanningProblem[StateT, DomainT], pi: stssys.Plan[StateT]) -> bool:
    """pi is shortest if there is no sol; pi' such that |pi'| < |pi|"""
    # 判定実装は分からん
    raise NotImplementedError()


def is_optimal(P: PlanningProblem[StateT, DomainT], pi: stssys.Plan[StateT]) -> bool:
    # 判定実装は分からん
    raise NotImplementedError()
