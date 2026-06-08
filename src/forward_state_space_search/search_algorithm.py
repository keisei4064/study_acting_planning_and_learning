import forward_state_space_search.model as fsss_model
import state_transition_system.model as sts_model
import state_transition_system.problem as sts_prob
from typing import TypeAlias, Generic, TypeVar, Callable

DomainT = TypeVar("DomainT")
StateT = TypeVar("StateT")

Frontier: TypeAlias = list[fsss_model.SearchNode[StateT]]
Expanded: TypeAlias = set[fsss_model.SearchNode[StateT]]
Children: TypeAlias = list[fsss_model.SearchNode[StateT]]

FrontierSelector: TypeAlias = Callable[
    [DomainT, Frontier, Expanded], fsss_model.SearchNode[StateT]
]
ChildrenBuilder: TypeAlias = Callable[
    [DomainT, fsss_model.SearchNode[StateT]], Children
]
NodePruner: TypeAlias = Callable[
    [DomainT, Children, Frontier, Expanded], tuple[Children, Frontier, Expanded]
]


def forward_search_det(
    problem: sts_prob.PlanningProblem[StateT, DomainT],
    frontier_selector: FrontierSelector[DomainT, StateT],
    children_builder: ChildrenBuilder[DomainT, StateT],
    node_pruner: NodePruner[DomainT],
) -> sts_model.Plan[StateT] | None:
    """Algorithm 3.2. Forward-Search-Det (p.35)"""
    frontier: Frontier[StateT] = [
        fsss_model.SearchNode[StateT](
            action=None,
            state=problem.initial_state,
            depth=0,
            cost=0,
            parent=None,
        )
    ]
    expanded: Expanded = set()

    while len(frontier) > 0:
        selected_node = frontier_selector(problem.domain, frontier, expanded)
        frontier.remove(selected_node)
        expanded.add(selected_node)

        if problem.goal_formula(selected_node.state):
            # プランニング完了
            return selected_node.extract_plan()

        # 子ノード展開
        children = children_builder(problem.domain, selected_node)

        # prune
        children, frontier, expanded = node_pruner(
            problem.domain, children, frontier, expanded
        )

        # フロンティアに追加
        frontier += children

    # 失敗
    return None
