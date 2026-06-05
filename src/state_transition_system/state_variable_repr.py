from __future__ import annotations

from dataclasses import dataclass
from typing import NewType
import logging
import pprint

ObjectConstant = NewType("ObjectConstant", str)
TypeName = NewType("TypeName", str)


class TypeHierarchy:
    def __init__(
        self,
        type_tree_structure: dict[TypeName, tuple[set[TypeName], set[ObjectConstant]]],
    ):
        self._type_dict: dict[TypeName, frozenset[ObjectConstant]] = {}
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

    def type_set(self, typename: TypeName) -> frozenset[ObjectConstant]:
        return self._type_dict[typename]


ObjectVariableName = NewType("ObjectVariableName", str)


@dataclass(frozen=True)
class ObjectVariable:
    # 変数名と値域
    name: ObjectVariableName
    value_range: frozenset[ObjectConstant]


RigidRelationName = NewType("RigidRelationName", str)


@dataclass(frozen=True)
class RigidRelationSchema:
    name: RigidRelationName
    arg_ranges: tuple[frozenset[ObjectConstant], ...]


class RigidRelations:
    def __init__(
        self,
        rigid_relations: dict[RigidRelationSchema, set[tuple[ObjectConstant, ...]]],
    ):
        self._rigid_relations: dict[
            RigidRelationSchema, frozenset[tuple[ObjectConstant, ...]]
        ] = {}
        self._schema_by_name: dict[RigidRelationName, RigidRelationSchema] = {}

        for schema, instances in rigid_relations.items():
            if schema.name in self._schema_by_name:
                raise ValueError(
                    f"The RigidRelation input is invalid. Duplicate relation name: {schema.name}"
                )

            for instance in instances:
                if len(instance) != len(schema.arg_ranges):
                    raise ValueError(
                        f"The RigidRelation input is invalid. Schema: {schema}, Instance: {instance}"
                    )
                for arg, arg_range in zip(instance, schema.arg_ranges):
                    if arg not in arg_range:
                        raise ValueError(
                            f"The RigidRelation input is invalid. Schema: {schema}, Instance: {instance}"
                        )

            self._schema_by_name[schema.name] = schema
            self._rigid_relations[schema] = frozenset(instances)

    def __str__(self) -> str:
        res: str = ""
        for schema, instances in self._rigid_relations.items():
            res += f"{schema.name}({schema.arg_ranges}): {instances}\n"
        return res


# ---


ObjectTerm = ObjectConstant | ObjectVariable


StateVariableName = NewType("StateVariableName", str)


@dataclass(frozen=True)
class StateVariableSchema:
    """型としての表現

    例: len(r) \in {'r1', 'r2', ...}

    """

    name: StateVariableName
    args: tuple[ObjectVariable, ...]
    value_range: frozenset[ObjectConstant]


@dataclass(frozen=True)
class StateVariableExpr:
    """StateVariable の実体．引数には ObjectVariable も許す（部分実体化）"""

    schema: StateVariableSchema
    args: tuple[ObjectTerm, ...]

    def __post_init__(self) -> None:
        if len(self.args) != len(self.schema.args):
            raise ValueError(
                "Invalid state variable expression. "
                f"The number of arguments does not match: "
                f"{len(self.args)} != {len(self.schema.args)}"
            )

        for arg, schema_arg in zip(self.args, self.schema.args):
            if isinstance(arg, ObjectVariable):
                if not arg.value_range.issubset(schema_arg.value_range):
                    raise ValueError(
                        "Invalid state variable expression. "
                        f"The value range of {arg} is not a subset of "
                        f"{schema_arg.value_range}."
                    )
            else:
                if arg not in schema_arg.value_range:
                    raise ValueError(
                        "Invalid state variable expression. "
                        f"{arg} is not in {schema_arg.value_range}."
                    )

    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args)
        return f"{self.schema.name}({args_str})"

    def is_ground(self) -> bool:
        return all(not isinstance(arg, ObjectVariable) for arg in self.args)


