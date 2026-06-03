import typing
import dataclasses
import enum
from typing import TypeAlias, NewType
import logging

ObjectName = NewType("ObjectName", str)
TypeName = NewType("TypeName", str)


class TypeHierarchy:
    def __init__(
        self, type_tree_structure: dict[TypeName, tuple[set[TypeName], set[ObjectName]]]
    ):
        self._type_dict: dict[TypeName, frozenset[ObjectName]] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        unresolved = set(type_tree_structure.keys())
        resolved = set()
        is_progress = False
        while len(unresolved) > 0:
            is_progress = False
            for typename in unresolved:
                subtypes, objects = type_tree_structure[typename]
                if not subtypes.issubset(resolved):
                    continue

                # 直接の子要素と，子型に含まれる要素の和集合を登録
                self._type_dict[typename] = frozenset(objects).union(
                    *[self._type_dict[subtype] for subtype in subtypes]
                )

                resolved.add(typename)
                unresolved = unresolved - resolved
                is_progress = True

            if not is_progress:
                raise ValueError(
                    "The TypeHierarchy input is invalid. Unresolved types: %s"
                    % unresolved
                )

    def type_set(self, typename: TypeName) -> frozenset[ObjectName]:
        return self._type_dict[typename]


# @dataclasses.dataclass(frozen=True)
# class RigidRelation:
#     adjacentset: set[tuple[ObjectName, ObjectName]]
#     at: set[tuple[ObjectName, ObjectName]]


# StateVariableName: TypeAlias = str

# StateKey: TypeAlias = tuple[StateVariableName, tuple[ObjectName, ...]]
# State: TypeAlias = dict[StateKey, ObjectName]

if __name__ == "__main__":
    type_hierarchy = TypeHierarchy(
        {
            TypeName("Objects"): (
                {
                    TypeName("Positions"),
                    TypeName("Containers"),
                    TypeName("Piles"),
                    TypeName("Symbols"),
                },
                set(),
            ),
            TypeName("Positions"): (
                {
                    TypeName("Robots"),
                    TypeName("Docks"),
                },
                {
                    ObjectName("nil"),
                },
            ),
            TypeName("Symbols"): (
                set(),
                {
                    ObjectName("T"),
                    ObjectName("F"),
                    ObjectName("nil"),
                },
            ),
            TypeName("Containers"): (
                set(),
                {
                    ObjectName("c1"),
                    ObjectName("c2"),
                    ObjectName("c3"),
                },
            ),
            TypeName("Piles"): (
                set(),
                {
                    ObjectName("p1"),
                    ObjectName("p2"),
                    ObjectName("p3"),
                },
            ),
            TypeName("Robots"): (
                set(),
                {
                    ObjectName("r1"),
                    ObjectName("r2"),
                },
            ),
            TypeName("Docks"): (
                set(),
                {
                    ObjectName("d1"),
                    ObjectName("d2"),
                    ObjectName("d3"),
                },
            ),
        }
    )
    print(type_hierarchy._type_dict)
    print(f"Positions: {type_hierarchy.type_set(TypeName('Positions'))}")
    print(f"Containers: {type_hierarchy.type_set(TypeName('Containers'))}")
    print(f"Piles: {type_hierarchy.type_set(TypeName('Piles'))}")
    print(f"Symbols: {type_hierarchy.type_set(TypeName('Symbols'))}")
    print(f"Robots: {type_hierarchy.type_set(TypeName('Robots'))}")
    print(f"Docks: {type_hierarchy.type_set(TypeName('Docks'))}")
