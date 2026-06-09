import dataclasses
import state_variable_representation.model as svr_model
import state_variable_representation.action as svr_act
import state_variable_representation.first_order_logic as svr_fol
import state_transition_system.problem as sts_prob
from typing import TypeAlias


@dataclasses.dataclass(frozen=True)
class StateVariablePlanningDomain:
    """Σ = (𝑆, 𝐴, 𝛾, cost) = (H , 𝑅, 𝑋, A) | p.22"""

    type_hierarchy: svr_model.TypeHierarchy
    rigid_relations: svr_model.RigidRelations
    state_variable_schemas: tuple[svr_model.StateVariableSchema, ...]
    action_schemas: tuple[svr_act.ActionSchema, ...]


@dataclasses.dataclass(frozen=True)
class GoalFormula:
    literals: tuple[svr_fol.StateVariableLiteralExpr, ...]

    def evaluate(self, state: svr_model.StateVariableState) -> bool:
        return all(literal.evaluate(state) for literal in self.literals)

    def __call__(self, state: svr_model.StateVariableState) -> bool:
        return self.evaluate(state)

    def __str__(self) -> str:
        return " ∧ ".join(str(literal) for literal in self.literals)


StateVariablePlanningProblem: TypeAlias = sts_prob.PlanningProblem[
    svr_model.StateVariableState,
    StateVariablePlanningDomain,
]
"""𝑃 = (Σ, 𝑠_0, 𝑔)"""
