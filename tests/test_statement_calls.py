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

    expr1 = Node(g, child_nodes=[Node(By, child_nodes=[Node(dy), Node(delta), Node(y)])])     # g(B_{delta}^{dy}(y))
    expr2 = Node(Bz, child_nodes=[Node(dz), Node(epsilon), Node(g, child_nodes=[Node(y)])])   # B_{epsilon}^{dz}(g(y))
    term = Node(Bz, child_nodes=[Node(dz), Node(epsilon), Node(g, child_nodes=[Node(f, child_nodes=[Node(x)])])])  # B_{epsilon}^{dz}(g(f(x)))

    statement = Statement(expression1=expr1, expression2=expr2, relation=Relation.SUBSET)

    res = next(statement.apply_inverse(term))
    assert res == Node(g, child_nodes=[Node(By, child_nodes=[Node(dy), Node(delta), Node(f, child_nodes=[Node(x)])])])

    expr1_f = Node(f, child_nodes=[Node(Bx, child_nodes=[Node(dx), Node(delta), Node(x)])])  # f(B_{delta}^{dx}(x))
    expr2_f = Node(By, child_nodes=[Node(dy), Node(epsilon), Node(f, child_nodes=[Node(x)])])  # B_{epsilon}^{dy}(f(x))

    statement_f = Statement(expression1=expr1_f, expression2=expr2_f, relation=Relation.SUBSET)
    res_2 = next(statement_f.apply_inverse(res))
    print(res_2)


