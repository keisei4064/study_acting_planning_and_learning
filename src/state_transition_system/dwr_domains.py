import state_transition_system.state_variable_repr as stssvr
import dataclasses
from typing import Self


@dataclasses.dataclass(frozen=True)
class DWRDomain:
    type_hierarchy: stssvr.TypeHierarchy
    rigid_rel_adjacent: stssvr.RigidRelationSchema
    rigid_rel_at: stssvr.RigidRelationSchema
    rigid_relations: stssvr.RigidRelations

    state_var_cargo: stssvr.StateVariableSchema
    state_var_loc: stssvr.StateVariableSchema
    state_var_occupied: stssvr.StateVariableSchema
    state_var_pile: stssvr.StateVariableSchema
    state_var_pos: stssvr.StateVariableSchema
    state_var_top: stssvr.StateVariableSchema

    @classmethod
    def build(cls) -> Self:
        type_hierarchy = stssvr.TypeHierarchy(
            {
                stssvr.TypeName("Objects"): (
                    {
                        stssvr.TypeName("Positions"),
                        stssvr.TypeName("Containers"),
                        stssvr.TypeName("Piles"),
                        stssvr.TypeName("Symbols"),
                    },
                    set(),
                ),
                stssvr.TypeName("Positions"): (
                    {
                        stssvr.TypeName("Robots"),
                        stssvr.TypeName("Docks"),
                    },
                    {
                        stssvr.ObjectConstant("nil"),
                    },
                ),
                stssvr.TypeName("Symbols"): (
                    set(),
                    {
                        stssvr.ObjectConstant("T"),
                        stssvr.ObjectConstant("F"),
                        stssvr.ObjectConstant("nil"),
                    },
                ),
                stssvr.TypeName("Containers"): (
                    set(),
                    {
                        stssvr.ObjectConstant("c1"),
                        stssvr.ObjectConstant("c2"),
                        stssvr.ObjectConstant("c3"),
                    },
                ),
                stssvr.TypeName("Piles"): (
                    set(),
                    {
                        stssvr.ObjectConstant("p1"),
                        stssvr.ObjectConstant("p2"),
                        stssvr.ObjectConstant("p3"),
                    },
                ),
                stssvr.TypeName("Robots"): (
                    set(),
                    {
                        stssvr.ObjectConstant("r1"),
                        stssvr.ObjectConstant("r2"),
                    },
                ),
                stssvr.TypeName("Docks"): (
                    set(),
                    {
                        stssvr.ObjectConstant("d1"),
                        stssvr.ObjectConstant("d2"),
                        stssvr.ObjectConstant("d3"),
                    },
                ),
            }
        )

        docks = type_hierarchy.type_set(stssvr.TypeName("Docks"))
        piles = type_hierarchy.type_set(stssvr.TypeName("Piles"))

        rigid_rel_adjacent = stssvr.RigidRelationSchema(
            stssvr.RigidRelationName("adjacent"),
            (docks, docks),
        )

        rigid_rel_at = stssvr.RigidRelationSchema(
            stssvr.RigidRelationName("at"),
            (piles, docks),
        )

        rigid_relations = stssvr.RigidRelations(
            {
                rigid_rel_adjacent: {
                    (stssvr.ObjectConstant("d1"), stssvr.ObjectConstant("d2")),
                    (stssvr.ObjectConstant("d2"), stssvr.ObjectConstant("d1")),
                    (stssvr.ObjectConstant("d2"), stssvr.ObjectConstant("d3")),
                    (stssvr.ObjectConstant("d3"), stssvr.ObjectConstant("d2")),
                    (stssvr.ObjectConstant("d3"), stssvr.ObjectConstant("d1")),
                    (stssvr.ObjectConstant("d1"), stssvr.ObjectConstant("d3")),
                },
                rigid_rel_at: {
                    (stssvr.ObjectConstant("p1"), stssvr.ObjectConstant("d1")),
                    (stssvr.ObjectConstant("p2"), stssvr.ObjectConstant("d2")),
                    (stssvr.ObjectConstant("p3"), stssvr.ObjectConstant("d2")),
                },
            }
        )

        nil = stssvr.ObjectConstant("nil")
        true = stssvr.ObjectConstant("T")
        false = stssvr.ObjectConstant("F")

        containers = type_hierarchy.type_set(stssvr.TypeName("Containers"))
        robots = type_hierarchy.type_set(stssvr.TypeName("Robots"))
        docks = type_hierarchy.type_set(stssvr.TypeName("Docks"))
        piles = type_hierarchy.type_set(stssvr.TypeName("Piles"))

        containers_or_nil = containers | frozenset({nil})

        schema_r = stssvr.ObjectVariable(stssvr.ObjectVariableName("r"), robots)
        schema_d = stssvr.ObjectVariable(stssvr.ObjectVariableName("d"), docks)
        schema_c = stssvr.ObjectVariable(stssvr.ObjectVariableName("c"), containers)
        schema_p = stssvr.ObjectVariable(stssvr.ObjectVariableName("p"), piles)

        state_var_cargo = stssvr.StateVariableSchema(
            stssvr.StateVariableName("cargo"),
            (schema_r,),
            containers_or_nil,
        )

        state_var_loc = stssvr.StateVariableSchema(
            stssvr.StateVariableName("loc"),
            (schema_r,),
            docks,
        )

        state_var_occupied = stssvr.StateVariableSchema(
            stssvr.StateVariableName("occupied"),
            (schema_d,),
            frozenset({true, false}),
        )

        state_var_pile = stssvr.StateVariableSchema(
            stssvr.StateVariableName("pile"),
            (schema_c,),
            piles | frozenset({nil}),
        )

        state_var_pos = stssvr.StateVariableSchema(
            stssvr.StateVariableName("pos"),
            (schema_c,),
            robots | containers | frozenset({nil}),
        )

        state_var_top = stssvr.StateVariableSchema(
            stssvr.StateVariableName("top"),
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
    def objects(self) -> frozenset[stssvr.ObjectConstant]:
        return self.type_hierarchy.type_set(stssvr.TypeName("Objects"))

    @property
    def positions(self) -> frozenset[stssvr.ObjectConstant]:
        return self.type_hierarchy.type_set(stssvr.TypeName("Positions"))

    @property
    def containers(self) -> frozenset[stssvr.ObjectConstant]:
        return self.type_hierarchy.type_set(stssvr.TypeName("Containers"))

    @property
    def piles(self) -> frozenset[stssvr.ObjectConstant]:
        return self.type_hierarchy.type_set(stssvr.TypeName("Piles"))

    @property
    def symbols(self) -> frozenset[stssvr.ObjectConstant]:
        return self.type_hierarchy.type_set(stssvr.TypeName("Symbols"))

    @property
    def robots(self) -> frozenset[stssvr.ObjectConstant]:
        return self.type_hierarchy.type_set(stssvr.TypeName("Robots"))

    @property
    def docks(self) -> frozenset[stssvr.ObjectConstant]:
        return self.type_hierarchy.type_set(stssvr.TypeName("Docks"))
