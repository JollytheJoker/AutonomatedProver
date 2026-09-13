import copy
from typing import List, Tuple
from Statement import Statement, Relation, LogicalOperation
from collections import deque
from CommonStatements import DEFINITIONS


class Prove:
    def __init__(self, initial_state: Statement):
        self.current_state: Statement = initial_state
        self.transformations: List[Statement] = []
        self.state_log: List[Statement] = [initial_state]

    def push(self, new_state: Statement, transformation: Statement):
        """ Pushes the next state and transformation information into object """
        self.current_state = new_state
        self.state_log.append(new_state)
        self.transformations.append(transformation)

    def __hash__(self):
        """ Since a proves history isn't important for the prover, we only have to hash the current state """
        return hash(self.current_state)

    def __repr__(self):
        return f"{str(self.current_state)}\n Transformations: \n {"; \n".join(str(transformation) + ("^-1" if is_inverse else "") for transformation, is_inverse in self.transformations)}, \n State log: {"; \n".join(str(state) for state in self.state_log)}"


class Prover:
    def __init__(self, statements: Tuple[Statement] = (), initial_state: Statement = None):
        self.statements: Tuple[Statement] = statements
        self.goal_statement: Statement | None = initial_state

    def prove(self, print_trace: bool = False) -> Tuple[Prove, ...]:
        """ Runs search algorithm on state space to find prove for the goal statement """
        # Create sub-proof tasks on logical operations
        def find_substatements(sub_statement: Statement) -> List[Statement]:
            if isinstance(sub_statement.node_function, LogicalOperation):
                return find_substatements(sub_statement.child_left) + find_substatements(sub_statement.child_right)

            return [sub_statement]

        if isinstance(self.goal_statement.node_function, LogicalOperation):
            sub_statements = find_substatements(self.goal_statement)

            proves = []
            for sub in sub_statements:
                sub_statement_prover = Prover(self.statements, sub)

                if not sub_statement_prover.prove():
                    return ()
                proves.append(sub_statement_prover)

            return tuple(proves)

        # Self has non-logical operation as node_function
        # TODO: Implement Defintion unfolding
        return (self.prove_static(print_trace),)

    def prove_static(self, print_trace: bool = False) -> Prove | None:
        """ This function runs BFS on a static state-space, where definitons are not used to change statements """
        # BFS (direct and inverse application)
        # TODO: Is only valid for transivit non-logical operations (e.g. =>, <=>, subset of etc.)
        junction_operation = self.goal_statement.node_function

        start = self.goal_statement.child_left
        finish = self.goal_statement.child_right
        queue_start_to_fin = deque([Prove(start)])
        queue_fin_to_start = deque([Prove(finish)])
        visited_start_to_fin = {Prove(start)}
        visited_fin_to_start = {Prove(finish)}
        depth = 1

        # Statespace update function (application of any statement)
        def update_state_space(application_statement: Statement, state: Prove, queue: deque, visited: set):
            if not state:
                return

            for new_statement in application_statement(state.current_state):
                new_state = copy.deepcopy(state)
                new_state.push(new_statement, application_statement)

                if new_state not in visited:
                    if print_trace: print(f"Add {new_statement}")
                    visited.add(new_state)
                    queue.append(new_state)

        # Statespace search (BFS)
        while queue_start_to_fin or queue_fin_to_start:
            if print_trace: print("-" * 15 + f" DEPTH = {depth} " + "-" * 15)

            try:
                state_start_to_fin = queue_start_to_fin.popleft()
            except IndexError:
                state_start_to_fin = None

            try:
                state_fin_to_start = queue_fin_to_start.popleft()
            except IndexError:
                state_fin_to_start = None

            # Note: No errors cos' python's lazy bool evaluation
            if state_start_to_fin and state_start_to_fin.current_state == finish:
                return state_start_to_fin

            if state_fin_to_start and state_fin_to_start.current_state == start:
                return state_fin_to_start

            # Get new current states
            for statement in self.statements:
                if statement.node_function != junction_operation:
                    # TODO: What if statement only has packed non-logical junction-function
                    continue

                # Forward
                update_state_space(statement, state_start_to_fin, queue_start_to_fin, visited_start_to_fin)

                # Backward
                update_state_space(statement, state_fin_to_start, queue_fin_to_start, visited_fin_to_start)

            depth += 1
        return None


def update_relation(input_statement: Statement, to_relation: Relation) -> Statement:
    """ Tries to update statements relation to given relation according to relation hierarchy """
    # TODO
    return input_statement
