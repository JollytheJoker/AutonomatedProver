import copy
from typing import List, Tuple, Set, Union, Generator

from Knuth_Bendix_Algorithm import reducde_statement_modulo_directed_axioms, \
    reducde_statement_modulo_directed_axioms_return_replacement_list
from Statement import Statement, Relation, LogicalOperation, Bool, canonicalize_ac, kbo_compare, MetaObject, \
    OPERATION_PROPERTIES, generate_ac_invariants
from collections import deque
from CommonStatements import DEFINITIONS, logical_axioms


class Prove:
    def __init__(self, initial_state: Union[Statement, None] = None):
        self.current_statement: Union[Statement, None] = initial_state
        self.transformations: List[Statement] = []
        self.state_log: List[Statement] = [initial_state]

    def push(self, new_state: Statement, transformation: Statement):
        """ Pushes the next state and transformation information into object """
        self.current_statement = new_state
        self.state_log.append(new_state)
        self.transformations.append(transformation)

    def __hash__(self):
        """ Since a proves history isn't important for the prover, we only have to hash the current state """
        return hash(self.current_statement)

    def __repr__(self):
        prove_str = f'Initial State: {self.state_log[0]}'
        for updated_state, transformation in zip(self.state_log[1:], self.transformations):
            prove_str += f'\n{updated_state} (Using: {transformation})'
        return prove_str


class Prover:
    def __init__(self, statements: Tuple[Statement, ...] = (), initial_state: Statement = None):
        self.statements: Tuple[Statement, ...] = statements
        self.goal_statement: Statement | None = initial_state

    def prove(self, print_trace: bool = False) -> Tuple[Union[Prove, None], ...]:
        """ Runs search algorithm on state space to find prove for the goal statement """
        # Create sub-proof tasks on logical operations
        def find_substatements(sub_statement: Statement) -> List[Statement]:
            # TODO: What if an object is dependent over logical operator (exists x in R: x = 0 and x = 1 is false, but exsits x = 0 in R and exists x = 1 in R is true)
            if isinstance(sub_statement.node_function, LogicalOperation) and not (sub_statement.node_function == LogicalOperation.IMPLIES or sub_statement.node_function == LogicalOperation.IMPLIEDBY):
                return find_substatements(sub_statement.child_left) + find_substatements(sub_statement.child_right)

            return [sub_statement]

        if isinstance(self.goal_statement.node_function, LogicalOperation) and not (self.goal_statement.node_function == LogicalOperation.IMPLIES or self.goal_statement.node_function == LogicalOperation.IMPLIEDBY):
            sub_statements = find_substatements(self.goal_statement)

            proves = []
            for sub in sub_statements:
                sub_statement_prover = Prover(self.statements, sub)

                if not sub_statement_prover.prove():
                    return ()
                proves.append(sub_statement_prover)

            return tuple(proves)

        # Self has non-logical operation as node_function (or implies)
        # TODO: Implement Defintion unfolding
        queue = deque([Prove(self.goal_statement)])
        visited: Set[Prove] = {Prove(self.goal_statement)}
        depth = 1

        while queue:
            state = queue.popleft()
            if print_trace: print("-" * 15 + f" {state.current_statement} " + "-" * 15)

            # If the state is true, then we have finished the proof
            if state.current_statement == Statement(Bool.TRUE):
                return (state, )

            for statement in list(set(self.statements) - set(state.transformations)):
                if print_trace: print("-" * 5 + f" {statement} " + "-" * 5)
                # Update statespace
                # Option 1: simplify state with statement
                for new_statement in state.current_statement.simplify(statement, Statement(Bool.TRUE)):
                    new_statement = canonicalize_ac(new_statement)
                    new_statement = reducde_statement_modulo_directed_axioms(new_statement, logical_axioms)

                    new_state = copy.deepcopy(state)
                    new_state.push(new_statement, statement)

                    if new_state not in visited:
                        if print_trace: print(f"Add {new_statement}")
                        queue.append(new_state)
                        visited.add(new_state)

                # Option 2: simplify statement with state
                for new_statement in statement.simplify(state.current_statement, Statement(Bool.AMBIGUOUS)):
                    new_statement = canonicalize_ac(new_statement)
                    new_statement = reducde_statement_modulo_directed_axioms(new_statement, logical_axioms)

                    new_state = copy.deepcopy(state)
                    new_state.push(new_statement, statement)

                    if new_state not in visited:
                        if print_trace: print(f"Add {new_statement}")
                        queue.append(new_state)
                        visited.add(new_state)

        return (None, )


def update_relation(input_statement: Statement, to_relation: Relation) -> Statement:
    """ Tries to update statements relation to given relation according to relation hierarchy """
    # TODO
    return input_statement


def find_implicit_simplifications_from_axioms_definitions(definition_obj: Statement, definition_expr: Statement, axiom_obj: Statement, axiom_simplification: Statement) -> Generator[Union[Statement, None]]:
    """
    Uses the given axiom to replace things in given definition to find implicit simplification on definition.
    E.g. P | F = P is not axiomatically defined but can be found by this function.
    definition_obj : the object that go defined (e.g. P | Q)
    definition_expr : the objects definition (e.g. (P xor Q) xor (P and Q))
    axiom_obj : the axiom object that can be written differently (e.g. P xor F)
    axiom_simplification : the following simplification for the axiom_obj (e.g. P)
    """
    # Here we also use the not-canonical version of the axiom for replacements
    for invariant in generate_ac_invariants(axiom_obj):
        # Try to use Axiom to simplify definition_expr
        for axiom_replaced_version, replacement_list_tmp in definition_expr.simplify_return_replacement_list(invariant, axiom_simplification, allow_bool_val_replacement=True):
            # We don't want to identify the entire axiom with just one metaobject, this would be redundant
            if any(isinstance(s.node_function, MetaObject) and t == invariant for s, t in replacement_list_tmp):
                continue

            # Replace definition obj accordingly
            original_replaced = definition_obj.replace_with_list(replacement_list_tmp)

            # Simplify over other axioms (here we can't replace metaobjects with boolean values)
            final_version, replacement_list = reducde_statement_modulo_directed_axioms_return_replacement_list(axiom_replaced_version, logical_axioms)

            # Apply replacement to other for as long as it changes
            original_replaced = original_replaced.strong_replace_with_list(replacement_list)

            # Repeat reduction phase on original
            original_replaced, replacement_list = reducde_statement_modulo_directed_axioms_return_replacement_list(original_replaced, logical_axioms)
            final_version = final_version.strong_replace_with_list(replacement_list)

            # Canonicalize
            original_replaced = original_replaced.canonical
            final_version = final_version.canonical

            # Check kbo weights
            if kbo_compare(original_replaced, final_version) > 0:
                yield original_replaced, final_version
