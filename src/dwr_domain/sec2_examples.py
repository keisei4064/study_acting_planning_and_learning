import state_variable_representation.model as svr_model
import dwr_domain.model
import state_variable_representation.action as svr_act
import state_variable_representation.first_order_logic as svr_fol


def build_domain_figure_2_3() -> tuple[
    dwr_domain.model.DWRPlanningDomain, dwr_domain.model.DWRState
]:
    """p.14"""

    # objects and type hierarchy ---

    # type names
    type_name_objects = svr_model.TypeName("Objects")
    type_name_positions = svr_model.TypeName("Positions")
    type_name_containers = svr_model.TypeName("Containers")
    type_name_piles = svr_model.TypeName("Piles")
    type_name_symbols = svr_model.TypeName("Symbols")
    type_name_robots = svr_model.TypeName("Robots")
    type_name_docks = svr_model.TypeName("Docks")

    # object constants
    obj_const_nil = svr_model.ObjectConstant("nil")
    obj_const_true = svr_model.ObjectConstant("T")
    obj_const_false = svr_model.ObjectConstant("F")
    obj_const_c1 = svr_model.ObjectConstant("c1")
    obj_const_c2 = svr_model.ObjectConstant("c2")
    obj_const_c3 = svr_model.ObjectConstant("c3")
    obj_const_p1 = svr_model.ObjectConstant("p1")
    obj_const_p2 = svr_model.ObjectConstant("p2")
    obj_const_p3 = svr_model.ObjectConstant("p3")
    obj_const_r1 = svr_model.ObjectConstant("r1")
    obj_const_r2 = svr_model.ObjectConstant("r2")
    obj_const_d1 = svr_model.ObjectConstant("d1")
    obj_const_d2 = svr_model.ObjectConstant("d2")
    obj_const_d3 = svr_model.ObjectConstant("d3")

    # type hierarchy を構築
    type_hierarchy = svr_model.TypeHierarchy(
        {
            type_name_objects: (
                {
                    type_name_positions,
                    type_name_symbols,
                    type_name_containers,
                    type_name_piles,
                },
                set(),
            ),
            type_name_positions: (
                {
                    type_name_robots,
                    type_name_docks,
                },
                {
                    obj_const_nil,
                },
            ),
            type_name_symbols: (
                set(),
                {
                    obj_const_true,
                    obj_const_false,
                    obj_const_nil,
                },
            ),
            type_name_containers: (
                set(),
                {
                    obj_const_c1,
                    obj_const_c2,
                    obj_const_c3,
                },
            ),
            type_name_piles: (
                set(),
                {
                    obj_const_p1,
                    obj_const_p2,
                    obj_const_p3,
                },
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

    # rigid relations ---

    rigid_rel_adjacent = svr_model.RigidRelationSchema(
        svr_model.RigidRelationName("adjacent"),
        (
            type_hierarchy.type_range(type_name_docks),
            type_hierarchy.type_range(type_name_docks),
        ),
    )
    rigid_rel_at = svr_model.RigidRelationSchema(
        svr_model.RigidRelationName("at"),
        (
            type_hierarchy.type_range(type_name_piles),
            type_hierarchy.type_range(type_name_docks),
        ),
    )

    rigid_relations = svr_model.RigidRelations(
        {
            rigid_rel_adjacent: {
                (obj_const_d1, obj_const_d2),
                (obj_const_d2, obj_const_d1),
                (obj_const_d2, obj_const_d3),
                (obj_const_d3, obj_const_d2),
                (obj_const_d3, obj_const_d1),
                (obj_const_d1, obj_const_d3),
            },
            rigid_rel_at: {
                (obj_const_p1, obj_const_d1),
                (obj_const_p2, obj_const_d2),
                (obj_const_p3, obj_const_d2),
            },
        }
    )

    # object variables ---

    obj_var_r = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("r"),
        type_hierarchy.type_range(type_name_robots),
    )
    obj_var_d = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("d"),
        type_hierarchy.type_range(type_name_docks),
    )
    obj_var_c = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("c"),
        type_hierarchy.type_range(type_name_containers),
    )
    obj_var_p = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("p"),
        type_hierarchy.type_range(type_name_piles),
    )

    # state variables ---

    state_var_schema_cargo = svr_model.StateVariableSchema(
        svr_model.StateVariableName("cargo"),
        (obj_var_r,),
        type_hierarchy.type_range(type_name_containers) | frozenset({obj_const_nil}),
    )
    state_var_schema_loc = svr_model.StateVariableSchema(
        svr_model.StateVariableName("loc"),
        (obj_var_r,),
        type_hierarchy.type_range(type_name_docks),
    )
    state_var_schema_occupied = svr_model.StateVariableSchema(
        svr_model.StateVariableName("occupied"),
        (obj_var_d,),
        frozenset({obj_const_true, obj_const_false}),
    )
    state_var_schema_pile = svr_model.StateVariableSchema(
        svr_model.StateVariableName("pile"),
        (obj_var_c,),
        type_hierarchy.type_range(type_name_piles) | frozenset({obj_const_nil}),
    )
    state_var_schema_pos = svr_model.StateVariableSchema(
        svr_model.StateVariableName("pos"),
        (obj_var_c,),
        type_hierarchy.type_range(type_name_robots)
        | type_hierarchy.type_range(type_name_containers)
        | frozenset({obj_const_nil}),
    )
    state_var_schema_top = svr_model.StateVariableSchema(
        svr_model.StateVariableName("top"),
        (obj_var_p,),
        type_hierarchy.type_range(type_name_containers) | frozenset({obj_const_nil}),
    )

    state_variable_schemas = (
        state_var_schema_cargo,
        state_var_schema_loc,
        state_var_schema_occupied,
        state_var_schema_pile,
        state_var_schema_pos,
        state_var_schema_top,
    )

    # s0 (initial state) ---
    s0 = dwr_domain.model.DWRState(
        [
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_cargo, (obj_const_r1,)),
                obj_const_nil,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_cargo, (obj_const_r2,)),
                obj_const_nil,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_loc, (obj_const_r1,)),
                obj_const_d1,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_loc, (obj_const_r2,)),
                obj_const_d2,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_occupied, (obj_const_d1,)),
                obj_const_true,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_occupied, (obj_const_d2,)),
                obj_const_true,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_occupied, (obj_const_d3,)),
                obj_const_false,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_pile, (obj_const_c1,)),
                obj_const_p1,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_pile, (obj_const_c2,)),
                obj_const_p1,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_pile, (obj_const_c3,)),
                obj_const_p2,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_pos, (obj_const_c1,)),
                obj_const_c2,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_pos, (obj_const_c2,)),
                obj_const_nil,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_pos, (obj_const_c3,)),
                obj_const_nil,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_top, (obj_const_p1,)),
                obj_const_c1,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_top, (obj_const_p2,)),
                obj_const_c3,
            ),
            svr_model.StateVariableAssignment(
                svr_model.StateVariableExpr(state_var_schema_top, (obj_const_p3,)),
                obj_const_nil,
            ),
        ],
    )

    # Action schemas ---

    # additional object variables

    obj_var_c_prime = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("c'"),
        type_hierarchy.type_range(type_name_containers) | frozenset({obj_const_nil}),
    )
    obj_var_d_prime = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("d'"),
        type_hierarchy.type_range(type_name_docks),
    )

    # take(r, c, c', p, d)
    action_schema_take = svr_act.ActionSchema(
        head=svr_act.Head(
            name="take",
            parameters=(obj_var_r, obj_var_c, obj_var_c_prime, obj_var_p, obj_var_d),
        ),
        preconditions=svr_act.Preconditions(
            literals=(
                svr_fol.RigidRelationLiteralExpr(
                    svr_fol.RigidRelationAssertion(rigid_rel_at, (obj_var_p, obj_var_d))
                ),
                svr_fol.StateVariableLiteralExpr(
                    svr_model.StateVariableAssignment(
                        svr_model.StateVariableExpr(
                            state_var_schema_cargo, (obj_var_r,)
                        ),
                        obj_const_nil,
                    )
                ),
                svr_fol.StateVariableLiteralExpr(
                    svr_model.StateVariableAssignment(
                        svr_model.StateVariableExpr(state_var_schema_loc, (obj_var_r,)),
                        obj_var_d,
                    )
                ),
                svr_fol.StateVariableLiteralExpr(
                    svr_model.StateVariableAssignment(
                        svr_model.StateVariableExpr(state_var_schema_pos, (obj_var_c,)),
                        obj_var_c_prime,
                    )
                ),
                svr_fol.StateVariableLiteralExpr(
                    svr_model.StateVariableAssignment(
                        svr_model.StateVariableExpr(state_var_schema_top, (obj_var_p,)),
                        obj_var_c,
                    )
                ),
            )
        ),
        effects=svr_act.Effects(
            effects=(
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(state_var_schema_cargo, (obj_var_r,)),
                    obj_var_c,
                ),
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(state_var_schema_pile, (obj_var_c,)),
                    obj_const_nil,
                ),
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(state_var_schema_pos, (obj_var_c,)),
                    obj_var_r,
                ),
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(state_var_schema_top, (obj_var_p,)),
                    obj_var_c_prime,
                ),
            )
        ),
    )

    # put(r, c, c', p, d)
    action_schema_put = svr_act.ActionSchema(
        head=svr_act.Head(
            name="put",
            parameters=(obj_var_r, obj_var_c, obj_var_c_prime, obj_var_p, obj_var_d),
        ),
        preconditions=svr_act.Preconditions(
            literals=(
                svr_fol.RigidRelationLiteralExpr(
                    svr_fol.RigidRelationAssertion(rigid_rel_at, (obj_var_p, obj_var_d))
                ),
                svr_fol.StateVariableLiteralExpr(
                    svr_model.StateVariableAssignment(
                        svr_model.StateVariableExpr(state_var_schema_pos, (obj_var_c,)),
                        obj_var_r,
                    )
                ),
                svr_fol.StateVariableLiteralExpr(
                    svr_model.StateVariableAssignment(
                        svr_model.StateVariableExpr(state_var_schema_loc, (obj_var_r,)),
                        obj_var_d,
                    )
                ),
                svr_fol.StateVariableLiteralExpr(
                    svr_model.StateVariableAssignment(
                        svr_model.StateVariableExpr(state_var_schema_top, (obj_var_p,)),
                        obj_var_c_prime,
                    )
                ),
            )
        ),
        effects=svr_act.Effects(
            effects=(
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(state_var_schema_cargo, (obj_var_r,)),
                    obj_const_nil,
                ),
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(state_var_schema_pile, (obj_var_c,)),
                    obj_var_p,
                ),
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(state_var_schema_pos, (obj_var_c,)),
                    obj_var_c_prime,
                ),
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(state_var_schema_top, (obj_var_p,)),
                    obj_var_c,
                ),
            )
        ),
    )

    # move(r, d, d')
    action_schema_move = svr_act.ActionSchema(
        head=svr_act.Head(
            name="move",
            parameters=(obj_var_r, obj_var_d, obj_var_d_prime),
        ),
        preconditions=svr_act.Preconditions(
            literals=(
                svr_fol.RigidRelationLiteralExpr(
                    svr_fol.RigidRelationAssertion(
                        rigid_rel_adjacent, (obj_var_d, obj_var_d_prime)
                    )
                ),
                svr_fol.StateVariableLiteralExpr(
                    svr_model.StateVariableAssignment(
                        svr_model.StateVariableExpr(state_var_schema_loc, (obj_var_r,)),
                        obj_var_d,
                    )
                ),
                svr_fol.StateVariableLiteralExpr(
                    svr_model.StateVariableAssignment(
                        svr_model.StateVariableExpr(
                            state_var_schema_occupied, (obj_var_d_prime,)
                        ),
                        obj_const_false,
                    )
                ),
            )
        ),
        effects=svr_act.Effects(
            effects=(
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(state_var_schema_loc, (obj_var_r,)),
                    obj_var_d_prime,
                ),
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(
                        state_var_schema_occupied, (obj_var_d,)
                    ),
                    obj_const_false,
                ),
                svr_model.StateVariableAssignment(
                    svr_model.StateVariableExpr(
                        state_var_schema_occupied, (obj_var_d_prime,)
                    ),
                    obj_const_true,
                ),
            )
        ),
    )

    action_schemas = (action_schema_take, action_schema_put, action_schema_move)

    # ---

    return dwr_domain.model.DWRPlanningDomain(
        type_hierarchy, rigid_relations, state_variable_schemas, action_schemas
    ), s0


