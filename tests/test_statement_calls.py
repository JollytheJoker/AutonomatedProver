import pytest
from typing import Dict, Tuple, Generator
from MObject import Object, Function, Quantor, ElementrySet, Set, PowerSet, FunctionSet, Variable
from ExpressionTree import Node
from Statement import Statement, Relation


def test_quantor_logic():
    """Tests mathematical logical quantor logic"""
    assert (Quantor.FORALL >= Quantor.EXISTS) is True
    assert (Quantor.EXISTS >= Quantor.FORALL) is False
    assert Quantor.FORALL.min(Quantor.EXISTS) == Quantor.EXISTS
    assert Quantor.EXISTS.min(Quantor.DEFINE) is None


def test_mapping_exact_match():
    """Tests if the exact same node will generate the exact same mapping"""
    obj = ElementrySet(quantor=Quantor.FORALL)
    node1 = Node(obj)
    node2 = Node(obj)

    mapping, is_valid = node1.get_mappings_dict_for_replacement(node2)
    assert is_valid is True
    assert len(mapping) == 0


def test_mapping_with_quantor_substitution():
    """Tests is variables are mapped correctly, if the quantor is valid"""
    X = ElementrySet(quantor=Quantor.FORALL)
    f = Function(quantor=Quantor.DEFINE, binding_quantity=(X, X))

    x_forall = Node(Variable(quantor=Quantor.FORALL, binding_quantity=(X, )))
    node_x = Node(f, [x_forall])

    constant_define = Node(Variable(quantor=Quantor.DEFINE, binding_quantity=(X, )))
    node_concrete = Node(f, [constant_define])

    mapping, is_valid = node_x.get_mappings_dict_for_replacement(node_concrete)

    assert is_valid is True
    assert x_forall in mapping
    assert mapping[x_forall] == constant_define


def test_mapping_invalid_quantor_substitution():
    """Tests if mapping is negative if quantors disallow it"""
    X = ElementrySet(quantor=Quantor.FORALL)
    f = Function(quantor=Quantor.DEFINE, binding_quantity=(X, X))

    x_forall = Node(Variable(quantor=Quantor.FORALL, binding_quantity=(X,)))
    node_x = Node(f, [x_forall])

    constant_define = Node(Variable(quantor=Quantor.DEFINE, binding_quantity=(X,)))
    node_concrete = Node(f, [constant_define])

    mapping, is_valid = node_concrete.get_mappings_dict_for_replacement(node_x)
    assert is_valid is False


def test_statement_application():
    """Tests with an example"""
    X = ElementrySet(quantor=Quantor.DEFINE, assosiation='X')
    Y = ElementrySet(quantor=Quantor.DEFINE, assosiation='Y')
    Z = ElementrySet(quantor=Quantor.DEFINE, assosiation='Z')
    R = ElementrySet(quantor=Quantor.DEFINE, assosiation='R')
    dx = Function(quantor=Quantor.DEFINE, binding_quantity=(X, X), assosiation='dx')
    dy = Function(quantor=Quantor.DEFINE, binding_quantity=(Y, Y), assosiation='dy')
    dz = Function(quantor=Quantor.DEFINE, binding_quantity=(Z, Z), assosiation='dz')
    f = Function(quantor=Quantor.FORALL, binding_quantity=(X, Y), assosiation='f')
    g = Function(quantor=Quantor.FORALL, binding_quantity=(Y, Z), assosiation='g')
    x = Variable(quantor=Quantor.FORALL, binding_quantity=(X, ), assosiation='x')
    y = Variable(quantor=Quantor.FORALL, binding_quantity=(Y, ), assosiation='y')
    Bx = Function(quantor=Quantor.DEFINE, binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(FunctionSet(quantor=Quantor.FORALL, binding_quantity=(X, X)), R, X)), PowerSet(quantor=Quantor.FORALL, binding_quantity=(X, ))), assosiation='B_{dx}')
    By = Function(quantor=Quantor.DEFINE, binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(FunctionSet(quantor=Quantor.FORALL, binding_quantity=(Y, Y)), R, Y)), PowerSet(quantor=Quantor.FORALL, binding_quantity=(Y, ))), assosiation='B_{dy}')
    Bz = Function(quantor=Quantor.DEFINE, binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(FunctionSet(quantor=Quantor.FORALL, binding_quantity=(Z, Z)), R, Z)), PowerSet(quantor=Quantor.FORALL, binding_quantity=(Z, ))), assosiation='B_{dz}')
    epsilon = Variable(quantor=Quantor.FORALL, binding_quantity=(R, ))
    delta = Variable(quantor=Quantor.EXISTS, binding_quantity=(R, ))

    g_continuity_left = Node(g, child_nodes=[Node(By, child_nodes=[Node(dy), Node(delta), Node(y)])])     # g(B_{delta}^{dy}(y))
    g_continuity_right = Node(Bz, child_nodes=[Node(dz), Node(epsilon), Node(g, child_nodes=[Node(y)])])   # B_{epsilon}^{dz}(g(y))
    gf_continuity_right = Node(Bz, child_nodes=[Node(dz), Node(epsilon), Node(g, child_nodes=[Node(f, child_nodes=[Node(x)])])])  # B_{epsilon}^{dz}(g(f(x)))

    g_continuous = Statement(expression1=g_continuity_left, expression2=g_continuity_right, relation=Relation.SUBSET)

    applied_g_term = next(g_continuous.apply_inverse(gf_continuity_right))
    assert applied_g_term == Node(g, child_nodes=[Node(By, child_nodes=[Node(dy), Node(delta), Node(f, child_nodes=[Node(x)])])])

    f_continuity_right = Node(f, child_nodes=[Node(Bx, child_nodes=[Node(dx), Node(delta), Node(x)])])  # f(B_{delta}^{dx}(x))
    f_continuity_left = Node(By, child_nodes=[Node(dy), Node(epsilon), Node(f, child_nodes=[Node(x)])])  # B_{epsilon}^{dy}(f(x))

    f_continuous = Statement(expression1=f_continuity_right, expression2=f_continuity_left, relation=Relation.SUBSET)
    applied_gf_term = next(f_continuous.apply_inverse(applied_g_term))
    assert applied_gf_term == Node(g, child_nodes=[Node(f, child_nodes=[Node(Bx, child_nodes=[Node(dx), Node(delta), Node(x)])])])

