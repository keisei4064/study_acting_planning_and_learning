import forward_state_space_search.template as fsss_template
import state_variable_representation.model as svr_model
import state_variable_representation.action as svr_act
import state_variable_representation.planning_domain as svr_domain
import state_transition_system.model as sts_model
from typing import Iterable, Iterator
import itertools


def iter_ground_args(
    parameters: tuple[svr_model.ObjectVariable, ...],
) -> Iterator[tuple[svr_model.ObjectTerm, ...]]:
    """Action の引数情報から，具体的な組み合わせを順に返す"""
    value_ranges: tuple[tuple[svr_model.ObjectConstant, ...], ...] = tuple(
        tuple(sorted(parameter.value_range, key=str)) for parameter in parameters
    )

    # 直積
    for args in itertools.product(*value_ranges):
        yield args


class ApplicableActionBuilder(
    fsss_template.ApplicableActionBuilder[
        svr_domain.StateVariablePlanningDomain, svr_model.StateVariableState
    ]
):
    """現在の状態に対して適用可能な Action を返す"""

    def __call__(
        self,
        domain: svr_domain.StateVariablePlanningDomain,
        state: svr_model.StateVariableState,
    ) -> Iterable[sts_model.Action[svr_model.StateVariableState]]:
        # 全 Action候補を走査
        for action in domain.action_schemas:
            # 引数の全組み合わせ集合（直積）を順に試す
            for args in iter_ground_args(action.head.parameters):
                # 実体化
                action_expr = svr_act.ActionExpr(action, args)
                grounded_action = svr_act.GroundAction.try_build(
                    action_expr, domain.rigid_relations
                )
                if grounded_action is not None and grounded_action.is_applicable(state):
                    # 適用可能なアクションを返却
                    yield grounded_action
