import copy
from typing import List, Tuple
from Statement import Statement, Relation
from ExpressionTree import Node
from collections import deque


class Prove:
    def __init__(self, initial_state: Node):
        self.current_state: Node = initial_state
        self.transformations: List[Tuple[Statement, bool]] = []
        self.state_log: List[Node] = [initial_state]

    def push(self, new_state: Node, transformation: Statement, is_inverse: bool):
        """ Pushes the next state and transformation information into object """
        self.current_state = new_state
        self.state_log.append(new_state)
        self.transformations.append((transformation, is_inverse))

    def __hash__(self):
        """ Since a proves history isn't important for the prover, we only have to hash the current state """
        return hash(self.current_state)

    def __repr__(self):
        return f"{str(self.current_state)}\n Transformations: \n {"; \n".join(str(transformation) + ("^-1" if is_inverse else "") for transformation, is_inverse in self.transformations)}, \n State log: {"; \n".join(str(state) for state in self.state_log)}"

class Prover:
    def __init__(self):
        self.statements: List[Statement] = []
        self.goal_statement: Statement | None = None

    def prove(self, print_trace: bool = False) -> Prove | None:
        """ Runs different search algorithms to find prove for goal statement """
        goal_statement_relation = self.goal_statement.relation
        statements = self.statements.copy()
        for i, statement in enumerate(self.statements):
            if statement.relation != goal_statement_relation:
                if print_trace: print(f"Need to update relation of {statement}")
                statements[i] = update_relation(statement, goal_statement_relation)

        # BFS (direct and inverse application)
        start = self.goal_statement.expression1
        finish = self.goal_statement.expression2
        queue_start_to_fin = deque([Prove(start)])
        queue_fin_to_start = deque([Prove(finish)])
        visited_start_to_fin = {Prove(start)}
        visited_fin_to_start = {Prove(finish)}
        depth = 1

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

            if state_start_to_fin:
                if state_start_to_fin.current_state.id_less_equal(finish):
                    return state_start_to_fin
            if state_fin_to_start:
                if state_fin_to_start.current_state.id_less_equal(start):
                    return state_fin_to_start

            # Get new current states
            for statement in self.statements:
                # Forward
                if state_start_to_fin:
                    for new_node in statement(state_start_to_fin.current_state, print_trace=print_trace):
                        new_state = copy.deepcopy(state_start_to_fin)
                        new_state.push(new_node, statement, False)
                        if new_state not in visited_start_to_fin:
                            if print_trace: print(f"Add {new_node}")
                            visited_start_to_fin.add(new_state)
                            queue_start_to_fin.append(new_state)
                # Backward
                if state_fin_to_start:
                    for new_node in statement.apply_inverse(state_fin_to_start.current_state, print_trace=print_trace):
                        new_state = copy.deepcopy(state_fin_to_start)
                        new_state.push(new_node, statement, False)
                        if new_state not in visited_fin_to_start:
                            if print_trace: print(f"Add {new_node}")
                            visited_fin_to_start.add(new_state)
                            queue_fin_to_start.append(new_state)
            depth += 1
        return None


def update_relation(input_statement: Statement, to_relation: Relation) -> Statement:
    """ Tries to update statements relation to given relation according to relation hierarchy """
    # TODO
    return input_statement
