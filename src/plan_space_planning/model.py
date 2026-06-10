import state_transition_system.model as sts_model
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

    def __str__(self) -> str:
        return f"({self.before.id}, {self.after.id})"


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

    def has_cycle(self) -> bool:
        """サイクルを持っているか"""
        visited: set[PlanNode] = set()
        visiting: set[PlanNode] = set()

        def visit(node: PlanNode) -> bool:
            if node in visiting:
                # 2回目の訪問 ➾ サイクル
                return True

            if node in visited:
                # 検査済み ➾ 枝切り
                return False

            # 未確定ノード
            visiting.add(node)

            # 全分岐を探索
            for child in self.children_of(node):
                if visit(child):
                    return True

            # この node を始点としたパスは検査完了
            visiting.remove(node)
            visited.add(node)

            return False

        # 全て順序制約における始点ノードを検査
        for node in [edge.before for edge in self.constraints]:
            if visit(node):
                # サイクル発見
                return True

        # サイクル見つからず
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

    def is_self_contradictory(self) -> bool:
        """自己矛盾かどうか"""
        return self.left == self.right


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

    def __str__(self) -> str:
        return f"{self.left.node.id}.eff[{self.left.effect_id}] ---> {self.right.node.id}.pre[{self.right.precondition_id}]"

    def validate(self, edges: PlanEdges, action_by_node: ActionByNode) -> None:
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

        # left effect と right precondition は同じ StateVariable を参照しているか
        if left_effect.state_variable != right_precondition.atom.state_variable:
            raise ValueError(
                "The left effect and right precondition must refer to the same "
                f"state variable: {left_effect.state_variable} != "
                f"{right_precondition.atom.state_variable}"
            )

        # left effect が right precondition を満たす構造になっているか
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
    ) -> bool:
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

    def __str__(self) -> str:
        result_strs: list[str] = []
        result_strs.append(f"V: {sorted(node.id for node in partial_plan.nodes)}")
        result_strs.append(
            "E: {" + ", ".join(f"{edge}" for edge in partial_plan.edges) + "}"
        )

        result_strs.append("act:")
        for node in sorted(partial_plan.act.keys(), key=lambda n: n.id):
            result_strs.append(f"  {node.id} = {partial_plan.act[node]}")
        result_strs.append("C:")
        for constraint in partial_plan.constraints:
            result_strs.append(f"  {constraint}")

        return "\n".join(result_strs)

    @property
    def plan_edges(self) -> PlanEdges:
        return PlanEdges(self.edges)

    def is_inconsistent(self) -> tuple[bool, str]:
        """p.55

        Returns:
            tuple[bool, str]: (is_inconsistent, reason)
        """
        plan_edges = self.plan_edges

        # サイクルチェック
        if plan_edges.has_cycle():
            return True, "has cycle"

        # 自己矛盾制約チェック
        for inequality_constraint in (
            ineq for ineq in self.constraints if isinstance(ineq, InequalityConstraint)
        ):
            if inequality_constraint.is_self_contradictory():
                return (
                    True,
                    f"has self contradictory constraint: {inequality_constraint}",
                )

        # 違反CausalLink制約チェック
        for causal_link in (
            cl for cl in self.constraints if isinstance(cl, CausalLink)
        ):
            # そもそも有効なのか
            causal_link.validate(plan_edges, self.act)

            # violates をチェック
            for node in self.nodes:
                if causal_link.violates(node, plan_edges, self.act):
                    return True, f"has violated causal link: {causal_link}"

        # 違反 action 引数チェック
        for action in self.act.values():
            for argument, parameter in zip(action.args, action.schema.head.parameters):
                if not parameter.can_be_instantiated_by(argument):
                    return True, f"has violated action argument: {action}"

        # consistent!
        return False, ""

    def is_consistent(self) -> tuple[bool, str]:
        result, reason = self.is_inconsistent()
        return not result, reason


# ---