def execute_example_2_9_transition(
    figure_2_3_domain: dwr_domain.model.DWRPlanningDomain,
) -> None:
    """p.21"""

    r1 = svr_model.ObjectConstant("r1")

    d1 = svr_model.ObjectConstant("d1")

    c1 = svr_model.ObjectConstant("c1")
    c2 = svr_model.ObjectConstant("c2")

    p1 = svr_model.ObjectConstant("p1")

    take = figure_2_3_domain.action_schemas[0]
    a1_expr = svr_act.ActionExpr(
        schema=take,
        args=(r1, c1, c2, p1, d1),
    )
    a1 = svr_act.GroundAction.try_build(a1_expr, figure_2_3_domain.rigid_relations)
    print("a1: ", a1)

    assert a1 is not None
    assert a1.is_applicable(s0)

    # Action による状態遷移
    s1 = a1.transition(s0)

    assert s1 is not None

    print()
    print("a1 is applicable to s0:", a1.is_applicable(s0))
    print("Changed state variables:")
    for s0_state_variable_key, s0_state_variable_value in s0.items():
        s1_state_variable_value = s1.get_value(s0_state_variable_key)

        if s0_state_variable_value != s1_state_variable_value:
            print(
                f"  {s0_state_variable_key}: {s0_state_variable_value} → {s1_state_variable_value}"
            )


if __name__ == "__main__":
    print("Figure 2.3 domain ===\n")

    domain, s0 = build_domain_figure_2_3()
    # print(domain)
    print("Type hierarchy:")
    print(domain.type_hierarchy)

    print()

    print("Rigid relations:")
    print(domain.rigid_relations)

    print()

    print("State variables:")
    for sv in domain.state_variable_schemas:
        print(f"  {sv}")

    print()

    print("Actions:")
    for action_schema in domain.action_schemas:
        print(action_schema)

    print()

    print("Initial state:")
    print(s0)

    # ----
    print("Example 2.9 transition ===\n")
    execute_example_2_9_transition(domain)
