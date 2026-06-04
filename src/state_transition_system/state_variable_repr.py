from typing import NewType, TypeAlias
import logging
import pprint
from dataclasses import dataclass

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
class RigidRelation:
    # 関係名と組の集合
    name: RigidRelationName
    pairs: frozenset[tuple[ObjectConstant, ObjectConstant]]


# ---


ObjectTerm = ObjectConstant | ObjectVariable


@dataclass(frozen=True)
class Substitution:
    # 変数名と値
    name: ObjectVariableName
    value: ObjectConstant


StateVariableName = NewType("StateVariableName", str)


@dataclass(frozen=True)
class StateVariableSchema:
    name: StateVariableName
    args: tuple[ObjectVariable, ...]
    value_range: frozenset[ObjectConstant]


@dataclass(frozen=True)
class StateVariableExpr:
    name: StateVariableName
    args: tuple[ObjectTerm, ...]


class StateVariables:
    def __init__(self, schemas: list[StateVariableSchema]):
        self._schema_dict: dict[StateVariableName, StateVariableSchema] = {}
        self._variable_exprs: set[StateVariableExpr] = set()
        for schema in schemas:
            self._schema_dict[schema.name] = schema

    def verify_and_register_expr(self, expr: StateVariableExpr) -> StateVariableExpr:
        schema = self._schema_dict[expr.name]
        assert len(expr.args) == len(schema.args)
        for arg, arg_schema in zip(expr.args, schema.args):
            assert arg in arg_schema.value_range

        self._variable_exprs.add(expr)

        return expr


@dataclass(frozen=True)
class StateVariableAssignment:
    expr: StateVariableExpr
    value: ObjectTerm


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

    rigid_rel_adjacent = RigidRelation(
        RigidRelationName("adjacent"),
        frozenset(
            {
                (ObjectConstant("d1"), ObjectConstant("d2")),
                (ObjectConstant("d2"), ObjectConstant("d1")),
                (ObjectConstant("d2"), ObjectConstant("d3")),
                (ObjectConstant("d3"), ObjectConstant("d2")),
                (ObjectConstant("d3"), ObjectConstant("d1")),
                (ObjectConstant("d1"), ObjectConstant("d3")),
            }
        ),
    )
    rigid_rel_at = RigidRelation(
        RigidRelationName("at"),
        frozenset(
            {
                (ObjectConstant("p1"), ObjectConstant("d1")),
                (ObjectConstant("p2"), ObjectConstant("d2")),
                (ObjectConstant("p3"), ObjectConstant("d2")),
            }
        ),
    )

    rigid_relations: set[RigidRelation] = {rigid_rel_adjacent, rigid_rel_at}
    print("rigid_relations:")
    pprint.pprint(rigid_relations)

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

    state_var_cargo = StateVariableSchema(
        StateVariableName("cargo"),
        (obj_var_r,),
        containers | frozenset({nil}),
    )
    state_var_loc = StateVariableSchema(
        StateVariableName("loc"),
        (obj_var_r,),
        docks,
    )
    state_var_occupied = StateVariableSchema(
        StateVariableName("occupied"),
        (obj_var_d,),
        frozenset({true, false}),
    )
    state_var_pile = StateVariableSchema(
        StateVariableName("pile"),
        (obj_var_c,),
        piles | frozenset({nil}),
    )
    state_var_pos = StateVariableSchema(
        StateVariableName("pos"),
        (obj_var_c,),
        robots | containers | frozenset({nil}),
    )
    state_var_top = StateVariableSchema(
        StateVariableName("top"),
        (obj_var_p,),
        containers | frozenset({nil}),
    )

    state_variables = [
        state_var_cargo,
        state_var_loc,
        state_var_occupied,
        state_var_pile,
        state_var_pos,
        state_var_top,
    ]

    print("state_variables:")
    pprint.pprint(state_variables)
