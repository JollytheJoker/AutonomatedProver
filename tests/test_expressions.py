import pytest
from ExpressionTree import Node
from MObject import Object, Function, Quantor, ConcatenatedSet, ElementrySet


def test_leaf_node_creation():
    """Test that a node with no children initializes correctly."""
    u = ElementrySet(assosiation="X")
    node = Node(math_object=u)

    assert node.is_root is False
    assert len(node.child_nodes) == 0
    assert node.node_tuple == u.toTuple()

def test_non_function_with_children_raises():
    """Test that you can't assign a child node to a non-function"""
    u = ElementrySet(assosiation="X")
    child_node = Node(math_object=u)

    with pytest.raises(Exception, match="Can only call functions"):
        Node(math_object=u, child_nodes=frozenset([child_node]))

def test_function_wrong_input_length_raises():
    """Test that the number of children must be the same length of the ConcatenatedSet."""
    u1 = ElementrySet(assosiation="X")
    u2 = ElementrySet(assosiation="Y")
    u3 = ElementrySet(assosiation="Z")

    concat_inputs = ConcatenatedSet(binding_quantity=(u1, u2, u3))
    out_set = ElementrySet(assosiation="Out")

    f = Function(binding_quantity=(concat_inputs, out_set), assosiation="f")

    child1 = Node(math_object=u1)
    child2 = Node(math_object=u2)

    with pytest.raises(Exception, match="Function has not the given number of inputs"):
        Node(math_object=f, child_nodes=frozenset([child1, child2]))


def test_primitive_eq():
    """Test the primitive equality logic between two identical nodes."""
    u1 = ElementrySet(assosiation="X")
    u2 = ElementrySet(assosiation="X")  # Same structure

    node1 = Node(math_object=u1)
    node2 = Node(math_object=u2)

    assert node1.primitive_eq(node2) is True