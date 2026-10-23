from dataclasses import replace
from GraphBuilder import GraphBuilder
import pytest
from Prover import Prover
from MObject import Function, Set, Quantor, Object
from CommonStatements import continuous, DEFINITIONS, topolgy, _is_topology, transitiv, logical_axioms, inverse
from ExpressionTree import Node
from Statement import Relation, LogicalOperation, Bool, Statement, canonicalize_ac
from Knuth_Bendix_Algorithm import reducde_statement_modulo_directed_axioms


def test_prove_on_continuity():
    X = Set(association='X')
    tx = topolgy(X)
    tx = replace(tx, association='tx')
    Y = Set(association='Y')
    ty = topolgy(Y)
    ty = replace(ty, association='ty')
    Z = Set(association='Z')
    tz = topolgy(Z)
    tz = replace(tz, association='tz')

    f = Function(binding_quantity=(X, Y), association='f')
    g = Function(binding_quantity=(Y, Z), association='g')
    f_inv, f_inv_cond = inverse(f)
    g_inv, g_inv_cond = inverse(g)

    cf, _ = continuous(f, tx, ty, f_inv)
    cg, _ = continuous(g, ty, tz, g_inv)

    # g(f)
    gf_graph = GraphBuilder()
    f_node = gf_graph.add_node(f, 0)
    g_node = gf_graph.add_node(g, 1, Z)

    edge = gf_graph.add_edge(to_node=f_node, weight=1, from_node=g_node)

    gf_graph.add_edge_to_slot(g_node, edge, 0)
    gf_graph.set_root_node(g_node)

    # f^-1(g^-1)
    gf_inv_graph = GraphBuilder()
    f_inv_node = gf_inv_graph.add_node(f_inv, 1, X)
    g_inv_node = gf_inv_graph.add_node(g_inv, 0)

    edge = gf_inv_graph.add_edge(to_node=g_inv_node, weight=1, from_node=f_inv_node)

    gf_inv_graph.add_edge_to_slot(f_inv_node, edge, 0)
    gf_inv_graph.set_root_node(f_inv_node)

    cgf, conditions = continuous(gf_graph.build(), tx, tz, gf_inv_graph.build())

    trans = transitiv(LogicalOperation.IMPLIES)

    prover = Prover((cf, cg, trans), cgf)

    assert prover.prove() != (None, )


def test_transitivity_prove():
    """ Show that ((A => B) & (B => C)) => (A => C) """
    prover = Prover((), transitiv(LogicalOperation.IMPLIES))

    print(prover.prove())

