import pytest
from Prover import Prover
from MObject import ElementrySet, Function, Quantor
from CommonStatements import continuous, definitions
from ExpressionTree import Node


def test_prove_on_continuity():
    X = ElementrySet(quantor=Quantor.DEFINE, assosiation='X')
    Y = ElementrySet(quantor=Quantor.DEFINE, assosiation='Y')
    Z = ElementrySet(quantor=Quantor.DEFINE, assosiation='Z')
    dx = Function(quantor=Quantor.DEFINE, binding_quantity=(X, X), assosiation='dx')
    dy = Function(quantor=Quantor.DEFINE, binding_quantity=(Y, Y), assosiation='dy')
    dz = Function(quantor=Quantor.DEFINE, binding_quantity=(Z, Z), assosiation='dz')

    f = Function(quantor=Quantor.FORALL, binding_quantity=(X, Y), assosiation='f')
    g = Function(quantor=Quantor.FORALL, binding_quantity=(Y, Z), assosiation='g')

    f_continuity = continuous(f, dx, dy)
    g_continuity = continuous(g, dy, dz)
    gf_continuity = continuous(Node(g, child_nodes=[Node(f)]), dx, dz)

    prover = Prover()
    prover.statements = [f_continuity, g_continuity]
    prover.goal_statement = gf_continuity

    res = prover.prove()

    assert res
