import state_transition_system.model as sts_model
import state_variable_representation.action as svr_act
import state_variable_representation.model as svr_model
import state_variable_representation.action as svr_act
import state_variable_representation.first_order_logic as svr_fol
import dataclasses
from collections.abc import Callable, Mapping
from typing import TypeAlias, NewType


PlanNodeId = NewType("PlanNodeId", str)


@dataclasses.dataclass(frozen=True)
class PlanNode:
    """v"""

    id: PlanNodeId


@dataclasses.dataclass(frozen=True)
class PlanEdge:
    """ordering constraint"""

    before: PlanNode
    after: PlanNode


@dataclasses.dataclass(frozen=True)
class PlanEdges:
    """E"""

    constraints: frozenset[PlanEdge]

    def children_of(self, node: PlanNode) -> frozenset[PlanNode]:
        """指定ノードについての直接の子ノード集合を返す"""
        return frozenset(edge.after for edge in self.constraints if edge.before == node)

    def precedes(self, before: PlanNode, after: PlanNode) -> bool:
        """before node から after node へのパスが存在するかどうかを返す

        def: 𝑣 ≺ 𝑣′ if 𝑣′ = 𝑣 or (𝑉, 𝐸) contains a path from 𝑣 to 𝑣′. (p.54)
        """

        if before == after:
            return False

        visited: set[PlanNode] = set()
        frontier: list[PlanNode] = list(self.children_of(before))

        while len(frontier) > 0:
            current = frontier.pop()

            if current == after:
                return True

            if current in visited:
                continue

            visited.add(current)
            frontier.extend(self.children_of(current))

        return False


ActionByNode: TypeAlias = Mapping[PlanNode, svr_act.ActionExpr]


@dataclasses.dataclass(frozen=True)
class PartiallyOrderedPlan:
    """p.54"""

    nodes: frozenset[PlanNode]
    """V"""

    edges: PlanEdges
    """E"""

    act: ActionByNode
    """act (must be ground)"""

    def __post_init__(self):
        # act が指すActionが全てgroundになっているか確認
        for node, action in self.act.items():
            if not svr_model.is_ground(action):
                raise ValueError(
                    f"The action {action} of the node {node} is not ground."
                )


@dataclasses.dataclass(frozen=True)
class InequalityConstraint:
    left: svr_model.ObjectVariable
    right: svr_model.ObjectTerm


class CausalLink:
    left_node: PlanNode
    right_node: PlanNode
    left_effect: svr_model.StateVariableAssignment
    right_precondition: svr_fol.StateVariableLiteralExpr

    def __post_init__(self):
        if (
            self.left_effect.state_variable
            != self.right_precondition.atom.state_variable
        ):
            raise ValueError(
                f"The state variable of the left effect must be the same as the state variable of the right precondition: {self.left_effect.state_variable} != {self.right_precondition.atom.state_variable}"
            )

        assign_value = self.left_effect.value  # x
        if self.right_precondition.negated:
            # x ≠ b' for some b' ≠ b
            if assign_value == self.right_precondition.atom.value:
                raise ValueError(
                    f"The left node's state variable literal is negated: {self.right_precondition}\n"
                    f"The right node's effect value must be different from the left node's precondition value."
                    f"But they are the same: {self.left_effect.value} != {self.right_precondition.atom.value}"
                )
        else:
            # x = b
            if not assign_value == self.right_precondition.atom.value:
                raise ValueError(
                    f"The left node's state variable literal is not negated: {self.right_precondition}\n"
                    f"The right node's effect value must be the same as the left node's precondition value."
                    f"But they are different: {self.left_effect.value} != {self.right_precondition.atom.value}"
                )


Constraint: TypeAlias = InequalityConstraint | CausalLink


@dataclasses.dataclass
class PartialPlan:
    """p.54 def 3.10"""

    nodes: frozenset[PlanNode]
    """V"""

    edges: frozenset[PlanEdge]
    """E"""

    act: ActionByNode
    """act (may be unground)"""

    constraints: frozenset[Constraint]
    """C"""


# ---


class Flaw:
    pass


class Resolver:
    pass
