from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, NewType, Protocol, Self, TypeVar, cast
from typing import Mapping
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

    def type_range(self, typename: TypeName) -> frozenset[ObjectConstant]:
        return self._type_dict[typename]

    def __str__(self):
        res_strs: list[str] = []
        for typename, objects in sorted(
            self._type_dict.items(), key=lambda item: len(item[1]), reverse=True
        ):
            res_strs.append(f"{typename}: {set(objects)}")
        return "\n".join(res_strs)


ObjectVariableName = NewType("ObjectVariableName", str)


# 変数の同一性は name ではなくインスタンス identity で判定する
@dataclass(frozen=True, eq=False)
class ObjectVariable:
    # 変数名と値域
    name: ObjectVariableName
    value_range: frozenset[ObjectConstant]

    def can_be_instantiated_by(self, value: ObjectTerm) -> bool:
        if isinstance(value, ObjectVariable):
            return value.value_range.issubset(self.value_range)
        return value in self.value_range


# ---


ObjectTerm = ObjectConstant | ObjectVariable


def object_term_to_str(term: ObjectTerm) -> str:
    if isinstance(term, ObjectVariable):
        return term.name
    else:
        return str(term)


TermSubstitutionMap = Mapping[ObjectVariable, ObjectTerm]


def substitute_object_term_if_mapped(
    term: ObjectTerm, substitution_map: TermSubstitutionMap
) -> ObjectTerm:
    """Map に従って，ObjectTerm を置き換える"""
    if isinstance(term, ObjectVariable) and term in substitution_map:
        return substitution_map[term]
    return term


# ---


class InstantiableExpression(Protocol):
    """ObjectVariable を含みうる式表現"""

    def _object_variables(self) -> frozenset[ObjectVariable]: ...

    def _substitute_terms(self, mapping: TermSubstitutionMap) -> Self: ...


InstantiableExpressionT = TypeVar(
    "InstantiableExpressionT",
    bound=InstantiableExpression,
)


def instantiate(
    expr: InstantiableExpressionT,
    mapping: TermSubstitutionMap,
) -> InstantiableExpressionT:
    """Def 2.5. Instantiating"""
    for var, term in mapping.items():
        if not var.can_be_instantiated_by(term):
            raise ValueError(
                f"The mapping input is invalid. Mapping: {mapping}, Variable: {var}, Term: {term}"
            )

    return expr._substitute_terms(mapping)


def is_ground(expr: InstantiableExpression) -> bool:
    return len(expr._object_variables()) == 0


# ---


RigidRelationName = NewType("RigidRelationName", str)


@dataclass(frozen=True)
class RigidRelationSchema:
    name: RigidRelationName
    arg_ranges: tuple[frozenset[ObjectConstant], ...]

    def __str__(self) -> str:
        ranges_strs: list[str] = []
        for arg_range in self.arg_ranges:
            ranges_strs.append("{" + ", ".join(arg_range) + "}")
        return f"{self.name}({', '.join(ranges_strs)})"


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
            instance_strs = ["(" + ", ".join(instance) + ")" for instance in instances]
            res += f"{schema}: \n  {', '.join(instance_strs)}" + "\n"
        return res

    def has_rigid_relation(self, schema: RigidRelationSchema) -> bool:
        return schema in self._rigid_relations

    def is_contained_in(
        self, schema: RigidRelationSchema, instance: tuple[ObjectConstant, ...]
    ) -> bool:
        return instance in self._rigid_relations[schema]


# ---


StateVariableName = NewType("StateVariableName", str)


@dataclass(frozen=True)
class StateVariableSchema:
    """StateVariable のスキーマ表現

    Example: len(r) \\in {'r1', 'r2', ...} の名前，引数の個数・値域，および変数自体の値域 を表現

    """

    name: StateVariableName
    args: tuple[ObjectVariable, ...]
    value_range: frozenset[ObjectConstant]

    def __str__(self) -> str:
        return f"{self.name}({', '.join(f'{arg.name} ∈ {set(arg.value_range)}' for arg in self.args)}) ∈ {set(self.value_range)}"


@dataclass(frozen=True)
class StateVariableExpr(InstantiableExpression):
    """StateVariable の実体．引数には ObjectVariable も許す

    Example: loc(r1) = d1 の `loc(r1)`部分のみを表現

    """

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
        args_str = ", ".join(object_term_to_str(arg) for arg in self.args)
        return f"{self.schema.name}({args_str})"

    def _object_variables(self) -> frozenset[ObjectVariable]:
        return frozenset(arg for arg in self.args if isinstance(arg, ObjectVariable))

    def _substitute_terms(self, mapping: TermSubstitutionMap) -> StateVariableExpr:
        new_args: list[ObjectTerm] = []
        for arg in self.args:
            new_args.append(substitute_object_term_if_mapped(arg, mapping))

        return StateVariableExpr(self.schema, tuple(new_args))


