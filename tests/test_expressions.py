import pytest
from ExpressionTree import Node, ArgumentSlot
from dataclasses import replace
from MObject import Set, Function, Quantor


def test_leaf_node_creation():
    """ Test that a node with no children initializes correctly. """
    s = Set()
    node = Node(s)

    assert len(node.argument_slots) == 0
    assert node.node_object == s


def test_non_function_with_children_raises():
    """Test that you can't assign a child node to a non-function"""
    s = Set()
    n = Node(s)

    with pytest.raises(Exception):
        Node(math_object=s, argument_slots=(ArgumentSlot.create(n, s), ))


def test_node_call():
    """Tests that calling a node works and raises errors"""
    s = Set()
    f = Node(Function((s, s)))

    res = f(s)
    assert isinstance(res, Node)
    assert len(res.argument_slots) == 1

    f2 = Node(Function((Set((s, s)), s)))
    assert len(f2(s, s).argument_slots) == 2

    with pytest.raises(Exception):
        Node(s)(s)

    with pytest.raises(Exception):
        f(s, s)

    with pytest.raises(NotImplementedError):
        f(2)

    w = Set()
    with pytest.raises(Exception):
        f(w)


def test_node_tuple_creation():
    X = Set(association="X")
    f = Function(association="f", binding_quantity=(X, X), quantor=Quantor.DEFINE)
    x = Set(association="x", binding_quantity=(X,), nested_depth=0, quantor=Quantor.DEFINE)

    node_x = Node(x)
    node_f = Node(f)(x)
    assert node_f.node_object.binding_quantity == (X, )
    assert node_f.node_object.quantor == Quantor.EXISTS
    assert node_f.node_object.nested_depth == 0
    assert node_f.node_object.obj_id is None

    assert Node(f)(X).node_object.nested_depth == 1

