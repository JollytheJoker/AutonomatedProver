import copy
from typing import List, Tuple, Set, Union

from Knuth_Bendix_Algorithm import reducde_statement_modulo_directed_axioms
from Statement import Statement, Relation, LogicalOperation, Bool, canonicalize_ac
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
            if print_trace: print("-" * 15 + f" DEPTH = {depth} " + "-" * 15)

            state = queue.popleft()

            # If the state is true, then we have finished the proof
            if state.current_statement == Statement(Bool.TRUE):
                return (state, )

            for statement in list(set(self.statements) - set(state.transformations)):
                '''if statement.node_function != self.goal_statement.node_function:
                    # TODO: What if statement only has packed non-logical junction-function
                    continue'''

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
