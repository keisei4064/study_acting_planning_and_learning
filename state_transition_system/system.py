from __future__ import annotations

import dataclasses
import abc


class State:
    pass


class Action(abc.ABC):
    @abc.abstractmethod
    def is_applicable(self, s: State) -> bool:
        pass

    @abc.abstractmethod
    def transition(self, s: State) -> State | None:
        pass

    @property
    def cost(self) -> float:
        return 1


@dataclasses.dataclass
class StateTransitionSystem:
    """Σ = (𝑆, 𝐴, 𝛾, cost)"""

    states: tuple[State]
    actions: tuple[Action]


def applicable_actions(system: StateTransitionSystem, s: State):
    return [a for a in system.actions if a.is_applicable(s)]


@dataclasses.dataclass
class Plan:
    """𝜋"""

    actions: list[Action]

    @property
    def length(self) -> int:
        return len(self.actions)

    def cost(self) -> float:
        return sum([a.cost for a in self.actions])

    def prefix(self, to_index: int) -> Plan:
        return Plan(actions=self.actions[:to_index])

    def suffix(self, from_index: int) -> Plan:
        return Plan(actions=self.actions[from_index:])

    def concatnate_to_front(self, other: Action | Plan):
        match other:
            case Action():
                self.actions.insert(0, other)
            case Plan():
                self.actions = other.actions + self.actions

    def concatnate_to_back(self, other: Action | Plan):
        match other:
            case Action():
                self.actions.insert(-1, other)
            case Plan():
                self.actions += other.actions


def transition(s: State, a: Action) -> State | None:
    if not a.is_applicable(s):
        return None


def transtion(s: State, pi: Plan) -> State | None:
    new_s = s
    for a in pi.actions:
        if new_s is None:
            return None
        new_s = transition(new_s, a)

    return new_s


@dataclasses.dataclass
class TransitiveClosure:
    states: list[State]
    pi: Plan

    @classmethod
    def try_build(cls, s0: State, pi: Plan) -> TransitiveClosure | None:
        states: list[State] = [s0]

        for a in pi.actions:
            s = states[-1]
            if not a.is_applicable(s):
                return None
            new_s = transition(s, a)
            assert new_s is not None
            states.append(new_s)

        return TransitiveClosure(states=states, pi=pi)

    @property
    def length(self) -> int:
        return len(self.states)

    def cost(self) -> float:
        return self.pi.cost()