if __name__ == "__main__":
    print("Example 3.11.")

    # --- domain ---

    type_name_objects = svr_model.TypeName("Objects")
    type_name_robots = svr_model.TypeName("Robots")
    type_name_docks = svr_model.TypeName("Docks")
    type_name_symbols = svr_model.TypeName("Symbols")

    r1 = svr_model.ObjectConstant("r1")
    r2 = svr_model.ObjectConstant("r2")
    d1 = svr_model.ObjectConstant("d1")
    d2 = svr_model.ObjectConstant("d2")
    d3 = svr_model.ObjectConstant("d3")
    nil = svr_model.ObjectConstant("nil")

    type_hierarchy = svr_model.TypeHierarchy(
        {
            type_name_objects: (
                {type_name_robots, type_name_docks, type_name_symbols},
                set(),
            ),
            type_name_robots: (set(), {r1, r2}),
            type_name_docks: (set(), {d1, d2, d3}),
            type_name_symbols: (set(), {nil}),
        }
    )

    robots = type_hierarchy.type_range(type_name_robots)
    docks = type_hierarchy.type_range(type_name_docks)
    symbols = type_hierarchy.type_range(type_name_symbols)

    rigid_relations = svr_model.RigidRelations({})

    # --- object variables ---

    param_r = svr_model.ObjectVariable(svr_model.ObjectVariableName("r"), robots)
    param_d = svr_model.ObjectVariable(svr_model.ObjectVariableName("d"), docks)
    param_d_prime = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("d_prime"), docks
    )

    arg_r = svr_model.ObjectVariable(svr_model.ObjectVariableName("r"), robots)
    arg_d = svr_model.ObjectVariable(svr_model.ObjectVariableName("d"), docks)

    # --- state variables ---

    state_var_loc = svr_model.StateVariableSchema(
        svr_model.StateVariableName("loc"),
        (param_r,),
        docks,
    )
    state_var_occupied = svr_model.StateVariableSchema(
        svr_model.StateVariableName("occupied"),
        (param_d,),
        robots | symbols,
    )

    def assign(
        schema: svr_model.StateVariableSchema,
        args: tuple[svr_model.ObjectTerm, ...],
        value: svr_model.ObjectTerm,
    ) -> svr_model.StateVariableAssignment:
        return svr_model.StateVariableAssignment(
            state_variable=svr_model.StateVariableExpr(schema, args),
            value=value,
        )

    def lit(
        assignment: svr_model.StateVariableAssignment,
        negated: bool = False,
    ) -> svr_fol.StateVariableLiteralExpr:
        return svr_fol.StateVariableLiteralExpr(assignment, negated)

    # --- action schema ---

    action_schema_move = svr_act.ActionSchema(
        head=svr_act.Head(
            name="move",
            parameters=(param_r, param_d, param_d_prime),
        ),
        preconditions=svr_act.Preconditions(
            literals=(
                lit(assign(state_var_loc, (param_r,), param_d)),
                lit(assign(state_var_occupied, (param_d_prime,), nil)),
            )
        ),
        effects=svr_act.Effects(
            effects=(
                assign(state_var_loc, (param_r,), param_d_prime),
                assign(state_var_occupied, (param_d,), nil),
                assign(state_var_occupied, (param_d_prime,), param_r),
            )
        ),
    )

    # === partial plan ===

    v1 = PlanNode(PlanNodeId("v1"))
    v2 = PlanNode(PlanNodeId("v2"))

    #   act(v1) = move(r, d2, d)
    #   act(v2) = move(r1, d1, d2)
    act_v1 = svr_act.ActionExpr(
        schema=action_schema_move,
        args=(arg_r, d2, arg_d),
    )
    act_v2 = svr_act.ActionExpr(
        schema=action_schema_move,
        args=(r1, d1, d2),
    )

    partial_plan = PartialPlan(
        nodes=frozenset({v1, v2}),
        edges=frozenset({PlanEdge(v1, v2)}),
        act={
            v1: act_v1,
            v2: act_v2,
        },
        constraints=frozenset(
            {
                CausalLink(
                    left=EffectRef(node=v1, effect_id=EffectIndex(1)),
                    right=PreconditionRef(
                        node=v2, precondition_id=PreconditionIndex(1)
                    ),
                )
            }
        ),
    )

    # 表示 ---

    print("\nDomain:")
    print("Type hierarchy:")
    print(type_hierarchy)
    print("\nRigid relations:")
    print(rigid_relations)
    print("\nAction schema:")
    print(action_schema_move)

    print("\nPartial plan:")
    print(partial_plan)

    print("\nConsistency check:")
    print(f"  is_consistent = {partial_plan.is_consistent()}")
