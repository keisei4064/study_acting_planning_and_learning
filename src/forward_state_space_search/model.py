from __future__ import annotations

import dataclasses
import state_transition_system.model as sts_model

from typing import Generic, TypeVar

StateT = TypeVar("StateT")


@dataclasses.dataclass(frozen=True)
class SearchNode(Generic[StateT]):
    action_from_parent: sts_model.Action[StateT] | None
    state: StateT
    depth: int
    path_cost: float
    parent: SearchNode[StateT] | None
    # children: tuple[Self, ...]

    def is_ancestor_of(self, descendant_candidate_node: SearchNode[StateT]) -> bool:
        """p.35"""
        if self is descendant_candidate_node.parent:
            return True

        if descendant_candidate_node.parent is None:
            return False

        return self.is_ancestor_of(descendant_candidate_node.parent)

    def is_successor_of(self, ancestor_candidate_node: SearchNode[StateT]) -> bool:
        """p.35"""
        return ancestor_candidate_node.is_ancestor_of(self)

    def try_build_child(
        self, action: sts_model.Action[StateT]
    ) -> SearchNode[StateT] | None:
        new_state = sts_model.transition_by_action(self.state, action)
        if new_state is None:
            return None

        return SearchNode[StateT](
            action_from_parent=action,
            state=new_state,
            depth=self.depth + 1,
            path_cost=self.path_cost + action.cost,
            parent=self,
        )

    def extract_plan(self) -> sts_model.Plan[StateT]:
        """action の列を辿って plan を作る"""
        actions_from_goal_to_root: list[sts_model.Action[StateT]] = []

        current_node: SearchNode[StateT] | None = self
        while current_node is not None:
            if current_node.action_from_parent is not None:
                actions_from_goal_to_root.append(current_node.action_from_parent)
            current_node = current_node.parent

        return sts_model.Plan[StateT](list(reversed(actions_from_goal_to_root)))
