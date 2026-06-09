import state_transition_system.model as sts_model
import state_variable_representation.action as svr_act
import state_variable_representation.model as svr_model
import state_variable_representation.action as svr_act
import state_variable_representation.first_order_logic as svr_fol
import dataclasses
from collections.abc import Callable
from typing import TypeAlias


@dataclasses.dataclass(frozen=True)
class Node:
    action_schema: svr_act.ActionExpr


@dataclasses.dataclass(frozen=True)
class Edge:
    from_node: Node
    to_node: Node


def do_node1_preceds_node2(node1: Node, node2: Node, edges: set[Edge]) -> bool:
    """𝑣 ≺ 𝑣′ if 𝑣 ≠ 𝑣′ and (𝑉, 𝐸) contains a path from 𝑣 to 𝑣′. (p.54)"""
    if Edge(from_node=node1, to_node=node2) in edges:
        return True
    children = [edge.from_node for edge in edges if edge.to_node == node1]
    for child in children:
        return do_node1_preceds_node2(child, node2, edges)
    return False


@dataclasses.dataclass
class PartiallyOrderedPlan:
    """p.54"""

    nodes: set[Node]
    """V"""

    edges: set[Edge]
    """E"""

    act: Callable[[Node], svr_act.GroundAction]
    """act (must be ground)"""


@dataclasses.dataclass(frozen=True)
class InequalityConstraint:
    left: svr_model.ObjectVariable
    right: svr_model.ObjectTerm


class CausalLink:
    left_node: Node
    right_node: Node
    left_effect: svr_model.StateVariableAssignment
    right_precondition: svr_fol.StateVariableLiteralExpr

    def __post_init__(self):
        if (
            self.left_effect.state_variable
            is not self.right_precondition.atom.state_variable
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

    nodes: set[Node]
    """V"""

    edges: set[Edge]
    """E"""

    act: Callable[[Node], svr_act.ActionExpr]
    """act (may be unground)"""

    constraints: set[Constraint]
    """C"""


class Flaw:
    pass


class Resolver:
    pass
