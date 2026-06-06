from __future__ import annotations
from typing import cast

import state_transition_system.state_variable_repr as stssvr
import state_transition_system.first_order_logic as stsfol
import state_transition_system.system as stssystem
import dataclasses
import logging


@dataclasses.dataclass(frozen=True)
class Head:
    """Def 2.7."""

    name: str
    parameters: tuple[stssvr.ObjectVariable, ...]

    def __str__(self) -> str:
        args_str = ", ".join(arg.name for arg in self.parameters)
        return f"{self.name}({args_str})"


@dataclasses.dataclass(frozen=True)
class Preconditions:
    literals: tuple[stsfol.LiteralExpr, ...]

    def __str__(self) -> str:
        result = "pre: "
        result += ", ".join(str(literal) for literal in self.literals)
        return result


@dataclasses.dataclass(frozen=True)
class Effects:
    effects: tuple[stssvr.StateVariableAssignment, ...]

    def __str__(self) -> str:
        result = "eff: "
        effect_strs: list[str] = []
        for effect in self.effects:
            state_variable_str = str(effect.state_variable)
            value_str = stssvr.object_term_to_str(effect.value)
            effect_strs.append(f"{state_variable_str} ← {value_str}")
        result += ", ".join(effect_strs)
        return result


@dataclasses.dataclass(frozen=True)
class Cost:
    value: float = 1

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Cost must be non-negative.")

    def __str__(self) -> str:
        return f"cost: {self.value}"


@dataclasses.dataclass(frozen=True)
class ActionSchema:
    head: Head
    preconditions: Preconditions
    effects: Effects
    cost: Cost = Cost()

    def __post_init__(self):
        # pre の引数チェック
        for precondition in self.preconditions.literals:
            for var_arg in precondition.atom._object_variables():
                if var_arg not in self.head.parameters:
                    raise ValueError(
                        f"Precondition argument: {var_arg} is not a parameter of the head: {self.head.parameters}"
                    )

        # eff の引数チェック
        for effect in self.effects.effects:
            for var_arg in effect._object_variables():
                if var_arg not in self.head.parameters:
                    raise ValueError(
                        f"Effect argument: {var_arg} is not a parameter of the head: {self.head.parameters}"
                    )

    def __str__(self) -> str:
        result = f"{self.head}\n"
        result += f"  {self.preconditions}\n"
        result += f"  {self.effects}\n"
        result += f"  {self.cost}"
        return result


# ---


@dataclasses.dataclass(frozen=True)
class ActionExpr(stssvr.InstantiableExpression):
    schema: ActionSchema
    args: tuple[stssvr.ObjectTerm, ...]

    def __str__(self) -> str:
        args_str = ", ".join(stssvr.object_term_to_str(arg) for arg in self.args)
        return f"{self.schema.head.name}({args_str})"

    def __post_init__(self):
        if len(self.args) != len(self.schema.head.parameters):
            raise ValueError(
                "Invalid action instance expression. "
                f"The number of arguments does not match: "
                f"{len(self.args)} != {len(self.schema.head.parameters)}"
            )

        for arg, schema_arg in zip(self.args, self.schema.head.parameters):
            if isinstance(arg, stssvr.ObjectVariable):
                if not arg.value_range.issubset(schema_arg.value_range):
                    raise ValueError(
                        "Invalid action instance expression. "
                        f"The value range of {arg} is not a subset of "
                        f"{schema_arg.value_range}."
                    )
            else:
                if arg not in schema_arg.value_range:
                    raise ValueError(
                        "Invalid action instance expression. "
                        f"{arg} is not in {schema_arg.value_range}."
                    )

    def _object_variables(self) -> frozenset[stssvr.ObjectVariable]:
        return frozenset(
            arg for arg in self.args if isinstance(arg, stssvr.ObjectVariable)
        )

    def _substitute_terms(self, mapping: stssvr.TermSubstitutionMap) -> ActionExpr:
        return ActionExpr(
            schema=self.schema,
            args=tuple(
                stssvr.substitute_object_term_if_mapped(arg, mapping)
                for arg in self.args
            ),
        )


# ---


@dataclasses.dataclass(frozen=True)
class GroundAction(stssystem.Action[stssvr.StateVariableState]):
    expr: ActionExpr
    state_preconditions: tuple[stsfol.StateVariableLiteralExpr, ...]

    @classmethod
    def try_build(
        cls, expr: ActionExpr, rigid_relations: stssvr.RigidRelations
    ) -> GroundAction | None:
        # ActionExpr がそもそも ground かどうか
        if not stssvr.is_ground(expr):
            logging.warning(
                f"Ground action cannot be built from non-ground action expression: {expr}"
            )
            return None

        state_preconditions: list[stsfol.StateVariableLiteralExpr] = []

        # RigidRelation Assertion はこの時点で処理
        for precondition in expr.schema.preconditions.literals:
            match precondition:
                case stsfol.StateVariableLiteralExpr():
                    state_preconditions.append(precondition)
                case stsfol.RigidRelationLiteralExpr():
                    if not precondition.evaluate(rigid_relations):
                        logging.warning(
                            f"Rigid relation precondition {precondition} is not satisfied."
                        )
                        return None
                    continue

        # 構築可能
        return cls(expr=expr, state_preconditions=tuple(state_preconditions))

    def is_applicable(self, s: stssvr.StateVariableState) -> bool:
        return stssvr.is_ground(self.expr) and all(
            precondition.evaluate(s) for precondition in self.state_preconditions
        )

    def transition(
        self, s: stssvr.StateVariableState
    ) -> stssvr.StateVariableState | None:
        if not self.is_applicable(s):
            return None

        for effect in self.expr.schema.effects.effects:
            s.set_value(
                effect.state_variable, cast(stssvr.ObjectConstant, effect.value)
            )

        return s

    @property
    def cost(self) -> float:
        return self.expr.schema.cost.value


