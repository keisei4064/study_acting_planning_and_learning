import state_transition_system.model as sts_model
import state_variable_representation.action as svr_act
import dataclasses
from collections.abc import Callable
from typing import TypeAlias


class Node:
    pass


class Edge:
    pass


@dataclasses.dataclass
class PartiallyOrderedPlan:
    """p.54"""

    nodes: set[Node]
    """V"""

    edges: set[Edge]
    """E"""

    act: Callable[[Node], svr_act.GroundAction]
    """act (must be ground)"""


class InequalityConstraint:
    pass


class CausalLink:
    pass


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


class Flaw:
    pass


class Resolver:
    pass
