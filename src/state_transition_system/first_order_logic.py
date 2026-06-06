from __future__ import annotations

from dataclasses import dataclass
from typing import cast
import state_transition_system.state_variable_repr as stssvr


@dataclass(frozen=True)
class RigidRelationAssertion(stssvr.InstantiableExpression):
    rigid_relation_schema: stssvr.RigidRelationSchema
    args: tuple[stssvr.ObjectTerm, ...]

    def __post_init__(self) -> None:
        if len(self.args) != len(self.rigid_relation_schema.arg_ranges):
            raise ValueError(
                "Invalid rigid relation assertion. "
                f"The number of arguments does not match: "
                f"{len(self.args)} != {len(self.rigid_relation_schema.arg_ranges)}"
            )

        for arg, arg_range in zip(self.args, self.rigid_relation_schema.arg_ranges):
            if isinstance(arg, stssvr.ObjectVariable):
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

    def _object_variables(self) -> frozenset[stssvr.ObjectVariable]:
        return frozenset(
            arg for arg in self.args if isinstance(arg, stssvr.ObjectVariable)
        )

    def _substitute_terms(
        self, mapping: stssvr.TermSubstitutionMap
    ) -> RigidRelationAssertion:
        return RigidRelationAssertion(
            self.rigid_relation_schema,
            tuple(
                stssvr.substitute_object_term_if_mapped(arg, mapping)
                for arg in self.args
            ),
        )

    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args)
        return f"{self.rigid_relation_schema.name}({args_str})"

    def as_ground_args(self) -> tuple[stssvr.ObjectConstant, ...]:
        if not stssvr.is_ground(self):
            raise ValueError(
                f"The unground rigid relation assertion {self} cannot be converted to ground arguments."
            )

        return cast(tuple[stssvr.ObjectConstant, ...], self.args)


@dataclass(frozen=True)
class StateVariableLiteralExpr(stssvr.InstantiableExpression):
    """StateVariableAssignment を atom に持つ literal"""

    atom: stssvr.StateVariableAssignment
    negated: bool = False

    def __str__(self) -> str:
        """否定の記号は '¬'"""
        args_str = ", ".join(
            stssvr.object_term_to_str(arg) for arg in self.atom.state_variable.args
        )
        value_str = stssvr.object_term_to_str(self.atom.value)
        atom_str = f"{self.atom.state_variable.schema.name}({args_str}) = {value_str}"
        return f"{'¬' if self.negated else ''}{atom_str}"

    def _object_variables(self) -> frozenset[stssvr.ObjectVariable]:
        return self.atom._object_variables()

    def _substitute_terms(
        self, mapping: stssvr.TermSubstitutionMap
    ) -> StateVariableLiteralExpr:
        return StateVariableLiteralExpr(
            self.atom._substitute_terms(mapping), self.negated
        )

    def evaluate(self, state: stssvr.StateVariableState) -> bool:
        if not stssvr.is_ground(self.atom):
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
class RigidRelationLiteralExpr(stssvr.InstantiableExpression):
    """RigidRelationAssertion を atom に持つ literal"""

    atom: RigidRelationAssertion
    negated: bool = False

    def __str__(self) -> str:
        """否定の記号は '¬'"""
        args_str = ", ".join(stssvr.object_term_to_str(arg) for arg in self.atom.args)
        atom_str = f"{self.atom.rigid_relation_schema.name}({args_str})"
        return f"{'¬' if self.negated else ''}{atom_str}"

    def _object_variables(self) -> frozenset[stssvr.ObjectVariable]:
        return self.atom._object_variables()

    def _substitute_terms(
        self, mapping: stssvr.TermSubstitutionMap
    ) -> RigidRelationLiteralExpr:
        return RigidRelationLiteralExpr(
            self.atom._substitute_terms(mapping), self.negated
        )

    def evaluate(self, rigid_relations: stssvr.RigidRelations) -> bool:
        if not stssvr.is_ground(self.atom):
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
    state: stssvr.StateVariableState,
    rigid_relations: stssvr.RigidRelations,
) -> bool:
    """literal を評価する"""
    return (
        literal.evaluate(state)
        if isinstance(literal, StateVariableLiteralExpr)
        else literal.evaluate(rigid_relations)
    )
