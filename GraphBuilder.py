from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Union, Tuple, List

from ExpressionTree import Node, Edge, ArgumentSlot
from MObject import Object


@dataclass
class _EdgeBuilder:
    to_node: _NodeBuilder
    weight: Union[int, float, _NodeBuilder]
    parent_node: _NodeBuilder

    def __hash__(self) -> int:
        return hash((id(self.to_node), id(self.weight), id(self.parent_node)))

@dataclass
class _ArgumentSlotBuilder:
    parent_node: _NodeBuilder
    desired_output: Object
    edge_sequence: List[_EdgeBuilder, ...]

    def __hash__(self) -> int:
        return hash((id(self.parent_node), id(self.desired_output)))

@dataclass
class _NodeBuilder:
    math_object: Object
    argument_slots: Tuple[_ArgumentSlotBuilder, ...]

    def __hash__(self) -> int:
        return hash((id(self.math_object), id(self.argument_slots)))


class GraphBuilder:
    def __init__(self):
        self._nodes: List[_NodeBuilder] = []
        self._edges: List[_EdgeBuilder] = []
        self._root_node: Union[_NodeBuilder, None] = None

    def add_node(self, math_object: Object, number_of_arguments: int, *desired_output: Object) -> _NodeBuilder:
        """ Returns and adds a private node builder object """
        if len(desired_output) != number_of_arguments:
            raise ValueError("Number of desired output arguments must be equal to number of arguments")
        node = _NodeBuilder(math_object, ())
        node.argument_slots = tuple(_ArgumentSlotBuilder(node, desired_output[i], []) for i in range(number_of_arguments))

        self._nodes.append(node)
        return node

    @staticmethod
    def add_edge_to_slot(node: _NodeBuilder, edge: _EdgeBuilder, idx: int):
        """ Adds an edge to a node argument slots at a desired index """
        if idx >= len(node.argument_slots):
            raise ValueError("Index out of range")

        node.argument_slots[idx].edge_sequence.append(edge)

    def add_edge(self, to_node: _NodeBuilder, weight: Union[int, float, _NodeBuilder], from_node: _NodeBuilder) -> _EdgeBuilder:
        """ Returns and adds a private edge builder object """
        edge = _EdgeBuilder(to_node, weight, from_node)

        self._edges.append(edge)
        return edge

    @staticmethod
    def change_edge_weight(edge: _EdgeBuilder, new_weight: Union[int, float, _NodeBuilder]) -> None:
        """ Changes the weight of an edge """
        edge.weight = new_weight

    def set_root_node(self, root_node: _NodeBuilder):
        """ Sets the graph's root node """
        self._root_node = root_node


    def build(self):
        """
        Builds the graph from the graph independent of node creation series.
        Mutable nodes get directly transformed to immutable nodes.
        Returns only the graph's root node
        """
        final_nodes = {node: object.__new__(Node) for node in self._nodes}
        final_edges = {edge: object.__new__(Edge) for edge in self._edges}

        # Convert builder nodes to immutable node objects
        for builder_node, node in final_nodes.items():
            object.__setattr__(node, "math_object", builder_node.math_object)
            object.__setattr__(node, "argument_slots", tuple(object.__new__(ArgumentSlot) for _ in builder_node.argument_slots))

        # Convert builder edges to immutable edges
        for builder_edge, edge in final_edges.items():
            object.__setattr__(edge, "to_node", final_nodes[builder_edge.to_node])
            object.__setattr__(edge, "weight", builder_edge.weight)
            object.__setattr__(edge, "parent_node", final_nodes[builder_edge.parent_node])

        # Edit created argument slots to account for edges
        for builder_node, node in final_nodes.items():
            for builder_slot, slot in zip(builder_node.argument_slots, node.argument_slots):
                object.__setattr__(slot, "parent_node", node)
                object.__setattr__(slot, "desired_output", builder_slot.desired_output)
                object.__setattr__(slot, "edge_sequence", tuple(final_edges[builder_edge] for builder_edge in builder_slot.edge_sequence))

        if not self._root_node:
            # Fall-back: Try to find a unique node that is not pointed to at all, that would be the root node
            pointed_to_nodes = set()
            for edge in self._edges:
                pointed_to_nodes.add(edge.to_node)

            diff = {node for node in self._nodes} - pointed_to_nodes
            if len(diff) == 1:
                warnings.warn("Fall-back solution. No root-node set")
                return final_nodes[diff.pop()]

            raise Exception("Can't build graph with not set root node and not unique non-pointed to node")
        return final_nodes[self._root_node]

