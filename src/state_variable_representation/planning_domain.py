import dataclasses
import state_variable_representation.state_variable_repr as svrsvr
import state_variable_representation.action_schema as svract
import state_variable_representation.first_order_logic as svrfol
import state_transition_system.problem as stsprob
from typing import TypeAlias


@dataclasses.dataclass
class StateVariablePlanningDomain:
    """Σ = (𝑆, 𝐴, 𝛾, cost) = (H , 𝑅, 𝑋, A) | p.22"""

    type_hierarchy: svrsvr.TypeHierarchy
    rigid_relations: svrsvr.RigidRelations
    state_variables: tuple[svrsvr.StateVariableSchema]
    action_schemas: tuple[svract.ActionSchema]


@dataclasses.dataclass(frozen=True)
class GoalFormula:
    literals: tuple[svrfol.StateVariableLiteralExpr, ...]

    def evaluate(self, state: svrsvr.StateVariableState) -> bool:
        return all(literal.evaluate(state) for literal in self.literals)

    def __call__(self, state: svrsvr.StateVariableState) -> bool:
        return self.evaluate(state)


StateVariablePlanningProblem: TypeAlias = stsprob.PlanningProblem[
    svrsvr.StateVariableState,
    StateVariablePlanningDomain,
]
"""𝑃 = (Σ, 𝑠_0, 𝑔)"""
