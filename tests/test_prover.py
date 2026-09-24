from dataclasses import replace
from GraphBuilder import GraphBuilder
import pytest
from Prover import Prover
from MObject import Function, Set, Quantor
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

