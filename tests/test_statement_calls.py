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
    X = ElementrySet(quantor=Quantor.DEFINE)
    Y = ElementrySet(quantor=Quantor.DEFINE)
    Z = ElementrySet(quantor=Quantor.DEFINE)
    R = ElementrySet(quantor=Quantor.DEFINE)
    dx = Function(quantor=Quantor.DEFINE, binding_quantity=(X, X))
    dy = Function(quantor=Quantor.DEFINE, binding_quantity=(Y, Y))
    dz = Function(quantor=Quantor.DEFINE, binding_quantity=(Z, Z))
    f = Function(quantor=Quantor.FORALL, binding_quantity=(X, Y))
    g = Function(quantor=Quantor.FORALL, binding_quantity=(Y, Z))
    x = Variable(quantor=Quantor.FORALL, binding_quantity=(X, ))
    y = Variable(quantor=Quantor.FORALL, binding_quantity=(Y, ))
    Bx = Function(quantor=Quantor.DEFINE, binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(FunctionSet(quantor=Quantor.FORALL, binding_quantity=(X, X)), R, X)), PowerSet(quantor=Quantor.FORALL, binding_quantity=(X, ))))
    By = Function(quantor=Quantor.DEFINE, binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(FunctionSet(quantor=Quantor.FORALL, binding_quantity=(Y, Y)), R, Y)), PowerSet(quantor=Quantor.FORALL, binding_quantity=(Y, ))))
    Bz = Bx = Function(quantor=Quantor.DEFINE, binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(FunctionSet(quantor=Quantor.FORALL, binding_quantity=(Z, Z)), R, Z)), PowerSet(quantor=Quantor.FORALL, binding_quantity=(Z, ))))
    epsilon = Variable(quantor=Quantor.FORALL, binding_quantity=(R, ))
    delta = Variable(quantor=Quantor.EXISTS, binding_quantity=(R, ))

    expr1 = Node(g, child_nodes=[Node(By, child_nodes=[Node(dy), Node(delta), Node(y)])])
    expr2 = Node(Bz, child_nodes=[Node(dz), Node(epsilon), Node(g, child_nodes=[Node(y)])])
    f_term = Node(By, child_nodes=[Node(dy), Node(epsilon), Node(f, child_nodes=[Node(x)])])

    statement = Statement(expression1=expr1, expression2=expr2, relation=Relation.SUBSET)

    res = statement(f_term)
    assert res != f_term

