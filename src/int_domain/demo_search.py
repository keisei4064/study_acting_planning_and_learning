from __future__ import annotations

import forward_state_space_search.algorithm as fsss_algorithm
import int_domain.model as int_domain


def main() -> None:
    problem = int_domain.IntPlanningProblem(
        int_domain.IntDomain(),
        3,
        lambda s: s == 11,
    )
    action_builder = int_domain.ApplicableActionBuilder()
    print("BFS: ", fsss_algorithm.breadth_first_search(problem, action_builder))
    print("DFS: ", fsss_algorithm.depth_first_search(problem, action_builder))


if __name__ == "__main__":
    main()
