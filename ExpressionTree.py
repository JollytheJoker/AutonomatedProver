from __future__ import annotations
from dataclasses import dataclass, field
from MObject import Object, Function, Quantor, ConcatenatedSet
from typing import FrozenSet, Tuple


@dataclass
class Node:
    """
    One node in the expression tree graph. Contains the child nodes for recursive build up
    """
    math_object: Object
    node_tuple: Tuple = field(default_factory=tuple)
    child_nodes: FrozenSet['Node'] = field(default_factory=frozenset)
    is_root: bool = field(default=False)

    def __post_init__(self):
        if len(self.child_nodes) > 0 and not isinstance(self.math_object, Function):
            raise Exception("Can only call functions")
        if len(self.child_nodes) > 1:
            if not isinstance(self.math_object.binding_quantity[0], ConcatenatedSet):
                raise Exception("A function can not have multiple inputs if binding quantity is not concatenated set")
            if len(self.math_object.binding_quantity[0]) != len(self.child_nodes):
                raise Exception("Function has not the given number of inputs")

        self.object_tuple = self.math_object.toTuple()
        self.set_node_tuple()

    def set_node_tuple(self):
        """
        Recursively build up the node tuple using the function at the node
        """
        if not self.child_nodes:
            self.node_tuple = self.math_object.toTuple()
            return

        quantor = Quantor.FORALL
        for node in self.child_nodes:
            node.set_node_tuple()
            # Update quantor
            if node.node_tuple[3] == Quantor.DEFINE or node.node_tuple[3] == Quantor.EXISTS:
                if quantor != Quantor.EXISTS:
                    quantor = node.node_tuple[3]
        self.node_tuple = (self.math_object.binding_quantity[1], self.math_object.binding_quantity[1], self.math_object.binding_quantity, quantor, -1)

    def primitive_eq(self, other: Node):
        """
        Runs premitive equal check between two nodes. They are equal if type and binding quantity are the same
        """
        return self.node_tuple[0] == other.node_tuple[0] and self.node_tuple[1] == other.node_tuple[1]

    def primitive_contains(self, other: Node):
        """
        Runs premitive recursive check on tree structure to yield possible equal nodes.
        """
        if self.primitive_eq(other):
            yield self
        for child_node in self.child_nodes:
            for res in child_node.primitive_contains(other):
                yield res

    def __hash__(self):
        return hash(self.node_tuple)