@dataclass(frozen=True)
class StateVariableAssignment:
    state_variable: StateVariableExpr
    value: ObjectTerm


class State:
    def __init__(
        self,
        state_variable_assignments: list[StateVariableAssignment],
        rigid_relations: RigidRelations,
    ):
        """最初に登録するものが全て"""
        self._state_variable_expr_to_value: dict[StateVariableExpr, ObjectTerm] = {}
        for assignment in state_variable_assignments:
            self._state_variable_expr_to_value[assignment.state_variable] = (
                assignment.value
            )

        self._rigid_relations = rigid_relations

    def __str__(self) -> str:
        res: str = ""
        res += "Rigid Relations:\n" + str(self._rigid_relations)

        res += "\n"
        res += "State Variables:\n"
        for state_variable, value in self._state_variable_expr_to_value.items():
            res += f"{state_variable.schema.name}{state_variable.args}: {value}\n"
        return res


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
                    ObjectConstant("nil"),
                },
            ),
            TypeName("Symbols"): (
                set(),
                {
                    ObjectConstant("T"),
                    ObjectConstant("F"),
                    ObjectConstant("nil"),
                },
            ),
            TypeName("Containers"): (
                set(),
                {
                    ObjectConstant("c1"),
                    ObjectConstant("c2"),
                    ObjectConstant("c3"),
                },
            ),
            TypeName("Piles"): (
                set(),
                {
                    ObjectConstant("p1"),
                    ObjectConstant("p2"),
                    ObjectConstant("p3"),
                },
            ),
            TypeName("Robots"): (
                set(),
                {
                    ObjectConstant("r1"),
                    ObjectConstant("r2"),
                },
            ),
            TypeName("Docks"): (
                set(),
                {
                    ObjectConstant("d1"),
                    ObjectConstant("d2"),
                    ObjectConstant("d3"),
                },
            ),
        }
    )

    pprint.pprint(type_hierarchy._type_dict)
    print(f"Positions: {type_hierarchy.type_set(TypeName('Positions'))}")
    print(f"Containers: {type_hierarchy.type_set(TypeName('Containers'))}")
    print(f"Piles: {type_hierarchy.type_set(TypeName('Piles'))}")
    print(f"Symbols: {type_hierarchy.type_set(TypeName('Symbols'))}")
    print(f"Robots: {type_hierarchy.type_set(TypeName('Robots'))}")
    print(f"Docks: {type_hierarchy.type_set(TypeName('Docks'))}")

    print("---")
    # ---

    rigid_rel_adjacent = RigidRelationSchema(
        RigidRelationName("adjacent"),
        (
            type_hierarchy.type_set(TypeName("Docks")),
            type_hierarchy.type_set(TypeName("Docks")),
        ),
    )
    rigid_rel_at = RigidRelationSchema(
        RigidRelationName("at"),
        (
            type_hierarchy.type_set(TypeName("Piles")),
            type_hierarchy.type_set(TypeName("Docks")),
        ),
    )

    rigid_relations = RigidRelations(
        {
            rigid_rel_adjacent: {
                (ObjectConstant("d1"), ObjectConstant("d2")),
                (ObjectConstant("d2"), ObjectConstant("d1")),
                (ObjectConstant("d2"), ObjectConstant("d3")),
                (ObjectConstant("d3"), ObjectConstant("d2")),
                (ObjectConstant("d3"), ObjectConstant("d1")),
                (ObjectConstant("d1"), ObjectConstant("d3")),
            },
            rigid_rel_at: {
                (ObjectConstant("p1"), ObjectConstant("d1")),
                (ObjectConstant("p2"), ObjectConstant("d2")),
                (ObjectConstant("p3"), ObjectConstant("d2")),
            },
        }
    )
    print("rigid_relations:\n", rigid_relations)

    print("---")
    # ---

    obj_var_r = ObjectVariable(
        ObjectVariableName("r"),
        type_hierarchy.type_set(TypeName("Robots")),
    )
    obj_var_d = ObjectVariable(
        ObjectVariableName("d"),
        type_hierarchy.type_set(TypeName("Docks")),
    )
    obj_var_c = ObjectVariable(
        ObjectVariableName("c"),
        type_hierarchy.type_set(TypeName("Containers")),
    )
    obj_var_p = ObjectVariable(
        ObjectVariableName("p"),
        type_hierarchy.type_set(TypeName("Piles")),
    )
    object_variables = [obj_var_r, obj_var_d, obj_var_c, obj_var_p]

    print("object_variables:")
    pprint.pprint(object_variables)

    print("---")
    # ---

    nil = ObjectConstant("nil")
    true = ObjectConstant("T")
    false = ObjectConstant("F")

    containers = type_hierarchy.type_set(TypeName("Containers"))
    robots = type_hierarchy.type_set(TypeName("Robots"))
    docks = type_hierarchy.type_set(TypeName("Docks"))
    piles = type_hierarchy.type_set(TypeName("Piles"))

    state_var_schema_cargo = StateVariableSchema(
        StateVariableName("cargo"),
        (obj_var_r,),
        containers | frozenset({nil}),
    )
    state_var_schema_loc = StateVariableSchema(
        StateVariableName("loc"),
        (obj_var_r,),
        docks,
    )
    state_var_schema_occupied = StateVariableSchema(
        StateVariableName("occupied"),
        (obj_var_d,),
        frozenset({true, false}),
    )
    state_var_schema_pile = StateVariableSchema(
        StateVariableName("pile"),
        (obj_var_c,),
        piles | frozenset({nil}),
    )
    state_var_schema_pos = StateVariableSchema(
        StateVariableName("pos"),
        (obj_var_c,),
        robots | containers | frozenset({nil}),
    )
    state_var_schema_top = StateVariableSchema(
        StateVariableName("top"),
        (obj_var_p,),
        containers | frozenset({nil}),
    )

    state_variables = [
        state_var_schema_cargo,
        state_var_schema_loc,
        state_var_schema_occupied,
        state_var_schema_pile,
        state_var_schema_pos,
        state_var_schema_top,
    ]

    print("state_variables:")
    pprint.pprint(state_variables)

    # ---
    # Example 2.4 を表現

    r1 = ObjectConstant("r1")
    r2 = ObjectConstant("r2")

    d1 = ObjectConstant("d1")
    d2 = ObjectConstant("d2")
    d3 = ObjectConstant("d3")

    c1 = ObjectConstant("c1")
    c2 = ObjectConstant("c2")
    c3 = ObjectConstant("c3")

    p1 = ObjectConstant("p1")
    p2 = ObjectConstant("p2")
    p3 = ObjectConstant("p3")

    s0 = State(
        [
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_cargo, (r1,)),
                nil,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_cargo, (r2,)),
                nil,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_loc, (r1,)),
                d1,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_loc, (r2,)),
                d2,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_occupied, (d1,)),
                true,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_occupied, (d2,)),
                true,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_occupied, (d3,)),
                false,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_pile, (c1,)),
                p1,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_pile, (c2,)),
                p1,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_pile, (c3,)),
                p2,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_pos, (c1,)),
                c2,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_pos, (c2,)),
                nil,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_pos, (c3,)),
                nil,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_top, (p1,)),
                c1,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_top, (p2,)),
                c3,
            ),
            StateVariableAssignment(
                StateVariableExpr(state_var_schema_top, (p3,)),
                nil,
            ),
        ],
        rigid_relations,
    )

    print("---")
    print("s0:")
    print(s0)
    # pprint.pprint(s0)
    # for expr, value in s0.items():
    #     print(f"{expr} = {value}")

    print("---")
    # ---

    ungrounded_loc = StateVariableExpr(state_var_schema_loc, (obj_var_r,))
    print(f"ungrounded_loc: {ungrounded_loc}")
    # ---
