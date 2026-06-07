from __future__ import annotations

from dataclasses import dataclass
from typing import cast
import state_variable_representation.model as svr_model


@dataclass(frozen=True)
class RigidRelationAssertion(svr_model.InstantiableExpression):
    rigid_relation_schema: svr_model.RigidRelationSchema
    args: tuple[svr_model.ObjectTerm, ...]

    def __post_init__(self) -> None:
        if len(self.args) != len(self.rigid_relation_schema.arg_ranges):
            raise ValueError(
                "Invalid rigid relation assertion. "
                f"The number of arguments does not match: "
                f"{len(self.args)} != {len(self.rigid_relation_schema.arg_ranges)}"
            )

        for arg, arg_range in zip(self.args, self.rigid_relation_schema.arg_ranges):
            if isinstance(arg, svr_model.ObjectVariable):
                if not arg.value_range.issubset(arg_range):
                    raise ValueError(
                        f"Invalid rigid relation assertion. "
                        f"The value range of {arg} is not a subset of {arg_range}."
                    )
                continue

            if arg not in arg_range:
                raise ValueError(
                    f"Invalid rigid relation assertion. {arg} is not in {arg_range}."
                )

    def _object_variables(self) -> frozenset[svr_model.ObjectVariable]:
        return frozenset(
            arg for arg in self.args if isinstance(arg, svr_model.ObjectVariable)
        )

    def _substitute_terms(
        self, mapping: svr_model.TermSubstitutionMap
    ) -> RigidRelationAssertion:
        return RigidRelationAssertion(
            self.rigid_relation_schema,
            tuple(
                svr_model.substitute_object_term_if_mapped(arg, mapping)
                for arg in self.args
            ),
        )

    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args)
        return f"{self.rigid_relation_schema.name}({args_str})"

    def as_ground_args(self) -> tuple[svr_model.ObjectConstant, ...]:
        if not svr_model.is_ground(self):
            raise ValueError(
                f"The unground rigid relation assertion {self} cannot be converted to ground arguments."
            )

        return cast(tuple[svr_model.ObjectConstant, ...], self.args)


@dataclass(frozen=True)
class StateVariableLiteralExpr(svr_model.InstantiableExpression):
    """StateVariableAssignment を atom に持つ literal"""

    atom: svr_model.StateVariableAssignment
    negated: bool = False

    def __str__(self) -> str:
        """否定の記号は '¬'"""
        args_str = ", ".join(
            svr_model.object_term_to_str(arg) for arg in self.atom.state_variable.args
        )
        value_str = svr_model.object_term_to_str(self.atom.value)
        atom_str = f"{self.atom.state_variable.schema.name}({args_str}) = {value_str}"
        return f"{'¬' if self.negated else ''}{atom_str}"

    def _object_variables(self) -> frozenset[svr_model.ObjectVariable]:
        return self.atom._object_variables()

    def _substitute_terms(
        self, mapping: svr_model.TermSubstitutionMap
    ) -> StateVariableLiteralExpr:
        return StateVariableLiteralExpr(
            self.atom._substitute_terms(mapping), self.negated
        )

    def evaluate(self, state: svr_model.StateVariableState) -> bool:
        if not svr_model.is_ground(self.atom):
            raise ValueError(
                f"The unground state variable expression {self.atom} cannot be evaluated."
            )

        if not state.has_state_variable(self.atom.state_variable):
            raise ValueError(
                f"The state variable {self.atom.state_variable} is not in the state."
            )

        if self.negated:
            return state.get_value(self.atom.state_variable) != self.atom.value
        else:
            return state.get_value(self.atom.state_variable) == self.atom.value


@dataclass(frozen=True)
class RigidRelationLiteralExpr(svr_model.InstantiableExpression):
    """RigidRelationAssertion を atom に持つ literal"""

    atom: RigidRelationAssertion
    negated: bool = False

    def __str__(self) -> str:
        """否定の記号は '¬'"""
        args_str = ", ".join(
            svr_model.object_term_to_str(arg) for arg in self.atom.args
        )
        atom_str = f"{self.atom.rigid_relation_schema.name}({args_str})"
        return f"{'¬' if self.negated else ''}{atom_str}"

    def _object_variables(self) -> frozenset[svr_model.ObjectVariable]:
        return self.atom._object_variables()

    def _substitute_terms(
        self, mapping: svr_model.TermSubstitutionMap
    ) -> RigidRelationLiteralExpr:
        return RigidRelationLiteralExpr(
            self.atom._substitute_terms(mapping), self.negated
        )

    def evaluate(self, rigid_relations: svr_model.RigidRelations) -> bool:
        if not svr_model.is_ground(self.atom):
            raise ValueError(
                f"The unground rigid relation expression {self.atom} cannot be evaluated."
            )

        if not rigid_relations.has_rigid_relation(self.atom.rigid_relation_schema):
            raise ValueError(
                f"The rigid relation {self.atom.rigid_relation_schema} is not in the rigid relations."
            )

        if self.negated:
            return not rigid_relations.is_contained_in(
                self.atom.rigid_relation_schema, self.atom.as_ground_args()
            )
        else:
            return rigid_relations.is_contained_in(
                self.atom.rigid_relation_schema, self.atom.as_ground_args()
            )


LiteralExpr = StateVariableLiteralExpr | RigidRelationLiteralExpr
"""Literal : 原子式 (atom) またはその否定"""


def evaluate_literal_expr(
    literal: LiteralExpr,
    state: svr_model.StateVariableState,
    rigid_relations: svr_model.RigidRelations,
) -> bool:
    """literal を評価する"""
    return (
        literal.evaluate(state)
        if isinstance(literal, StateVariableLiteralExpr)
        else literal.evaluate(rigid_relations)
    )
