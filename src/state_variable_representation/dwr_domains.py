import state_variable_representation.state_variable_repr as svrsvr
import dataclasses
from typing import Self


@dataclasses.dataclass(frozen=True)
class DWRDomain:
    type_hierarchy: svrsvr.TypeHierarchy
    rigid_rel_adjacent: svrsvr.RigidRelationSchema
    rigid_rel_at: svrsvr.RigidRelationSchema
    rigid_relations: svrsvr.RigidRelations

    state_var_cargo: svrsvr.StateVariableSchema
    state_var_loc: svrsvr.StateVariableSchema
    state_var_occupied: svrsvr.StateVariableSchema
    state_var_pile: svrsvr.StateVariableSchema
    state_var_pos: svrsvr.StateVariableSchema
    state_var_top: svrsvr.StateVariableSchema

    @classmethod
    def build(cls) -> Self:
        type_hierarchy = svrsvr.TypeHierarchy(
            {
                svrsvr.TypeName("Objects"): (
                    {
                        svrsvr.TypeName("Positions"),
                        svrsvr.TypeName("Containers"),
                        svrsvr.TypeName("Piles"),
                        svrsvr.TypeName("Symbols"),
                    },
                    set(),
                ),
                svrsvr.TypeName("Positions"): (
                    {
                        svrsvr.TypeName("Robots"),
                        svrsvr.TypeName("Docks"),
                    },
                    {
                        svrsvr.ObjectConstant("nil"),
                    },
                ),
                svrsvr.TypeName("Symbols"): (
                    set(),
                    {
                        svrsvr.ObjectConstant("T"),
                        svrsvr.ObjectConstant("F"),
                        svrsvr.ObjectConstant("nil"),
                    },
                ),
                svrsvr.TypeName("Containers"): (
                    set(),
                    {
                        svrsvr.ObjectConstant("c1"),
                        svrsvr.ObjectConstant("c2"),
                        svrsvr.ObjectConstant("c3"),
                    },
                ),
                svrsvr.TypeName("Piles"): (
                    set(),
                    {
                        svrsvr.ObjectConstant("p1"),
                        svrsvr.ObjectConstant("p2"),
                        svrsvr.ObjectConstant("p3"),
                    },
                ),
                svrsvr.TypeName("Robots"): (
                    set(),
                    {
                        svrsvr.ObjectConstant("r1"),
                        svrsvr.ObjectConstant("r2"),
                    },
                ),
                svrsvr.TypeName("Docks"): (
                    set(),
                    {
                        svrsvr.ObjectConstant("d1"),
                        svrsvr.ObjectConstant("d2"),
                        svrsvr.ObjectConstant("d3"),
                    },
                ),
            }
        )

        docks = type_hierarchy.type_set(svrsvr.TypeName("Docks"))
        piles = type_hierarchy.type_set(svrsvr.TypeName("Piles"))

        rigid_rel_adjacent = svrsvr.RigidRelationSchema(
            svrsvr.RigidRelationName("adjacent"),
            (docks, docks),
        )

        rigid_rel_at = svrsvr.RigidRelationSchema(
            svrsvr.RigidRelationName("at"),
            (piles, docks),
        )

        rigid_relations = svrsvr.RigidRelations(
            {
                rigid_rel_adjacent: {
                    (svrsvr.ObjectConstant("d1"), svrsvr.ObjectConstant("d2")),
                    (svrsvr.ObjectConstant("d2"), svrsvr.ObjectConstant("d1")),
                    (svrsvr.ObjectConstant("d2"), svrsvr.ObjectConstant("d3")),
                    (svrsvr.ObjectConstant("d3"), svrsvr.ObjectConstant("d2")),
                    (svrsvr.ObjectConstant("d3"), svrsvr.ObjectConstant("d1")),
                    (svrsvr.ObjectConstant("d1"), svrsvr.ObjectConstant("d3")),
                },
                rigid_rel_at: {
                    (svrsvr.ObjectConstant("p1"), svrsvr.ObjectConstant("d1")),
                    (svrsvr.ObjectConstant("p2"), svrsvr.ObjectConstant("d2")),
                    (svrsvr.ObjectConstant("p3"), svrsvr.ObjectConstant("d2")),
                },
            }
        )

        nil = svrsvr.ObjectConstant("nil")
        true = svrsvr.ObjectConstant("T")
        false = svrsvr.ObjectConstant("F")

        containers = type_hierarchy.type_set(svrsvr.TypeName("Containers"))
        robots = type_hierarchy.type_set(svrsvr.TypeName("Robots"))
        docks = type_hierarchy.type_set(svrsvr.TypeName("Docks"))
        piles = type_hierarchy.type_set(svrsvr.TypeName("Piles"))

        containers_or_nil = containers | frozenset({nil})

        schema_r = svrsvr.ObjectVariable(svrsvr.ObjectVariableName("r"), robots)
        schema_d = svrsvr.ObjectVariable(svrsvr.ObjectVariableName("d"), docks)
        schema_c = svrsvr.ObjectVariable(svrsvr.ObjectVariableName("c"), containers)
        schema_p = svrsvr.ObjectVariable(svrsvr.ObjectVariableName("p"), piles)

        state_var_cargo = svrsvr.StateVariableSchema(
            svrsvr.StateVariableName("cargo"),
            (schema_r,),
            containers_or_nil,
        )

        state_var_loc = svrsvr.StateVariableSchema(
            svrsvr.StateVariableName("loc"),
            (schema_r,),
            docks,
        )

        state_var_occupied = svrsvr.StateVariableSchema(
            svrsvr.StateVariableName("occupied"),
            (schema_d,),
            frozenset({true, false}),
        )

        state_var_pile = svrsvr.StateVariableSchema(
            svrsvr.StateVariableName("pile"),
            (schema_c,),
            piles | frozenset({nil}),
        )

        state_var_pos = svrsvr.StateVariableSchema(
            svrsvr.StateVariableName("pos"),
            (schema_c,),
            robots | containers | frozenset({nil}),
        )

        state_var_top = svrsvr.StateVariableSchema(
            svrsvr.StateVariableName("top"),
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
    def objects(self) -> frozenset[svrsvr.ObjectConstant]:
        return self.type_hierarchy.type_set(svrsvr.TypeName("Objects"))

    @property
    def positions(self) -> frozenset[svrsvr.ObjectConstant]:
        return self.type_hierarchy.type_set(svrsvr.TypeName("Positions"))

    @property
    def containers(self) -> frozenset[svrsvr.ObjectConstant]:
        return self.type_hierarchy.type_set(svrsvr.TypeName("Containers"))

    @property
    def piles(self) -> frozenset[svrsvr.ObjectConstant]:
        return self.type_hierarchy.type_set(svrsvr.TypeName("Piles"))

    @property
    def symbols(self) -> frozenset[svrsvr.ObjectConstant]:
        return self.type_hierarchy.type_set(svrsvr.TypeName("Symbols"))

    @property
    def robots(self) -> frozenset[svrsvr.ObjectConstant]:
        return self.type_hierarchy.type_set(svrsvr.TypeName("Robots"))

    @property
    def docks(self) -> frozenset[svrsvr.ObjectConstant]:
        return self.type_hierarchy.type_set(svrsvr.TypeName("Docks"))
