import forward_state_space_search.model as fsss_model
import state_transition_system.model as sts_model
import state_transition_system.problem as sts_prob
from typing import TypeAlias, Generic, TypeVar, Callable, Protocol, Iterable

DomainT = TypeVar("DomainT")
DomainT_contra = TypeVar("DomainT_contra", contravariant=True)
StateT = TypeVar("StateT")

Frontier: TypeAlias = list[fsss_model.SearchNode[StateT]]
Expanded: TypeAlias = list[fsss_model.SearchNode[StateT]]
Children: TypeAlias = list[fsss_model.SearchNode[StateT]]


class FrontierSelector(Protocol[DomainT_contra, StateT]):
    def __call__(
        self,
        domain: DomainT_contra,
        frontier: Frontier[StateT],
        expanded: Expanded[StateT],
    ) -> fsss_model.SearchNode[StateT]: ...


class NodePruner(Protocol[DomainT_contra, StateT]):
    def __call__(
        self,
        domain: DomainT_contra,
        children: Children[StateT],
        frontier: Frontier[StateT],
        expanded: Expanded[StateT],
    ) -> tuple[Children[StateT], Frontier[StateT], Expanded[StateT]]: ...


class ApplicableActionBuilder(Protocol[DomainT_contra, StateT]):
    def __call__(
        self,
        domain: DomainT_contra,
        state: StateT,
    ) -> Iterable[sts_model.Action[StateT]]: ...


def forward_search_det(
    problem: sts_prob.PlanningProblem[StateT, DomainT],
    frontier_selector: FrontierSelector[DomainT, StateT],
    applicable_action_builder: ApplicableActionBuilder[DomainT, StateT],
    node_pruner: NodePruner[DomainT, StateT],
) -> sts_model.Plan[StateT] | None:
    """Algorithm 3.2. Forward-Search-Det (p.35)"""
    frontier: Frontier[StateT] = [
        fsss_model.SearchNode[StateT](
            action_from_parent=None,
            state=problem.initial_state,
            depth=0,
            path_cost=0,
            parent=None,
        )
    ]
    expanded: Expanded = []

    while len(frontier) > 0:
        selected_node = frontier_selector(problem.domain, frontier, expanded)
        frontier.remove(selected_node)
        expanded.append(selected_node)

        if problem.goal_formula(selected_node.state):
            # プランニング完了
            return selected_node.extract_plan()

        # 子ノード展開
        children: Children[StateT] = []
        for action in applicable_action_builder(problem.domain, selected_node.state):
            child = selected_node.try_build_child(action)
            if child is not None:
                children.append(child)

        # prune
        children, frontier, expanded = node_pruner(
            problem.domain, children, frontier, expanded
        )

        # フロンティアに追加
        frontier += children

    # 失敗
    return None
