from typing import TypeAlias
import dataclasses
import plan_space_planning.model as psp_model


@dataclasses.dataclass(frozen=True)
class OpenGoal:
    precondition: psp_model.PreconditionRef


class Threat:
    causal_link: psp_model.CausalLink
    node: psp_model.PlanNode


Flaw: TypeAlias = OpenGoal | Threat


class Resolver:
    pass
