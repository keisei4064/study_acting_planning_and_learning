from __future__ import annotations

import dataclasses
import abc
from typing import Generic, TypeVar


StateT = TypeVar("StateT")
"""状態を表す型変数"""


class Action(abc.ABC, Generic[StateT]):
    @abc.abstractmethod
    def is_applicable(self, s: StateT) -> bool: ...

    @abc.abstractmethod
    def transition(self, s: StateT) -> StateT | None: ...

    @property
    def cost(self) -> float:
        return 1


# @dataclasses.dataclass
# class StateTransitionSystem(Generic[StateT]):
#     """Σ = (𝑆, 𝐴, 𝛾, cost)"""

#     states: tuple[StateT]
#     actions: tuple[Action[StateT]]


@dataclasses.dataclass
class Plan(Generic[StateT]):
    """𝜋"""

    actions: list[Action[StateT]]

    @property
    def length(self) -> int:
        return len(self.actions)

    def cost(self) -> float:
        return sum([a.cost for a in self.actions])

    def subplan(self, from_index: int, to_index: int) -> Plan[StateT]:
        return Plan(actions=self.actions[from_index:to_index])

    def prefix(self, to_index: int) -> Plan[StateT]:
        return Plan(actions=self.actions[:to_index])

    def suffix(self, from_index: int) -> Plan[StateT]:
        return Plan(actions=self.actions[from_index:])

    def concatenate_to_front(self, other: Action[StateT] | Plan[StateT]):
        match other:
            case Action():
                self.actions.insert(0, other)
            case Plan():
                self.actions = other.actions + self.actions

    def concatenate_to_back(self, other: Action[StateT] | Plan[StateT]):
        match other:
            case Action():
                self.actions.append(other)
            case Plan():
                self.actions += other.actions


def transition_by_action(s: StateT, a: Action[StateT]) -> StateT | None:
    if not a.is_applicable(s):
        return None

    return a.transition(s)


def transition_by_plan(s: StateT, pi: Plan[StateT]) -> StateT | None:
    new_s = s
    for a in pi.actions:
        if new_s is None:
            return None
        new_s = transition_by_action(new_s, a)

    return new_s


@dataclasses.dataclass
class TransitiveClosure(Generic[StateT]):
    states: list[StateT]
    pi: Plan[StateT]

    @classmethod
    def try_build(
        cls, s0: StateT, pi: Plan[StateT]
    ) -> TransitiveClosure[StateT] | None:
        states: list[StateT] = [s0]

        for a in pi.actions:
            s = states[-1]
            if not a.is_applicable(s):
                return None
            new_s = transition_by_action(s, a)
            assert new_s is not None
            states.append(new_s)

        return TransitiveClosure(states=states, pi=pi)

    @property
    def length(self) -> int:
        return len(self.states)

    def cost(self) -> float:
        return self.pi.cost()