# ---

# TODO
# PlanningDomain / StateVariableDomain
#   - type_hierarchy
#   - object sets
#   - state_variable_schemas
#   - rigid_relation_schemas
#   - rigid_relations
#   - action_schemas

# ---

if __name__ == "__main__":
    import state_transition_system.dwr_domains as stsdwr_domains

    dwr_domain = stsdwr_domains.DWRDomain.build()

    print(f"Objects: {dwr_domain.objects}")
    print(f"Positions: {dwr_domain.positions}")
    print(f"Containers: {dwr_domain.containers}")
    print(f"Piles: {dwr_domain.piles}")
    print(f"Symbols: {dwr_domain.symbols}")
    print(f"Robots: {dwr_domain.robots}")
    print(f"Docks: {dwr_domain.docks}")

    print("rigid_relations:\n", dwr_domain.rigid_relations)

    # ---
    print()
    print("--- Example 2.8 action schemas ---")

    nil = stssvr.ObjectConstant("nil")
    true = stssvr.ObjectConstant("T")
    false = stssvr.ObjectConstant("F")

    containers = dwr_domain.containers
    containers_or_nil = containers | frozenset({nil})
    docks = dwr_domain.docks
    piles = dwr_domain.piles
    robots = dwr_domain.robots

    # Action schema 用の object variables.
    r = stssvr.ObjectVariable(
        stssvr.ObjectVariableName("r"),
        robots,
    )
    c = stssvr.ObjectVariable(
        stssvr.ObjectVariableName("c"),
        containers,
    )
    c_prime = stssvr.ObjectVariable(
        stssvr.ObjectVariableName("c'"),
        containers_or_nil,
    )
    d = stssvr.ObjectVariable(
        stssvr.ObjectVariableName("d"),
        docks,
    )
    d_prime = stssvr.ObjectVariable(
        stssvr.ObjectVariableName("d'"),
        docks,
    )
    p = stssvr.ObjectVariable(
        stssvr.ObjectVariableName("p"),
        piles,
    )

    # ---

    state_var_cargo = dwr_domain.state_var_cargo
    state_var_loc = dwr_domain.state_var_loc
    state_var_occupied = dwr_domain.state_var_occupied
    state_var_pile = dwr_domain.state_var_pile
    state_var_pos = dwr_domain.state_var_pos
    state_var_top = dwr_domain.state_var_top

    def assign(
        schema: stssvr.StateVariableSchema,
        args: tuple[stssvr.ObjectTerm, ...],
        value: stssvr.ObjectTerm,
    ) -> stssvr.StateVariableAssignment:
        return stssvr.StateVariableAssignment(
            state_variable=stssvr.StateVariableExpr(schema, args),
            value=value,
        )

    def literal(
        atom: stssvr.StateVariableAssignment | stsfol.RigidRelationAssertion,
        negated: bool = False,
    ) -> stsfol.LiteralExpr:
        if isinstance(atom, stssvr.StateVariableAssignment):
            return stsfol.StateVariableLiteralExpr(atom, negated)
        else:
            return stsfol.RigidRelationLiteralExpr(atom, negated)

    # --- take(r, c, c', p, d) ---

    take = ActionSchema(
        head=Head(
            name="take",
            parameters=(r, c, c_prime, p, d),
        ),
        preconditions=Preconditions(
            literals=(
                literal(
                    stsfol.RigidRelationAssertion(
                        dwr_domain.rigid_rel_at,
                        (p, d),
                    )
                ),
                literal(assign(state_var_cargo, (r,), nil)),
                literal(assign(state_var_loc, (r,), d)),
                literal(assign(state_var_pos, (c,), c_prime)),
                literal(assign(state_var_top, (p,), c)),
            )
        ),
        effects=Effects(
            effects=(
                assign(state_var_cargo, (r,), c),
                assign(state_var_pile, (c,), nil),
                assign(state_var_pos, (c,), r),
                assign(state_var_top, (p,), c_prime),
            )
        ),
    )

    # --- put(r, c, c', p, d) ---

    put = ActionSchema(
        head=Head(
            name="put",
            parameters=(r, c, c_prime, p, d),
        ),
        preconditions=Preconditions(
            literals=(
                literal(
                    stsfol.RigidRelationAssertion(
                        dwr_domain.rigid_rel_at,
                        (p, d),
                    )
                ),
                literal(assign(state_var_pos, (c,), r)),
                literal(assign(state_var_loc, (r,), d)),
                literal(assign(state_var_top, (p,), c_prime)),
            )
        ),
        effects=Effects(
            effects=(
                assign(state_var_cargo, (r,), nil),
                assign(state_var_pile, (c,), p),
                assign(state_var_pos, (c,), c_prime),
                assign(state_var_top, (p,), c),
            )
        ),
    )

    # --- move(r, d, d') ---

    move = ActionSchema(
        head=Head(
            name="move",
            parameters=(r, d, d_prime),
        ),
        preconditions=Preconditions(
            literals=(
                literal(
                    stsfol.RigidRelationAssertion(
                        dwr_domain.rigid_rel_adjacent,
                        (d, d_prime),
                    )
                ),
                literal(assign(state_var_loc, (r,), d)),
                literal(assign(state_var_occupied, (d_prime,), false)),
            )
        ),
        effects=Effects(
            effects=(
                assign(state_var_loc, (r,), d_prime),
                assign(state_var_occupied, (d,), false),
                assign(state_var_occupied, (d_prime,), true),
            )
        ),
    )

    for action_schema in (take, put, move):
        print(action_schema)
        print()
