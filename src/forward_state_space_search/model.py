from __future__ import annotations

import dataclasses
import state_transition_system.model as sts_model

from typing import Generic, TypeVar, Self

StateT = TypeVar("StateT")


@dataclasses.dataclass(frozen=True)
class SearchNode(Generic[StateT]):
    action: sts_model.Action[StateT] | None
    state: StateT
    depth: int
    cost: float
    parent: Self | None
    # children: tuple[Self, ...]

    def is_ancestor_of(self, descendant_candidate_node: Self) -> bool:
        """p.35"""
        if self is descendant_candidate_node.parent:
            return True

        if descendant_candidate_node.parent is None:
            return False

        return self.is_ancestor_of(descendant_candidate_node.parent)

    def is_successor_of(self, ancestor_candidate_node: Self) -> bool:
        """p.35"""
        return ancestor_candidate_node.is_ancestor_of(self)

    def try_build_child(
        self, action: sts_model.Action[StateT]
    ) -> SearchNode[StateT] | None:
        new_state = sts_model.transition_by_action(self.state, action)
        if new_state is None:
            return None

        return SearchNode[StateT](
            action=action,
            state=new_state,
            depth=self.depth + 1,
            cost=self.cost + action.cost,
            parent=self,
        )

    def extract_plan(self) -> sts_model.Plan[StateT]:
        """action の列を辿って plan を作る"""
        actions_from_goal_to_root: list[sts_model.Action[StateT]] = []

        current_node: Self | None = self
        while current_node is not None:
            if current_node.action is not None:
                actions_from_goal_to_root.append(current_node.action)
            current_node = current_node.parent

        return sts_model.Plan[StateT](list(reversed(actions_from_goal_to_root)))
