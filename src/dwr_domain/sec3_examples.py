import state_transition_system.problem as sts_prob
import state_variable_representation.action as svr_act
import state_variable_representation.first_order_logic as svr_fol
import state_variable_representation.model as svr_model
import state_variable_representation.planning_domain as svr_domain
import forward_state_space_search.algorithm as fsss_algo
import state_variable_representation.applicable_action_builder as svr_aab


def build_problem_example_3_2() -> sts_prob.PlanningProblem[
    svr_model.StateVariableState,
    svr_domain.StateVariablePlanningDomain,
]:
    """Build the planning problem in Figure 3.2 / Example 3.2. (p43,44)"""

    # --- type names ---

    type_name_objects = svr_model.TypeName("Objects")
    type_name_robots = svr_model.TypeName("Robots")
    type_name_containers = svr_model.TypeName("Containers")
    type_name_docks = svr_model.TypeName("Docks")
    type_name_symbols = svr_model.TypeName("Symbols")

    # --- object constants ---

    nil = svr_model.ObjectConstant("nil")

    r1 = svr_model.ObjectConstant("r1")
    c1 = svr_model.ObjectConstant("c1")

    d1 = svr_model.ObjectConstant("d1")
    d2 = svr_model.ObjectConstant("d2")
    d3 = svr_model.ObjectConstant("d3")

    # --- type hierarchy ---

    type_hierarchy = svr_model.TypeHierarchy(
        {
            type_name_objects: (
                {
                    type_name_robots,
                    type_name_containers,
                    type_name_docks,
                    type_name_symbols,
                },
                set(),
            ),
            type_name_robots: (
                set(),
                {r1},
            ),
            type_name_containers: (
                set(),
                {c1},
            ),
            type_name_docks: (
                set(),
                {d1, d2, d3},
            ),
            type_name_symbols: (
                set(),
                {nil},
            ),
        }
    )

    robots = type_hierarchy.type_range(type_name_robots)
    containers = type_hierarchy.type_range(type_name_containers)
    docks = type_hierarchy.type_range(type_name_docks)

    # Example 3.2 では rigid relations は無い
    rigid_relations = svr_model.RigidRelations({})

    # --- object variables ---

    var_r = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("r"),
        robots,
    )
    var_c = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("c"),
        containers,
    )
    var_d = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("d"),
        docks,
    )
    var_e = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("e"),
        docks,
    )
    var_l = svr_model.ObjectVariable(
        svr_model.ObjectVariableName("l"),
        docks,  # | frozenset({r1}),
    )

    # --- state variable schemas ---

    # 教科書には loc(r1) と loc(c1) の両方が書かれている
    # 値の範囲が異なるため，同じ StateVariableName("loc") を持つが引数の範囲が異なる 2 つのスキーマとして表す

    state_var_cargo = svr_model.StateVariableSchema(
        svr_model.StateVariableName("cargo"),
        (var_r,),
        containers | frozenset({nil}),
    )

    state_var_robot_loc = svr_model.StateVariableSchema(
        svr_model.StateVariableName("loc"),
        (var_r,),
        docks,
    )

    state_var_container_loc = svr_model.StateVariableSchema(
        svr_model.StateVariableName("loc"),
        (var_c,),
        docks | robots,
    )

    state_variable_schemas = (
        state_var_cargo,
        state_var_robot_loc,
        state_var_container_loc,
    )

    # --- helper constructors ---

    def assign(
        schema: svr_model.StateVariableSchema,
        args: tuple[svr_model.ObjectTerm, ...],
        value: svr_model.ObjectTerm,
    ) -> svr_model.StateVariableAssignment:
        return svr_model.StateVariableAssignment(
            state_variable=svr_model.StateVariableExpr(schema, args),
            value=value,
        )

    def state_literal(
        assignment: svr_model.StateVariableAssignment,
        negated: bool = False,
    ) -> svr_fol.StateVariableLiteralExpr:
        return svr_fol.StateVariableLiteralExpr(assignment, negated)

    # --- action schemas ---

    # take(r, c, l)
    action_schema_take = svr_act.ActionSchema(
        head=svr_act.Head(
            name="take",
            parameters=(var_r, var_c, var_l),
        ),
        preconditions=svr_act.Preconditions(
            literals=(
                state_literal(assign(state_var_cargo, (var_r,), nil)),
                state_literal(assign(state_var_container_loc, (var_c,), var_l)),
                state_literal(assign(state_var_robot_loc, (var_r,), var_l)),
            )
        ),
        effects=svr_act.Effects(
            effects=(
                assign(state_var_cargo, (var_r,), var_c),
                assign(state_var_container_loc, (var_c,), var_r),
            )
        ),
    )

    # put(r, c, l)
    action_schema_put = svr_act.ActionSchema(
        head=svr_act.Head(
            name="put",
            parameters=(var_r, var_c, var_l),
        ),
        preconditions=svr_act.Preconditions(
            literals=(
                state_literal(assign(state_var_cargo, (var_r,), var_c)),
                state_literal(assign(state_var_robot_loc, (var_r,), var_l)),
            )
        ),
        effects=svr_act.Effects(
            effects=(
                assign(state_var_cargo, (var_r,), nil),
                assign(state_var_container_loc, (var_c,), var_l),
            )
        ),
    )

    # move(r, d, e)
    action_schema_move = svr_act.ActionSchema(
        head=svr_act.Head(
            name="move",
            parameters=(var_r, var_d, var_e),
        ),
        preconditions=svr_act.Preconditions(
            literals=(state_literal(assign(state_var_robot_loc, (var_r,), var_d)),)
        ),
        effects=svr_act.Effects(
            effects=(assign(state_var_robot_loc, (var_r,), var_e),)
        ),
    )

    action_schemas = (
        action_schema_take,
        action_schema_put,
        action_schema_move,
    )

    # --- domain作成 ---

    domain = svr_domain.StateVariablePlanningDomain(
        type_hierarchy=type_hierarchy,
        rigid_relations=rigid_relations,
        state_variable_schemas=state_variable_schemas,
        action_schemas=action_schemas,
    )

    # --- initial state ---

    initial_state = svr_model.StateVariableState(
        (
            assign(state_var_robot_loc, (r1,), d3),
            assign(state_var_cargo, (r1,), nil),
            assign(state_var_container_loc, (c1,), d1),
        )
    )

    # --- goal formula ---

    goal_formula = svr_domain.GoalFormula(
        literals=(
            state_literal(assign(state_var_robot_loc, (r1,), d3)),
            state_literal(assign(state_var_container_loc, (c1,), r1)),
        )
    )

    return sts_prob.PlanningProblem(
        domain=domain,
        initial_state=initial_state,
        goal_formula=goal_formula,
    )


if __name__ == "__main__":
    problem = build_problem_example_3_2()

    print("DOMEIN:")
    print("Type hierarchy:")
    print(problem.domain.type_hierarchy)
    print("\nRigid relations:")
    print(problem.domain.rigid_relations)
    print("\nState variables:")
    for sv in problem.domain.state_variable_schemas:
        print(sv)
    print("\nActions:")
    for a in problem.domain.action_schemas:
        print(a)
    print("\nInitial state:")
    print(problem.initial_state)
    print("\nGoal formula:")
    print(problem.goal_formula)

    print()

    print("Forward search:")

    applicable_action_builder = svr_aab.ApplicableActionBuilder()

    print("BFS: ", fsss_algo.breadth_first_search(problem, applicable_action_builder))
    print()
    print("DFS: ", fsss_algo.depth_first_search(problem, applicable_action_builder))  # 終わらない
