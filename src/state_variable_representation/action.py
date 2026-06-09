from __future__ import annotations

import state_variable_representation.model as svr_model
import state_variable_representation.first_order_logic as svr_fol
import state_transition_system.model as sts_model
import dataclasses
import logging


@dataclasses.dataclass(frozen=True)
class Head:
    """Def 2.7."""

    name: str
    parameters: tuple[svr_model.ObjectVariable, ...]

    def __str__(self) -> str:
        args_str = ", ".join(arg.name for arg in self.parameters)
        return f"{self.name}({args_str})"


@dataclasses.dataclass(frozen=True)
class Preconditions:
    literals: tuple[svr_fol.LiteralExpr, ...]

    def __str__(self) -> str:
        result = "pre: "
        result += ", ".join(str(literal) for literal in self.literals)
        return result


@dataclasses.dataclass(frozen=True)
class Effects:
    effects: tuple[svr_model.StateVariableAssignment, ...]

    def __str__(self) -> str:
        result = "eff: "
        effect_strs: list[str] = []
        for effect in self.effects:
            state_variable_str = str(effect.state_variable)
            value_str = svr_model.object_term_to_str(effect.value)
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
class ActionExpr(svr_model.InstantiableExpression):
    schema: ActionSchema
    args: tuple[svr_model.ObjectTerm, ...]

    def __str__(self) -> str:
        args_str = ", ".join(svr_model.object_term_to_str(arg) for arg in self.args)
        return f"{self.schema.head.name}({args_str})"

    def __post_init__(self):
        if len(self.args) != len(self.schema.head.parameters):
            raise ValueError(
                "Invalid action instance expression. "
                f"The number of arguments does not match: "
                f"{len(self.args)} != {len(self.schema.head.parameters)}"
            )

        for arg, schema_arg in zip(self.args, self.schema.head.parameters):
            if isinstance(arg, svr_model.ObjectVariable):
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

    def _object_variables(self) -> frozenset[svr_model.ObjectVariable]:
        return frozenset(
            arg for arg in self.args if isinstance(arg, svr_model.ObjectVariable)
        )

    def _substitute_terms(self, mapping: svr_model.TermSubstitutionMap) -> ActionExpr:
        return ActionExpr(
            schema=self.schema,
            args=tuple(
                svr_model.substitute_object_term_if_mapped(arg, mapping)
                for arg in self.args
            ),
        )

    def get_parameter_substitution_map(self) -> svr_model.TermSubstitutionMap:
        return {
            parameter: arg
            for parameter, arg in zip(self.schema.head.parameters, self.args)
        }


# ---


@dataclasses.dataclass(frozen=True)
class GroundAction(sts_model.Action[svr_model.StateVariableState]):
    expr: ActionExpr
    state_preconditions: tuple[svr_fol.StateVariableLiteralExpr, ...]
    grounded_effects: tuple[svr_model.StateVariableAssignment, ...]

    def __str__(self) -> str:
        result = f"{self.expr}\n"
        result += "  pre: "
        result += ", ".join(
            str(precondition) for precondition in self.state_preconditions
        )
        result += "\n"
        result += "  eff: "
        result += ", ".join(
            f"{effect.state_variable} ← {svr_model.object_term_to_str(effect.value)}"
            for effect in self.grounded_effects
        )
        result += "\n"
        result += f"  cost: {self.cost}"
        return result

    @classmethod
    def try_build(
        cls, expr: ActionExpr, rigid_relations: svr_model.RigidRelations
    ) -> GroundAction | None:
        # ActionExpr の引数が全て ground かどうか
        if not svr_model.is_ground(expr):
            logging.warning(
                f"Action expression {expr} ({expr.schema}) is not ground. GroundAction is not built."
            )
            return None

        # パラメータ -> 代入引数 のマッピング
        substitution_map = expr.get_parameter_substitution_map()

        # precondition を ground にする
        state_preconditions: list[svr_fol.StateVariableLiteralExpr] = []
        for precondition in expr.schema.preconditions.literals:
            match precondition:
                case svr_fol.StateVariableLiteralExpr():
                    state_preconditions.append(
                        svr_model.instantiate(precondition, substitution_map)
                    )
                # RigidRelation Assertion はこの時点で処理
                case svr_fol.RigidRelationLiteralExpr():
                    if not svr_model.instantiate(
                        precondition, substitution_map
                    ).evaluate(rigid_relations):
                        logging.warning(
                            f"Rigid relation precondition {precondition} is not satisfied."
                        )
                        return None

        # effect を ground にする
        grounded_effects: list[svr_model.StateVariableAssignment] = []
        for effect in expr.schema.effects.effects:
            grounded_effect = svr_model.instantiate(effect, substitution_map)
            if not svr_model.is_ground(grounded_effect):
                logging.warning(
                    f"Effect {grounded_effect} is not ground. GroundAction is not built."
                )
                return None
            grounded_effects.append(grounded_effect)

        # 構築可能
        return cls(
            expr=expr,
            state_preconditions=tuple(state_preconditions),
            grounded_effects=tuple(grounded_effects),
        )

    def is_applicable(self, s: svr_model.StateVariableState) -> bool:
        return svr_model.is_ground(self.expr) and all(
            precondition.evaluate(s) for precondition in self.state_preconditions
        )

    def transition(
        self, s: svr_model.StateVariableState
    ) -> svr_model.StateVariableState | None:
        """p.20,21 式(2.15)"""
        if not self.is_applicable(s):
            return None

        return s.copy_with_assignments(self.grounded_effects)

    @property
    def cost(self) -> float:
        return self.expr.schema.cost.value
