from __future__ import annotations
import state_transition_system.state_variable_repr as svrepr
from typing import Callable, TypeAlias


TermMapper: TypeAlias = Callable[[svrepr.ObjectTerm], svrepr.ObjectTerm]


def instantiate():
    pass


class BindingTable:
    pass
