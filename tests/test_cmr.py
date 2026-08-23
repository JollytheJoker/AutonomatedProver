import pytest
from ExpressionTree import Node, _get_cycle_nodes
from MObject import Set, Function, Quantor
from GraphBuilder import GraphBuilder


@pytest.fixture
def base_sets():
    X = Set(association="X")
    Y = Set(association="Y")
    Z = Set(association="Z")
    return X, Y, Z

@pytest.fixture
def remap(base_sets):
    X, _, _ = base_sets
    return Function(association="r", binding_quantity=(X, X), quantor=Quantor.DEFINE)

@pytest.fixture
def functions(base_sets):
    X, Y, Z = base_sets
    f = Function(association="f", binding_quantity=(X, Y), quantor=Quantor.DEFINE)
    g = Function(association="g", binding_quantity=(Y, Z), quantor=Quantor.DEFINE)
    return f, g


def test_primitive_eq_basic(base_sets):
    """ Tests simple equality of basic leave nodes """
    X, Y, _ = base_sets

    node_x = Node(X)
    node_x2 = Node(X)
    node_y = Node(Y)

    assert node_x.primitive_eq(node_x2) is True
    assert (node_x == node_x2) is True
    assert node_x.primitive_eq(node_y) is False


def test_primitive_eq_obj_id_minus_one(base_sets, functions):
    """ Tests a special case with obj_id of None """
    X, Y, _ = base_sets
    node_x = Node(Set(binding_quantity=(X, ), nested_depth=0))
    node_y = Node(Set(binding_quantity=(Y, ), nested_depth=0))
    f, _ = functions

    node_f_applied1 = Node(f)(node_x)
    node_f_applied2 = Node(f)(node_x)

    assert node_f_applied1.primitive_eq(node_f_applied2) is True
    assert (node_f_applied1 == node_f_applied2) is True
    assert node_f_applied1.primitive_eq(node_y) is True
    assert (node_f_applied1 == node_y) is False


def test_primitive_eq_type_mismatch(base_sets, functions):
    """ Tests if type differences are given false """
    X, _, _ = base_sets
    f, _ = functions
    node_x = Node(X)
    node_f = Node(f)

    assert node_x.primitive_eq(node_f) is False

def test_different_function_application(base_sets):
    """ Tests that differenct application of functions gives false in primitive equal """
    X, _, _ = base_sets
    node_x = Node(X)

    f1 = Function(binding_quantity=(X, X), quantor=Quantor.DEFINE)
    f2 = Function(binding_quantity=(X, X), quantor=Quantor.DEFINE)

    assert Node(f1)(node_x).primitive_eq(Node(f2)(node_x)) is False


def test_primitive_contains_self(base_sets):
    """ Tests that all nodes contain themselves """
    X, _, _ = base_sets
    node_x = Node(X)

    results = list(node_x.primitive_contains(node_x))

    assert len(results) == 1
    assert results[0][0] is node_x
    assert results[0][1] is None


def test_primitive_contains_deep_search(base_sets, remap):
    """ Checks if function applications of nodes are returned """
    X, _, _ = base_sets
    node_target = Node(X)

    root_node = Node(remap)(node_target)

    results = list(root_node.primitive_contains(node_target))

    assert len(results) == 1
    assert results[0][0].primitive_eq(node_target)


def test_primitive_contains_not_found(base_sets, remap):
    """ If """
    X, Y, _ = base_sets
    node_x = Node(X)
    node_y = Node(Y)

    root_node = Node(remap)(node_x)

    results = list(root_node.primitive_contains(node_y))
    assert len(results) == 0


def test_strict_eq_vs_id_less_eq(base_sets, functions):
    """ Tests that copmare functions is used properly """
    X, _, _ = base_sets

    node_x1 = Node(X)
    node_x2 = Node(X)

    root1 = Node(functions[0])(node_x1)
    root2 = Node(functions[0])(node_x2)

    assert root1 == root2
    assert root1.id_less_eq(root2) is True


def test_eq_mismatch_arguments(base_sets, functions):
    """ Tests, if __eq__ is wrong for different argument chains """
    X, Y, Z = base_sets

    root1 = Node(functions[0])(Node(X))

    assert (root1 == Node(X)) is False


# CYCLICAL GRAPHS - CMR USAGE
def test_different_cycle_length(base_sets, remap):
    """ Tests that graphs with different cycle lengths but different edge weight still give equality """
    X, _, _ = base_sets

    graph1 = GraphBuilder()
    graph2 = GraphBuilder()

    # Build 4 times to self remaping graph
    r = graph1.add_node(remap, 1, X)
    n_out = graph1.add_node(X, 0)
    graph1.set_root_node(r)

    e_self = graph1.add_edge(r, 4, r)
    graph1.add_edge_to_slot(r, e_self, 0)  # Add edge as 1. argument of the root node

    e_out = graph1.add_edge(n_out, 1, r)
    graph1.add_edge_to_slot(r, e_out, 0)  # Add edge to 1. Argument slot as output node

    root_node1 = graph1.build()

    # Build 2-cyclcial but 2-lenght graph
    r = graph2.add_node(remap, 1, X)
    n_inbetween = graph2.add_node(remap, 1, X)
    n_out = graph2.add_node(X, 0)
    graph2.set_root_node(r)

    r_to_n_inbetween = graph2.add_edge(n_inbetween, 2, r)
    graph2.add_edge_to_slot(r, r_to_n_inbetween, 0)

    n_inbetween_to_r = graph2.add_edge(r, 1, n_inbetween)
    graph2.add_edge_to_slot(n_inbetween,n_inbetween_to_r, 0)

    r_to_n_out = graph2.add_edge(n_out, 1, r)
    graph2.add_edge_to_slot(r, r_to_n_out, 0)

    root_node2 = graph2.build()

    assert root_node1 == root_node2

    # Unmatching case, weight of 5
    graph1.change_edge_weight(e_self, 5)
    root_node1 = graph1.build()

    assert root_node1 != root_node2

