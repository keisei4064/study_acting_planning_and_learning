import state_variable_representation.planning_domain as svr_domain
import state_transition_system.problem as sts_prob
import state_variable_representation.model as svr_model
from typing import TypeAlias


class DWRPlanningDomain(svr_domain.StateVariablePlanningDomain):
    pass


class DWRState(svr_model.StateVariableState):
    pass


DWRPlanningProblem: TypeAlias = sts_prob.PlanningProblem[DWRState, DWRPlanningDomain]
