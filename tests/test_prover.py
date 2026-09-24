from dataclasses import replace
from GraphBuilder import GraphBuilder
import pytest
from Prover import Prover
from MObject import Function, Set, Quantor
from CommonStatements import continuous, DEFINITIONS, topolgy, _is_topology, transitiv
from ExpressionTree import Node
from CommonStatements import inverse
from Statement import Relation, LogicalOperation, Bool, Statement


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

    cf, _ = continuous(f, tx, ty)
    cg, _ = continuous(g, ty, tz)

    gf_graph = GraphBuilder()
    f_node = gf_graph.add_node(f, 0)
    g_node = gf_graph.add_node(g, 1, Z)

    edge = gf_graph.add_edge(to_node=f_node, weight=1, from_node=g_node)

    gf_graph.add_edge_to_slot(g_node, edge, 0)
    gf_graph.set_root_node(g_node)

    cgf, conditions = continuous(gf_graph.build(), tx, tz)

    prover = Prover((cf, cg), cgf)

    trans = transitiv(LogicalOperation.IMPLIES)

    print(cgf)
    step1 = next(cgf.simplify(trans[0], trans[1]))

    print(step1)

    #breakpoint()
    step2 = next(step1.simplify(cg, Statement(Bool.TRUE)))

    print(step2)

    print(prover.prove())
