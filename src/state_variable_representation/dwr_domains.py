import state_variable_representation.model as svr_model
import dataclasses
from typing import Self


@dataclasses.dataclass(frozen=True)
class DWRDomain:
    type_hierarchy: svr_model.TypeHierarchy
    rigid_rel_adjacent: svr_model.RigidRelationSchema
    rigid_rel_at: svr_model.RigidRelationSchema
    rigid_relations: svr_model.RigidRelations

    state_var_cargo: svr_model.StateVariableSchema
    state_var_loc: svr_model.StateVariableSchema
    state_var_occupied: svr_model.StateVariableSchema
    state_var_pile: svr_model.StateVariableSchema
    state_var_pos: svr_model.StateVariableSchema
    state_var_top: svr_model.StateVariableSchema

    @classmethod
    def build(cls) -> Self:
        type_hierarchy = svr_model.TypeHierarchy(
            {
                svr_model.TypeName("Objects"): (
                    {
                        svr_model.TypeName("Positions"),
                        svr_model.TypeName("Containers"),
                        svr_model.TypeName("Piles"),
                        svr_model.TypeName("Symbols"),
                    },
                    set(),
                ),
                svr_model.TypeName("Positions"): (
                    {
                        svr_model.TypeName("Robots"),
                        svr_model.TypeName("Docks"),
                    },
                    {
                        svr_model.ObjectConstant("nil"),
                    },
                ),
                svr_model.TypeName("Symbols"): (
                    set(),
                    {
                        svr_model.ObjectConstant("T"),
                        svr_model.ObjectConstant("F"),
                        svr_model.ObjectConstant("nil"),
                    },
                ),
                svr_model.TypeName("Containers"): (
                    set(),
                    {
                        svr_model.ObjectConstant("c1"),
                        svr_model.ObjectConstant("c2"),
                        svr_model.ObjectConstant("c3"),
                    },
                ),
                svr_model.TypeName("Piles"): (
                    set(),
                    {
                        svr_model.ObjectConstant("p1"),
                        svr_model.ObjectConstant("p2"),
                        svr_model.ObjectConstant("p3"),
                    },
                ),
                svr_model.TypeName("Robots"): (
                    set(),
                    {
                        svr_model.ObjectConstant("r1"),
                        svr_model.ObjectConstant("r2"),
                    },
                ),
                svr_model.TypeName("Docks"): (
                    set(),
                    {
                        svr_model.ObjectConstant("d1"),
                        svr_model.ObjectConstant("d2"),
                        svr_model.ObjectConstant("d3"),
                    },
                ),
            }
        )

        docks = type_hierarchy.type_set(svr_model.TypeName("Docks"))
        piles = type_hierarchy.type_set(svr_model.TypeName("Piles"))

        rigid_rel_adjacent = svr_model.RigidRelationSchema(
            svr_model.RigidRelationName("adjacent"),
            (docks, docks),
        )

        rigid_rel_at = svr_model.RigidRelationSchema(
            svr_model.RigidRelationName("at"),
            (piles, docks),
        )

        rigid_relations = svr_model.RigidRelations(
            {
                rigid_rel_adjacent: {
                    (svr_model.ObjectConstant("d1"), svr_model.ObjectConstant("d2")),
                    (svr_model.ObjectConstant("d2"), svr_model.ObjectConstant("d1")),
                    (svr_model.ObjectConstant("d2"), svr_model.ObjectConstant("d3")),
                    (svr_model.ObjectConstant("d3"), svr_model.ObjectConstant("d2")),
                    (svr_model.ObjectConstant("d3"), svr_model.ObjectConstant("d1")),
                    (svr_model.ObjectConstant("d1"), svr_model.ObjectConstant("d3")),
                },
                rigid_rel_at: {
                    (svr_model.ObjectConstant("p1"), svr_model.ObjectConstant("d1")),
                    (svr_model.ObjectConstant("p2"), svr_model.ObjectConstant("d2")),
                    (svr_model.ObjectConstant("p3"), svr_model.ObjectConstant("d2")),
                },
            }
        )

        nil = svr_model.ObjectConstant("nil")
        true = svr_model.ObjectConstant("T")
        false = svr_model.ObjectConstant("F")

        containers = type_hierarchy.type_set(svr_model.TypeName("Containers"))
        robots = type_hierarchy.type_set(svr_model.TypeName("Robots"))
        docks = type_hierarchy.type_set(svr_model.TypeName("Docks"))
        piles = type_hierarchy.type_set(svr_model.TypeName("Piles"))

        containers_or_nil = containers | frozenset({nil})

        schema_r = svr_model.ObjectVariable(svr_model.ObjectVariableName("r"), robots)
        schema_d = svr_model.ObjectVariable(svr_model.ObjectVariableName("d"), docks)
        schema_c = svr_model.ObjectVariable(
            svr_model.ObjectVariableName("c"), containers
        )
        schema_p = svr_model.ObjectVariable(svr_model.ObjectVariableName("p"), piles)

        state_var_cargo = svr_model.StateVariableSchema(
            svr_model.StateVariableName("cargo"),
            (schema_r,),
            containers_or_nil,
        )

        state_var_loc = svr_model.StateVariableSchema(
            svr_model.StateVariableName("loc"),
            (schema_r,),
            docks,
        )

        state_var_occupied = svr_model.StateVariableSchema(
            svr_model.StateVariableName("occupied"),
            (schema_d,),
            frozenset({true, false}),
        )

        state_var_pile = svr_model.StateVariableSchema(
            svr_model.StateVariableName("pile"),
            (schema_c,),
            piles | frozenset({nil}),
        )

        state_var_pos = svr_model.StateVariableSchema(
            svr_model.StateVariableName("pos"),
            (schema_c,),
            robots | containers | frozenset({nil}),
        )

        state_var_top = svr_model.StateVariableSchema(
            svr_model.StateVariableName("top"),
            (schema_p,),
            containers_or_nil,
        )

        return cls(
            type_hierarchy=type_hierarchy,
            rigid_rel_adjacent=rigid_rel_adjacent,
            rigid_rel_at=rigid_rel_at,
            rigid_relations=rigid_relations,
            state_var_cargo=state_var_cargo,
            state_var_loc=state_var_loc,
            state_var_occupied=state_var_occupied,
            state_var_pile=state_var_pile,
            state_var_pos=state_var_pos,
            state_var_top=state_var_top,
        )

    @property
    def objects(self) -> frozenset[svr_model.ObjectConstant]:
        return self.type_hierarchy.type_set(svr_model.TypeName("Objects"))

    @property
    def positions(self) -> frozenset[svr_model.ObjectConstant]:
        return self.type_hierarchy.type_set(svr_model.TypeName("Positions"))

    @property
    def containers(self) -> frozenset[svr_model.ObjectConstant]:
        return self.type_hierarchy.type_set(svr_model.TypeName("Containers"))

    @property
    def piles(self) -> frozenset[svr_model.ObjectConstant]:
        return self.type_hierarchy.type_set(svr_model.TypeName("Piles"))

    @property
    def symbols(self) -> frozenset[svr_model.ObjectConstant]:
        return self.type_hierarchy.type_set(svr_model.TypeName("Symbols"))

    @property
    def robots(self) -> frozenset[svr_model.ObjectConstant]:
        return self.type_hierarchy.type_set(svr_model.TypeName("Robots"))

    @property
    def docks(self) -> frozenset[svr_model.ObjectConstant]:
        return self.type_hierarchy.type_set(svr_model.TypeName("Docks"))
