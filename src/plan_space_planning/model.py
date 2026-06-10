import state_transition_system.model as sts_model
import state_variable_representation.action as svr_act
import state_variable_representation.model as svr_model
import state_variable_representation.action as svr_act
import state_variable_representation.first_order_logic as svr_fol
import dataclasses
from collections.abc import Callable, Mapping
from typing import TypeAlias, NewType, Generic, TypeVar, Sequence


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


# Causal Link ---

ActionSchemaElementT = TypeVar(
    "ActionSchemaElementT", bound=svr_model.InstantiableExpression
)


def _resolve_indexed_action_element(
    *,
    node: PlanNode,
    index: int,
    action_by_node: ActionByNode,
    schema_elements_getter: Callable[
        [svr_act.ActionExpr], Sequence[ActionSchemaElementT]
    ],
    element_label: str,
) -> ActionSchemaElementT | None:
    # 登録されてるか
    if node not in action_by_node:
        return None

    action_expr = action_by_node[node]
    schema_elements = schema_elements_getter(action_expr)

    # 有効なindexか
    if not 0 <= index < len(schema_elements):
        raise ValueError(
            f"The {element_label} index {index} is out of range. "
            f"Action expression: {action_expr}, "
            f"number of {element_label}s: {len(schema_elements)}"
        )

    # Schema要素から現在のパラメータを代入して実体化
    schema_element = schema_elements[index]
    substitution_map = action_expr.get_parameter_substitution_map()

    return svr_model.instantiate(schema_element, substitution_map)


EffectIndex = NewType("EffectIndex", int)


@dataclasses.dataclass(frozen=True)
class EffectRef:
    node: PlanNode
    effect_id: EffectIndex

    def resolve(
        self, action_by_node: ActionByNode
    ) -> svr_model.StateVariableAssignment | None:
        # 参照先 effect を取得するヘルパ
        def get_effects(
            action_expr: svr_act.ActionExpr,
        ) -> Sequence[svr_model.StateVariableAssignment]:
            return action_expr.schema.effects.effects

        # 参照先 effect を実体化
        return _resolve_indexed_action_element(
            node=self.node,
            index=self.effect_id,
            action_by_node=action_by_node,
            schema_elements_getter=get_effects,
            element_label="effect",
        )


PreconditionIndex = NewType("PreconditionIndex", int)


@dataclasses.dataclass(frozen=True)
class PreconditionRef:
    node: PlanNode
    precondition_id: PreconditionIndex

    def resolve(self, action_by_node: ActionByNode) -> svr_fol.LiteralExpr | None:
        # 参照先 precondition を取得するヘルパ
        def get_preconditions(
            action_expr: svr_act.ActionExpr,
        ) -> Sequence[svr_fol.LiteralExpr]:
            return action_expr.schema.preconditions.literals

        # 参照先 precondition を実体化
        return _resolve_indexed_action_element(
            node=self.node,
            index=self.precondition_id,
            action_by_node=action_by_node,
            schema_elements_getter=get_preconditions,
            element_label="precondition",
        )


@dataclasses.dataclass(frozen=True)
class CausalLink:
    left: EffectRef
    right: PreconditionRef

    def validate(self, edges: PlanEdges, action_by_node: ActionByNode):
        # 順序が指定されているべき
        if not edges.precedes(self.left.node, self.right.node):
            raise ValueError(
                f"The left node {self.left.node} must precede the right node {self.right.node} in CausalLink."
            )

        left_effect = self.left.resolve(action_by_node)
        right_precondition = self.right.resolve(action_by_node)

        # 参照が解決出来たか
        if left_effect is None:
            raise ValueError(
                f"The reference to the left effect is invalid: {self.left}"
            )
        if right_precondition is None:
            raise ValueError(
                f"The reference to the right precondition is invalid: {self.right}"
            )

        # precondition は StateVariableLiteralExpr しか受け付けない
        if not isinstance(right_precondition, svr_fol.StateVariableLiteralExpr):
            raise ValueError(
                f"The right precondition must be a StateVariableLiteralExpr: {right_precondition}"
            )

        # left effect と right precondition が同一の変数を指しているか
        assign_value = left_effect.value  # b in x ← b
        if right_precondition.negated:
            # x ≠ b' for some b' ≠ b
            if assign_value == right_precondition.atom.value:
                raise ValueError(
                    f"The left node's state variable literal is negated: {right_precondition}\n"
                    f"The right node's effect value must be different from the left node's precondition value."
                    f"But they are the same: {left_effect.value} != {right_precondition.atom.value}"
                )
        else:
            # x = b
            if not assign_value == right_precondition.atom.value:
                raise ValueError(
                    f"The left node's state variable literal is not negated: {right_precondition}\n"
                    f"The right node's effect value must be the same as the left node's precondition value."
                    f"But they are different: {left_effect.value} != {right_precondition.atom.value}"
                )

    def violates(
        self, dubious_node: PlanNode, edges: PlanEdges, action_by_node: ActionByNode
    ):
        """p.55"""

        # 前提: 𝜈1 ≺ 𝜈3 ≺ 𝜈2
        if not (
            edges.precedes(self.left.node, dubious_node)
            and edges.precedes(dubious_node, self.right.node)
        ):
            return False

        # この CausalLink が関与する state variable を取得
        associated_state_variable = self.left.resolve(action_by_node)
        if associated_state_variable is None:
            raise ValueError(
                f"The reference to the left effect is invalid: {self.left}"
            )

        # 検査対称ノードの Action を取得
        dubious_action_expr = action_by_node[dubious_node]
        dubious_substitution_map = dubious_action_expr.get_parameter_substitution_map()

        # effect を順に検査
        for dubious_effect in dubious_action_expr.schema.effects.effects:
            instantiated_effect = svr_model.instantiate(
                dubious_effect, dubious_substitution_map
            )

            # effect の変数と前提の変数が一致するか
            if (
                associated_state_variable.state_variable
                == instantiated_effect.state_variable
            ):
                # violates !!
                return True

        # not violates.
        return False


# ---


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
