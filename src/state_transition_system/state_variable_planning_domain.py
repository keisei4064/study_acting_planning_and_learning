import dataclasses
import state_transition_system.state_variable_repr as stssvr
import state_transition_system.action_schema as stsact
import state_transition_system.first_order_logic as stsfol
import state_transition_system.problem as stsprob
from typing import TypeAlias


@dataclasses.dataclass
class StateVariablePlanningDomain:
    """Σ = (𝑆, 𝐴, 𝛾, cost) = (H , 𝑅, 𝑋, A) | p.22"""

    type_hierarchy: stssvr.TypeHierarchy
    rigid_relations: stssvr.RigidRelations
    state_variables: tuple[stssvr.StateVariableSchema]
    action_schemas: tuple[stsact.ActionSchema]


@dataclasses.dataclass(frozen=True)
class GoalFormula:
    literals: tuple[stsfol.StateVariableLiteralExpr, ...]

    def evaluate(self, state: stssvr.StateVariableState) -> bool:
        return all(literal.evaluate(state) for literal in self.literals)

    def __call__(self, state: stssvr.StateVariableState) -> bool:
        return self.evaluate(state)


StateVariablePlanningProblem: TypeAlias = stsprob.PlanningProblem[
    stssvr.StateVariableState,
    StateVariablePlanningDomain,
]
"""𝑃 = (Σ, 𝑠_0, 𝑔)"""
