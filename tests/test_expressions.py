import pytest
from ExpressionTree import Node
from dataclasses import replace
from MObject import Object, Function, Quantor, ElementrySet, Set, PowerSet, FunctionSet, Variable


def test_leaf_node_creation():
    """Test that a node with no children initializes correctly."""
    u = ElementrySet(association="X")
    node = Node(math_object=u)

    assert len(node.child_nodes) == 0
    assert node.node_object == u


def test_non_function_with_children_raises():
    """Test that you can't assign a child node to a non-function"""
    u = ElementrySet(association="X")
    child_node = Node(math_object=u)

    with pytest.raises(Exception, match="Can only call functions"):
        Node(math_object=u, child_nodes=[[(child_node, 1)]])


def test_function_wrong_input_length_raises():
    """Test that the number of children must be the same length of the ConcatenatedSet."""
    u1 = ElementrySet(association="X")
    u2 = ElementrySet(association="Y")
    u3 = ElementrySet(association="Z")

    concat_inputs = Set(binding_quantity=(u1, u2, u3))
    out_set = ElementrySet(association="Out")

    f = Function(binding_quantity=(concat_inputs, out_set), association="f")

    child1 = Node(math_object=u1)
    child2 = Node(math_object=u2)

    with pytest.raises(Exception, match="Function has not the given number of inputs"):
        Node(math_object=f, child_nodes=[[(child1, 1)], [(child2, 1)]])


def test_node_tuple_creation():
    u1 = ElementrySet(association="X")
    f1 = Function(association="f", binding_quantity=(u1, u1), quantor=Quantor.DEFINE)
    x1 = Variable(association="x", binding_quantity=(u1,), quantor=Quantor.DEFINE)

    node_x = Node(math_object=x1)
    node_f = Node(math_object=f1, child_nodes=[[(node_x, 1)]])
    assert node_f.node_object == Variable(binding_quantity=(u1, ), quantor=Quantor.EXISTS, obj_id=-1)

    node_f_of_u1 = Node(math_object=f1, child_nodes=[[(Node(u1), 1)]])
    assert node_f_of_u1.node_object == replace(u1, obj_id=-1, quantor=Quantor.EXISTS)

    p1 = PowerSet(binding_quantity=(u1, ), quantor=Quantor.DEFINE)
    node_f_of_p1 = Node(math_object=f1, child_nodes=[[(Node(p1), 1)]])
    assert isinstance(node_f_of_p1.node_object, PowerSet)


def test_primitive_eq():
    """Test the primitive equality logic between two identical nodes."""
    u1 = ElementrySet(association="X")
    u2 = ElementrySet(association="Y")

    node1 = Node(math_object=u1)
    node2 = Node(math_object=u2)

    assert node1.primitive_eq(node2) is False

    f1 = Function(association="f", binding_quantity=(u1, u2), quantor=Quantor.DEFINE)
    x1 = Variable(association="x", binding_quantity=(u1,), quantor=Quantor.DEFINE)
    y1 = Variable(association="y", binding_quantity=(u2,), quantor=Quantor.DEFINE)

    node_x = Node(math_object=x1)
    node_f = Node(math_object=f1, child_nodes=[[(node_x, 1)]])
    node_y = Node(math_object=y1)

    assert node_f.primitive_eq(node_y) is True
    assert node_f.primitive_eq(node2) is False
