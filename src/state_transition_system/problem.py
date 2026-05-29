import dataclasses

import state_transition_system.system as stsystem


@dataclasses.dataclass
class Problem:
    system: stsystem.StateTransitionSystem
    initial_state: stsystem.State
    """s0"""
    goal_states: set[stsystem.State]
    """S_g"""


def is_solution(P: Problem, pi: stsystem.Plan) -> bool:
    final_state = stsystem.transition_by_plan(P.initial_state, pi)
    if final_state is None:
        return False

    return final_state in P.goal_states


def is_minimal(P: Problem, pi: stsystem.Plan) -> bool:
    """The solution pi is minimal if no subsequence of pi is also a solution.　(p.16)"""

    for start_index in range(pi.length):
        for end_index in range(start_index, pi.length):
            subplan = pi.subplan(start_index, end_index)
            if is_solution(P, subplan):
                return False

    return True


def is_shortest(P: Problem, pi: stsystem.Plan) -> bool:
    """pi is shortest if there is no sol; pi' such that |pi'| < |pi|"""
    # 判定実装は分からん
    raise NotImplementedError()


def is_optimal(P: Problem, pi: stsystem.Plan) -> bool:
    # 判定実装は分からん
    raise NotImplementedError()
