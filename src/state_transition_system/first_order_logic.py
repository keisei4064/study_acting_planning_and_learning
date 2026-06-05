from __future__ import annotations

from dataclasses import dataclass

import state_transition_system.state_variable_repr as svrepr


@dataclass(frozen=True)
class RigidRelationAssertion:
    RididRelationSchema: svrepr.RigidRelationSchema
    args: tuple[svrepr.ObjectTerm, ...]

    def is_ground(self) -> bool:
        return all(not isinstance(arg, svrepr.ObjectVariable) for arg in self.args)


@dataclass
class AtomExpr:
    expr: svrepr.StateVariableAssignment | RigidRelationAssertion
    negated: bool = False

    # def eval(self, state: svrepr.State) -> bool:
    #     match self.expr:
    #         case svrepr.StateVariableAssignment(state_variable, value):
    #             return state._state_variable_expr_to_value[state_variable] == value
    #         case RigidRelationAssertion(RigidRelationSchema, args):
    #             return args in state._rigid_relations[RigidRelationSchema]