def test_definition_unfolding():
    """ Show that f(A U B) = f(A) U f(B)"""
    X = Set(association='X')
    Y = Set(association='Y')
    A = Set(association='A', binding_quantity=(X,))
    node_A = Node(A)
    B = Set(association='B', binding_quantity=(X,))
    node_B = Node(B)
    x = Set(association='x', binding_quantity=(X,), nested_depth=0)
    node_x = Node(x)

    union_function = Function(association='U', binding_quantity=(Set(binding_quantity=(X, X)), X))
    f = Function(binding_quantity=(X, Y), association='f')

    AUB_graph = GraphBuilder()
    u_node = AUB_graph.add_node(union_function, 2, X, X)
    a_node = AUB_graph.add_node(A, 0)
    b_node = AUB_graph.add_node(B, 0)

    edgeA = AUB_graph.add_edge(to_node=a_node, from_node=u_node, weight=1)
    edgeB = AUB_graph.add_edge(to_node=b_node, from_node=u_node, weight=1)

    AUB_graph.add_edge_to_slot(u_node, edgeA, 0)
    AUB_graph.add_edge_to_slot(u_node, edgeB, 1)
    AUB_graph.set_root_node(u_node)

    node_AUB = AUB_graph.build()

    # Necessary definitions
    # 1. x in A U B <=> x in A or x in B
    lhs = Statement(Relation.ELEMENTOF, Statement(node_x), Statement(node_AUB))
    rhs = Statement(LogicalOperation.OR, Statement(Relation.ELEMENTOF, Statement(node_x), Statement(node_A)), Statement(Relation.ELEMENTOF, Statement(node_x), Statement(node_B)))
    union_definition = Statement(LogicalOperation.EQUAL, lhs, rhs)

    # 2. y in f(M) => (exists x' in M => y=f(x'))
    M_X = Set(quantor=Quantor.FORALL, binding_quantity=(X,), association='M')
    node_M = Node(M_X)
    y = Set(quantor=Quantor.FORALL, binding_quantity=(Y,), nested_depth=0, association='y')
    node_y = Node(y)
    x_prime = Set(quantor=Quantor.EXISTS, binding_quantity=(X,), nested_depth=0, association="x'")
    node_x_prime = Node(x_prime)

    fM_node = _apply_helper(f, M_X)
    fx_prime_node = _apply_helper(f, x_prime)

    lhs = Statement(Relation.ELEMENTOF, Statement(node_y), Statement(fM_node))
    rhs = Statement(LogicalOperation.IMPLIES, Statement(Relation.ELEMENTOF, Statement(node_x_prime), Statement(node_M)), Statement(Relation.EQUAL, Statement(node_y), Statement(fx_prime_node)))
    set_application_definition = Statement(LogicalOperation.IMPLIES, lhs, rhs)

    # 3. M = N <=> for all y: y in M <=> y in N
    N_X = Set(quantor=Quantor.FORALL, binding_quantity=(X,), association='N')
    node_N = Node(N_X)

    lhs = Statement(Relation.EQUAL, Statement(node_M), Statement(node_N))
    rhs = Statement(LogicalOperation.EQUAL, Statement(Relation.ELEMENTOF, Statement(node_y), Statement(node_M)), Statement(Relation.ELEMENTOF, Statement(node_y), Statement(node_N)))
    set_equivalence_definition = Statement(LogicalOperation.EQUAL, lhs, rhs)

    # f(A U B)
    fAUB_graph = AUB_graph
    f_node = fAUB_graph.add_node(f, 1, Y)

    edge = fAUB_graph.add_edge(to_node=u_node, weight=1, from_node=f_node)
    fAUB_graph.add_edge_to_slot(f_node, edge, 0)
    fAUB_graph.set_root_node(f_node)
    node_fAUB = fAUB_graph.build()

    # f(A) U f(B)
    fAUfB_graph = GraphBuilder()
    u_node = fAUfB_graph.add_node(union_function, 2, Y, Y)
    fa_node = fAUfB_graph.add_node(f, 1, Y)
    fb_node = fAUfB_graph.add_node(f, 1, Y)
    A_node = fAUfB_graph.add_node(A, 0)
    B_node = fAUfB_graph.add_node(B, 0)

    fA_edge = fAUfB_graph.add_edge(to_node=A_node, from_node=fa_node, weight=1)
    fB_edge = fAUfB_graph.add_edge(to_node=B_node, from_node=fb_node, weight=1)
    U0_edge = fAUfB_graph.add_edge(to_node=fa_node, from_node=u_node, weight=1)
    U1_edge = fAUfB_graph.add_edge(to_node=fb_node, from_node=u_node, weight=1)

    fAUfB_graph.add_edge_to_slot(fa_node, fA_edge, 0)
    fAUfB_graph.add_edge_to_slot(fb_node, fB_edge, 0)
    fAUfB_graph.add_edge_to_slot(u_node, U0_edge, 0)
    fAUfB_graph.add_edge_to_slot(u_node, U1_edge, 1)

    fAUfB_graph.set_root_node(u_node)

    fAUfB_node = fAUfB_graph.build()

    goal = Statement(Relation.EQUAL, Statement(node_fAUB), Statement(fAUfB_node))


def _apply_helper(f: Function, x: Object):
    """ Builds a graph that applys the function (f) on the given object (x): f(x) """
    graph = GraphBuilder()

    f_node = graph.add_node(f, 1, f.binding_quantity[1])
    x_node = graph.add_node(x, 0)

    edge = graph.add_edge(to_node=x_node, weight=1, from_node=f_node)

    graph.add_edge_to_slot(f_node, edge, 0)
    graph.set_root_node(f_node)
    return graph.build()
