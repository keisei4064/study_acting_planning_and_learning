import state_transition_system.model as sts_model
import state_transition_system.problem as sts_prob
import forward_state_space_search.template as fsss_template
from typing import TypeAlias, Iterable


IntState: TypeAlias = int
IntAction: TypeAlias = sts_model.Action[IntState]


class IntDomain:
    pass


IntGoalFormula: TypeAlias = sts_prob.GoalFormula[IntState]
IntPlanningProblem: TypeAlias = sts_prob.PlanningProblem[IntState, IntDomain]


class AddOneAction(sts_model.Action[IntState]):
    def is_applicable(self, s: IntState) -> bool:
        return True

    def transition(self, s: IntState) -> IntState:
        return s + 1

    def __str__(self) -> str:
        return "+1"

class MultipleTwoAction(sts_model.Action[IntState]):
    def is_applicable(self, s: IntState) -> bool:
        return True

    def transition(self, s: IntState) -> IntState:
        return s * 2

    def __str__(self) -> str:
        return "×2"

class DivideTwoAction(sts_model.Action[IntState]):
    def is_applicable(self, s: IntState) -> bool:
        return s % 2 == 0

    def transition(self, s: IntState) -> IntState:
        return s // 2

    def __str__(self) -> str:
        return "÷2"

class ApplicableActionBuilder(
    fsss_template.ApplicableActionBuilder[IntDomain, IntState]
):
    def __call__(
        self,
        domain: IntDomain,
        state: IntState,
    ) -> Iterable[sts_model.Action[IntState]]:
        action_types: Iterable[type[sts_model.Action]] = [
            AddOneAction,
            MultipleTwoAction,
            DivideTwoAction,
        ]
        for ActionType in action_types:
            action = ActionType()
            if action.is_applicable(state):
                yield action
