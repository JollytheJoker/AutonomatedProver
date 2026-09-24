from collections import deque
from dataclasses import replace
from typing import List, Tuple, Union, Dict, Any
from GraphBuilder import GraphBuilder, get_builder
from ExpressionTree import Node
from MObject import Set, Function, Quantor
from Statement import Statement, LogicalOperation, MetaObject, Bool, Relation
from Knuth_Bendix_Algorithm import knuth_bendix_algorithm, kbo_compare, simplify_statement_on_system, simplify_fully


# ---------------------- BASIC AXIOMS ----------------------

# (\land & \lor will be refered to 'o')#
logical_axioms: List[Tuple[Statement, Statement]] = []

# Define 3 placeholders
a = Statement(MetaObject(Statement, name='A'))
b = Statement(MetaObject(Statement, name='B'))
c = Statement(MetaObject(Statement, name='C'))

# AXIOMS
# a xor false = a
lhs = Statement(LogicalOperation.XOR, a, Statement(Bool.FALSE))
logical_axioms.append((lhs, a))

# a xor a = false
lhs = Statement(LogicalOperation.XOR, a, a)
logical_axioms.append((lhs, Statement(Bool.FALSE)))

# a and true = a
lhs = Statement(LogicalOperation.AND, a, Statement(Bool.TRUE))
logical_axioms.append((lhs, a))

# a and false = false
lhs = Statement(LogicalOperation.AND, a, Statement(Bool.FALSE))
logical_axioms.append((lhs, Statement(Bool.FALSE)))

# a and a = a
lhs = Statement(LogicalOperation.AND, a, a)
logical_axioms.append((lhs, a))

# Distibutivity (a xor b) and c = (a and c) xor (b and c)
lhs = Statement(LogicalOperation.AND, Statement(LogicalOperation.XOR, a, b), c)
rhs = Statement(LogicalOperation.XOR, Statement(LogicalOperation.AND, a, c), Statement(LogicalOperation.AND, b, c))
logical_axioms.append((lhs, rhs))

"""print("KNUTH-BENDIX-SOLUTION")
system = knuth_bendix_algorithm(logical_axioms)
for key, value in system:
    print(f'Key: {key}, Value: {value}')


test_statement = Statement(LogicalOperation.XOR, a, Statement(LogicalOperation.XOR, a, a))
test_statement = test_statement.canonical

print(simplify_fully(test_statement, system))"""



# TODO: implement ZFC



# TODO: INGEGER DEFINITIONS AND OPERATIONS

# ---------------------- RELATIONAL DEFINITIONS ----------------------
def transitiv(r: Union[Relation, LogicalOperation]) -> Tuple[Statement, Statement]:
    """ Returns the statement that a relation is transitiv """
    A, B, C = MetaObject(Statement), MetaObject(Statement), MetaObject(Statement)
    arb = Statement(r, Statement(A), Statement(B))
    brc = Statement(r, Statement(B), Statement(C))
    arc = Statement(r, Statement(A), Statement(C))

    return arc, Statement(LogicalOperation.AND, arb, brc) #

# ---------------------- SET & FUNCTIONAL DEFINITIONS ----------------------
def inverse(f: Union[Function, Node]) -> Tuple[Union[Function, Node], Tuple[Statement, ...]]:
    """ Returns an instance of an inverse function and the statement that makes the function the functions inverse """
    if isinstance(f, Function):
        in_set = f.input_set
        out_set = f.output_set

        f_inv = replace(f, binding_quantity=(out_set, in_set), association=f'{f.association}^-1')
        in_el = Set((in_set,), Quantor.FORALL, '', 0)
        out_el = Set((out_set,), Quantor.FORALL, '', 0)

        f_node = Node(f)
        f_inv_node = Node(f_inv)
        in_el_node = Node(in_el)
        out_el_node = Node(out_el)

        # f^-1(f(x)) = x
        A = Statement(Relation.EQUAL, Statement(f_inv_node(f_node(in_el_node))), Statement(in_el_node))

        # f(f^-1(y)) = y
        B = Statement(Relation.EQUAL, Statement(f_node(f_inv_node(out_el_node))), Statement(out_el_node))

        return f_inv, (Statement(LogicalOperation.AND, A, B), )

    # f is a node
    if not isinstance(f.node_object, Function):
        raise TypeError(f'The given object {f} is no function')

    # TODO: Note: We can currently only inverte nodes that always have one exact input
    if len(f.node_object.binding_quantity[0].binding_quantity) > 1:
        raise NotImplementedError(f'The given function {f} can not be generally inverted')

    # Invert every math_object function and reverse order (so of edges)
    builder = GraphBuilder()
    inverse_conditions: list[Statement] = []
    node_mappings: Dict[Node, Any] = {}

    if not isinstance(f.math_object, Function):
        raise TypeError(f'The given math object {f} is no function')

    f_inv, f_cond = inverse(f.math_object)
    inverse_conditions.extend(list(f_cond))
    node_mappings[f] = builder.add_node(f_inv, 0)

    queue = deque([f])
    visited = set()

    while queue:
        new_to_node = queue.popleft()
        builder_node = node_mappings[new_to_node]
        builder.set_root_node(builder_node)

        if len(new_to_node.argument_slots) > 1:
            raise NotImplementedError(f'The given function {f} can not be generally inverted (ERROR)')

        if len(new_to_node.argument_slots) < 1:
            if isinstance(new_to_node.math_object, Function):
                continue
            raise Exception(f'The given object {new_to_node} is not a function')

        new_parent_node = new_to_node.argument_slots[0].edge_sequence[-1].to_node

        if not isinstance(new_parent_node.math_object, Function):
            raise TypeError(f'The given math object {new_parent_node.math_object} is no function')

        new_parent_inverse, new_parent_condition = inverse(new_parent_node.math_object)
        inverse_conditions.extend(list(new_parent_condition))
        new_builder_node = builder.add_node(new_parent_inverse, 1, new_parent_inverse.binding_quantity[1])
        node_mappings[new_parent_node] = new_builder_node

        new_edge = builder.add_edge(to_node=builder_node, from_node=new_builder_node, weight=new_to_node.argument_slots[0].edge_sequence[-1].weight)
        builder.add_edge_to_slot(new_builder_node, new_edge, 0)

        for i, edge in enumerate(new_to_node.argument_slots[0].edge_sequence[:-1][::-1]):
            if not isinstance(edge.to_node.math_object, Function):
                raise TypeError(f'The given math object {edge.to_node.math_object} is no function')

            new_inv, new_inv_condition = inverse(edge.to_node.math_object)
            inverse_conditions.extend(list(new_inv_condition))
            new_builder_node = builder.add_node(new_inv, 1, new_inv.binding_quantity[1])
            node_mappings[edge.to_node] = new_builder_node

            new_edge = builder.add_edge(to_node=new_builder_node, from_node=builder_node, weight=edge.weight)
            builder.add_edge_to_slot(builder_node, new_edge, i)

        # Add new nodes to queue
        for edge in new_to_node.argument_slots[0].edge_sequence:
            if not edge.to_node in visited:
                queue.append(edge.to_node)

        visited.add(new_to_node)

    return builder.build(), tuple(inverse_conditions)

