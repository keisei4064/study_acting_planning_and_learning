from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class LiteralExpr(stssvr.InstantiableExpression):
    """原子式 (atom) またはその否定"""

    atom: stssvr.StateVariableAssignment | RigidRelationAssertion
    negated: bool = False

    def __str__(self) -> str:
        """否定の記号は '¬'"""
        match self.atom:
            case stssvr.StateVariableAssignment(
                state_variable=state_variable, value=value
            ):
                args_str = ", ".join(stssvr.object_term_to_str(arg) for arg in state_variable.args)
                value_str = stssvr.object_term_to_str(value)
                atom_str = (
                    f"{state_variable.schema.name}({args_str}) = {value_str}"
                )
            case RigidRelationAssertion(
                rigid_relation_schema=rigid_relation_schema, args=args
            ):
                args_str = ", ".join(stssvr.object_term_to_str(arg) for arg in args)
                atom_str = f"{rigid_relation_schema.name}({args_str})"
            case _:
                atom_str = str(self.atom)
        return f"{'¬' if self.negated else ''}{atom_str}"

    def _object_variables(self) -> frozenset[stssvr.ObjectVariable]:
        return self.atom._object_variables()

    def _substitute_terms(self, mapping: stssvr.TermSubstitutionMap) -> LiteralExpr:
        return LiteralExpr(self.atom._substitute_terms(mapping), self.negated)

    # def eval(self, state: svrepr.State) -> bool:
    #     match self.expr:
    #         case svrepr.StateVariableAssignment(state_variable, value):
    #             return state._state_variable_expr_to_value[state_variable] == value
    #         case RigidRelationAssertion(RigidRelationSchema, args):
    #             return args in state._rigid_relations[RigidRelationSchema]
