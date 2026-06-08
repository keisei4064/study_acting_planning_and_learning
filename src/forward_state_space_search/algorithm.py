import forward_state_space_search.template as fsss_template
import forward_state_space_search.model as fsss_model
import state_transition_system.model as sts_model
from typing import TypeAlias, Generic, TypeVar

DomainT = TypeVar("DomainT")
DomainT_contra = TypeVar("DomainT_contra", contravariant=True)
StateT = TypeVar("StateT")


# 一般 ---


class ExpandedStatePruner(fsss_template.NodePruner[DomainT_contra, StateT]):
    """既に Expanded（探索済み）な State のノードを Frontier と Children から除外"""

    def __call__(
        self,
        domain: DomainT_contra,
        children: fsss_template.Children[StateT],
        frontier: fsss_template.Frontier[StateT],
        expanded: fsss_template.Expanded[StateT],
    ) -> tuple[
        fsss_template.Children[StateT],
        fsss_template.Frontier[StateT],
        fsss_template.Expanded[StateT],
    ]:
        expanded_states = [node.state for node in expanded]

        pruned_children = [
            node for node in children if node.state not in expanded_states
        ]
        pruned_frontier = [
            node for node in frontier if node.state not in expanded_states
        ]
        return pruned_children, pruned_frontier, expanded


# BFS (p.36) ---


class BFSSelector(fsss_template.FrontierSelector[DomainT_contra, StateT]):
    def __call__(
        self,
        domain: DomainT_contra,
        frontier: fsss_template.Frontier[StateT],
        expanded: fsss_template.Expanded[StateT],
    ) -> fsss_model.SearchNode[StateT]:
        min_length_node = frontier[0]
        for node in frontier:
            if node.depth < min_length_node.depth:
                min_length_node = node
        return min_length_node


def breadth_first_search(
    problem: fsss_template.sts_prob.PlanningProblem[StateT, DomainT],
    applicable_action_builder: fsss_template.ApplicableActionBuilder[DomainT, StateT],
) -> sts_model.Plan[StateT] | None:
    """Breadth-first search (p.36)"""
    return fsss_template.forward_search_det(
        problem, BFSSelector(), applicable_action_builder, ExpandedStatePruner()
    )


# DFS ---


class DFSSelector(fsss_template.FrontierSelector[DomainT_contra, StateT]):
    def __call__(
        self,
        domain: DomainT_contra,
        frontier: fsss_template.Frontier[StateT],
        expanded: fsss_template.Expanded[StateT],
    ) -> fsss_model.SearchNode[StateT]:
        max_length_node = frontier[0]
        for node in frontier:
            if node.depth > max_length_node.depth:
                max_length_node = node
        return max_length_node


def depth_first_search(
    problem: fsss_template.sts_prob.PlanningProblem[StateT, DomainT],
    applicable_action_builder: fsss_template.ApplicableActionBuilder[DomainT, StateT],
) -> sts_model.Plan[StateT] | None:
    """Depth-first search (p.36)

    ただし，メモリ使用量は無駄に増えちゃう実装
    """
    return fsss_template.forward_search_det(
        problem, DFSSelector(), applicable_action_builder, ExpandedStatePruner()
    )


if __name__ == "__main__":
    import int_domain.model as int_domain

    problem = int_domain.IntPlanningProblem(
        int_domain.IntDomain(),
        3,
        lambda s: s == 11,
    )
    action_builder = int_domain.ApplicableActionBuilder()
    print("BFS: ", breadth_first_search(problem, action_builder))
    print("DFS: ", depth_first_search(problem, action_builder))
