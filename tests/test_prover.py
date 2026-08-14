import pytest
from Prover import Prover
from MObject import ElementrySet, Function, Quantor
from CommonStatements import continuous, definitions
from ExpressionTree import Node


def test_prove_on_continuity():
    X = ElementrySet(quantor=Quantor.DEFINE, association='X')
    Y = ElementrySet(quantor=Quantor.DEFINE, association='Y')
    Z = ElementrySet(quantor=Quantor.DEFINE, association='Z')
    dx = Function(quantor=Quantor.DEFINE, binding_quantity=(X, X), association='dx')
    dy = Function(quantor=Quantor.DEFINE, binding_quantity=(Y, Y), association='dy')
    dz = Function(quantor=Quantor.DEFINE, binding_quantity=(Z, Z), association='dz')

    f = Function(quantor=Quantor.FORALL, binding_quantity=(X, Y), association='f')
    g = Function(quantor=Quantor.FORALL, binding_quantity=(Y, Z), association='g')

    f_continuity = continuous(f, dx, dy)
    g_continuity = continuous(g, dy, dz)
    gf_continuity = continuous(Node(g, child_nodes=[[(Node(f), 1)]]), dx, dz)

    prover = Prover()
    prover.statements = [f_continuity, g_continuity]
    prover.goal_statement = gf_continuity

    res = prover.prove()

    assert res