def test_different_cycle_length_complex(base_sets):
    """ Tests that graphs with different cycle lengths in a more complex scenario with more layered cycle length and residu set usage """
    X, _, _ = base_sets

    f = Function(binding_quantity=(X, X), quantor=Quantor.DEFINE)
    g = Function(binding_quantity=(X, X), quantor=Quantor.DEFINE)

    # Graphs node repetitions (manually for now)
    n = 1000

    # Graph 1: A 6-cycle alternating between f and g, with edge weight 4 * n
    # from the root f into the cycle, plus an output edge to X.

    graph1 = GraphBuilder()

    # Nodes
    root_f = graph1.add_node(f, 1, X)

    g1 = graph1.add_node(g, 1, X)
    f2 = graph1.add_node(f, 1, X)
    g2 = graph1.add_node(g, 1, X)
    f3 = graph1.add_node(f, 1, X)
    g3 = graph1.add_node(g, 1, X)

    # Output node
    n_out = graph1.add_node(X, 0)

    graph1.set_root_node(root_f)

    e1 = graph1.add_edge(g1, (4 * n), root_f)
    graph1.add_edge_to_slot(root_f, e1, 0)

    e2 = graph1.add_edge(f2, 1, g1)
    graph1.add_edge_to_slot(g1, e2, 0)

    e3 = graph1.add_edge(g2, 1, f2)
    graph1.add_edge_to_slot(f2, e3, 0)

    e4 = graph1.add_edge(f3, 1, g2)
    graph1.add_edge_to_slot(g2, e4, 0)

    e5 = graph1.add_edge(g3, 1, f3)
    graph1.add_edge_to_slot(f3, e5, 0)

    e6 = graph1.add_edge(root_f, 1, g3)
    graph1.add_edge_to_slot(g3, e6, 0)

    e_out = graph1.add_edge(n_out, 1, root_f)
    graph1.add_edge_to_slot(root_f, e_out, 0)

    root_node1 = graph1.build()

    # Graph 2: A root f with three independent 4-cycles, with initial
    # edge weights 3n - 1, 3n, and 1 respectively, plus an input edge to X.

    graph2 = GraphBuilder()

    root_f = graph2.add_node(f, 1, X)
    n_in = graph2.add_node(X, 0)

    graph2.set_root_node(root_f)

    g1 = graph2.add_node(g, 1, X)
    f2 = graph2.add_node(f, 1, X)
    g2 = graph2.add_node(g, 1, X)

    e1 = graph2.add_edge(g1, (3 * n - 1), root_f)
    graph2.add_edge_to_slot(root_f, e1, 0)

    e2 = graph2.add_edge(f2, 1, g1)
    graph2.add_edge_to_slot(g1, e2, 0)

    e3 = graph2.add_edge(g2, 1, f2)
    graph2.add_edge_to_slot(f2, e3, 0)

    e4 = graph2.add_edge(root_f, 1, g2)
    graph2.add_edge_to_slot(g2, e4, 0)

    g3 = graph2.add_node(g, 1, X)
    f3 = graph2.add_node(f, 1, X)
    g4 = graph2.add_node(g, 1, X)

    e5 = graph2.add_edge(g3, (3 * n), root_f)
    graph2.add_edge_to_slot(root_f, e5, 0)

    e6 = graph2.add_edge(f3, 1, g3)
    graph2.add_edge_to_slot(g3, e6, 0)

    e7 = graph2.add_edge(g4, 1, f3)
    graph2.add_edge_to_slot(f3, e7, 0)

    e8 = graph2.add_edge(root_f, 1, g4)
    graph2.add_edge_to_slot(g4, e8, 0)

    g5 = graph2.add_node(g, 1, X)
    f4 = graph2.add_node(f, 1, X)
    g6 = graph2.add_node(g, 1, X)

    e9 = graph2.add_edge(g5, 1, root_f)
    graph2.add_edge_to_slot(root_f, e9, 0)

    e10 = graph2.add_edge(f4, 1, g5)
    graph2.add_edge_to_slot(g5, e10, 0)

    e11 = graph2.add_edge(g6, 1, f4)
    graph2.add_edge_to_slot(f4, e11, 0)

    e12 = graph2.add_edge(root_f, 1, g6)
    graph2.add_edge_to_slot(g6, e12, 0)

    e_in = graph2.add_edge(n_in, 1, root_f)
    graph2.add_edge_to_slot(root_f, e_in, 0)

    root_node2 = graph2.build()

    assert root_node1 == root_node2