# ---------------------- TOPOLOGICAL DEFINITIONS ----------------------
def topolgy(X: Set) -> Set:
    """ Returns a topology set tau for this statement X """
    if not isinstance(X, Set):
        raise TypeError('X is not a set')

    if X.nested_depth == 0:
        raise Exception('X is not true set (most likely variable)')

    if not X.binding_quantity:
        return Set(binding_quantity=(X, ), nested_depth=2)
    return replace(X, nested_depth=X.nested_depth + 1)

def _is_topology(X: Set, tau: Set) -> bool:
    """ Checks if tau could be topology of X (equivalent to nested depth of tau is X's + 1) """
    if tau.binding_quantity == X.binding_quantity:
        return tau.nested_depth == X.nested_depth + 1

    return tau.binding_quantity == (X,) and tau.nested_depth == 2

def continuous(f: Union[Function, Node], topology_in: Set, topology_out: Set) -> Tuple[Statement, Tuple[Statement, ...]]:
    """ Returns the statement that a function f is continous """
    if isinstance(f, Function):
        if not _is_topology(f.binding_quantity[0], topology_in):
            raise Exception(f"{topology_in} is no topology of {f.binding_quantity[0]}")
        if not _is_topology(f.binding_quantity[1], topology_out):
            raise Exception(f"{topology_out} is no topology of {f.binding_quantity[1]}")
    elif isinstance(f, Node):
        if not _is_topology(f.node_object.binding_quantity[0], topology_in):
            raise Exception(f"{topology_in} is no topology of {f.node_object.binding_quantity[0]}")
        if not _is_topology(f.node_object.binding_quantity[1], topology_out):
            raise Exception(f"{topology_out} is no topology of {f.node_object.binding_quantity[1]}")
    else:
        raise TypeError('f is not a function or Node')

    f_inv, inv_conditions = inverse(f)

    if isinstance(f, Function):
        U = Set((f.output_set,), Quantor.FORALL)
    elif isinstance(f, Node):
        U = Set((f.math_object.output_set, ), Quantor.FORALL)

    # U open
    u_in = Statement(Relation.ELEMENTOF, Statement(Node(U)), Statement(Node(topology_out)))

    # f^-1(U) open
    if isinstance(f, Function):
        f_inv_u_graph = GraphBuilder()
        U_node = f_inv_u_graph.add_node(U, 0)
        f_inv_node = f_inv_u_graph.add_node(f_inv, 1, f_inv.binding_quantity[1])

        edge = f_inv_u_graph.add_edge(to_node=U_node, from_node=f_inv_node, weight=1)
        f_inv_u_graph.add_edge_to_slot(f_inv_node, edge, 0)
        f_inv_u_graph.set_root_node(f_inv_node)

        f_in = Statement(Relation.ELEMENTOF, Statement(f_inv_u_graph.build()), Statement(Node(topology_in)))
    else:
        f_in = Statement(Relation.ELEMENTOF, Statement(_apply_on_function(f_inv, U)), Statement(Node(topology_in)))

    return Statement(LogicalOperation.IMPLIES, u_in, f_in), inv_conditions


# HELPER
def _apply_on_function(f: Node, x: Union[Function, Set]) -> Node:
    """ Checks that f is has a functional node_object and applies it to x """
    if not isinstance(f.node_object, Function):
        raise Exception('f is not a function')

    builder = get_builder(f)

    current_child = builder.get_root_node()
    while current_child.argument_slots:
        current_child = current_child.argument_slots[0].edge_sequence[-1].to_node

    # Add slot to current_child
    builder.add_slot_to_node(current_child, current_child.math_object.binding_quantity[1])

    # Apply x
    x_node = builder.add_node(x, 0)
    edge = builder.add_edge(to_node=x_node, from_node=current_child, weight=1)

    builder.add_edge_to_slot(current_child, edge, 0)

    return builder.build()


# UNORDERED TUPLES FOR DEFINITION UNFOLDING
DEFINITIONS: List[Tuple[Statement | Statement]] = []