@dataclass(frozen=True)
class StateVariableAssignment(InstantiableExpression):
    """StateVariable に対する値の割り当てを表現

    Example: loc(r1) = d1 の全体を表現

    """

    state_variable: StateVariableExpr
    value: ObjectTerm

    def __post_init__(self) -> None:
        # `= value` にあたるvalue がStateVariableSchema の値域と適合するかチェック
        if isinstance(self.value, ObjectVariable):
            if not self.value.value_range.issubset(
                self.state_variable.schema.value_range
            ):
                raise ValueError(
                    "Invalid state variable assignment. "
                    f"The value range of {self.value} is not a subset of "
                    f"{self.state_variable.schema.value_range}."
                )
        else:
            if self.value not in self.state_variable.schema.value_range:
                raise ValueError(
                    "Invalid state variable assignment. "
                    f"{self.value} is not in {self.state_variable.schema.value_range}."
                )

    def __str__(self) -> str:
        return f"{self.state_variable} = {object_term_to_str(self.value)}"

    def _object_variables(self) -> frozenset[ObjectVariable]:
        if isinstance(self.value, ObjectVariable):
            return self.state_variable._object_variables().union({self.value})
        else:
            return self.state_variable._object_variables()

    def _substitute_terms(
        self, mapping: TermSubstitutionMap
    ) -> StateVariableAssignment:
        new_value = substitute_object_term_if_mapped(self.value, mapping)
        new_state_variable = self.state_variable._substitute_terms(mapping)
        return StateVariableAssignment(new_state_variable, new_value)


# ---


class StateVariableState:
    """Imutableです"""

    def __init__(
        self,
        state_variable_assignments: Iterable[StateVariableAssignment],
    ):
        """最初に登録するものが全て"""
        self._state_variable_expr_to_value: dict[StateVariableExpr, ObjectConstant] = {}
        for assignment in state_variable_assignments:
            if not is_ground(assignment):
                raise ValueError(
                    f"The state variable assignments: {assignment} which are passed to StateVariableState must be ground."
                )

            if assignment.state_variable in self._state_variable_expr_to_value:
                raise ValueError(
                    f"The state variable {assignment.state_variable} is already in the state."
                )

            self._state_variable_expr_to_value[assignment.state_variable] = cast(
                ObjectConstant, assignment.value
            )

    @classmethod
    def _from_mapping(
        cls,
        mapping: Mapping[StateVariableExpr, ObjectConstant],
    ) -> StateVariableState:
        obj = cls.__new__(cls)
        obj._state_variable_expr_to_value = dict(mapping)
        return obj

    def __str__(self) -> str:
        res_strs: list[str] = []
        for state_variable, value in self._state_variable_expr_to_value.items():
            res_strs.append(
                f"{state_variable.schema.name}{state_variable.args}: {value}"
            )
        return "\n".join(res_strs)

    def items(self) -> Iterator[tuple[StateVariableExpr, ObjectConstant]]:
        return iter(self._state_variable_expr_to_value.items())

    def has_state_variable(self, state_variable: StateVariableExpr) -> bool:
        return state_variable in self._state_variable_expr_to_value

    def get_value(self, state_variable: StateVariableExpr) -> ObjectConstant:
        return self._state_variable_expr_to_value[state_variable]

    def copy_with_assignment(
        self, assignment: StateVariableAssignment
    ) -> StateVariableState:
        return self.copy_with_assignments([assignment])

    def copy_with_assignments(
        self, assignments: Iterable[StateVariableAssignment]
    ) -> StateVariableState:
        new_state_variable_expr_to_value = self._state_variable_expr_to_value.copy()
        for assignment in assignments:
            if not is_ground(assignment):
                raise ValueError(
                    f"The state variable assignments: {assignment} which are passed to StateVariableState must be ground."
                )

            new_state_variable_expr_to_value[assignment.state_variable] = cast(
                ObjectConstant, assignment.value
            )
        return StateVariableState._from_mapping(new_state_variable_expr_to_value)


# ===


if __name__ == "__main__":
    """unground な state variable も表現できるか"""

    type_name_objects = TypeName("Objects")
    type_name_positions = TypeName("Positions")
    type_name_robots = TypeName("Robots")
    type_name_docks = TypeName("Docks")

    obj_const_r1 = ObjectConstant("r1")
    obj_const_r2 = ObjectConstant("r2")
    obj_const_d1 = ObjectConstant("d1")
    obj_const_d2 = ObjectConstant("d2")
    obj_const_d3 = ObjectConstant("d3")

    type_hierarchy = TypeHierarchy(
        {
            type_name_objects: (
                {
                    type_name_positions,
                },
                set(),
            ),
            type_name_positions: (
                {
                    type_name_robots,
                    type_name_docks,
                },
                set(),
            ),
            type_name_robots: (
                set(),
                {
                    obj_const_r1,
                    obj_const_r2,
                },
            ),
            type_name_docks: (
                set(),
                {
                    obj_const_d1,
                    obj_const_d2,
                    obj_const_d3,
                },
            ),
        }
    )

    obj_var_r = ObjectVariable(
        ObjectVariableName("r"),
        type_hierarchy.type_range(type_name_robots),
    )

    state_var_schema_loc = StateVariableSchema(
        StateVariableName("loc"),
        (obj_var_r,),
        type_hierarchy.type_range(type_name_docks),
    )

    ungrounded_loc = StateVariableExpr(state_var_schema_loc, (obj_var_r,))

    print("ungrounded loc: ")
    print(ungrounded_loc)
    pprint.pprint(ungrounded_loc)
