from __future__ import annotations
from functools import cached_property
from typing import Generator, Dict, Union
from ExpressionTree import Node
from dataclasses import dataclass, field, replace
from enum import Enum


class Relation(Enum):
    SUBSET = r'\subseteq'
    EQUAL = '='
    LEQ = '<='
    GEQ = '>='

class LogicalOperation(Enum):
    AND = 'and'
    OR = 'or'


@dataclass(frozen=True)
class Statement:
    """
    Statements are tree strucutures (ast) that will be used to express logical relation of different nodes terms.
    Leave nodes must be terms (so of type node of the expression trees).
    Logical functions such as (land and lor) are nodes in that graph with two child nodes.
    Statements or leave nodes must be passed into a relation to make them into boolean expressions.
    """
    node_function: Union[LogicalOperation, Relation, Node]
    child_right: Union[Statement, None]
    child_left: Union[Statement, None]

    def __post_init__(self):
        """
        Checks if definition is valid.
        If children are nodes, then node_function must be a realation.
        If the node_function is a logical operation, then child nodes can't be expression graphs
        If the node_function is an expression graph, they must be a leave node
        """
        if isinstance(self.node_function, LogicalOperation):
            if not self.child_right or not self.child_left:
                raise Exception("Logical operations must have children nodes")
            if isinstance(self.child_right.node_function, Node) or isinstance(self.child_left.node_function, Node):
                raise Exception("Logical operations must have boolean children")

        if isinstance(self.node_function, Relation):
            if not self.child_right or not self.child_left:
                raise Exception("Relations must have children nodes")
            if not isinstance(self.child_right.node_function, Node) or not isinstance(self.child_left.node_function, Node):
                raise Exception("Relation must have children of type nodes (so an expression graph)")

        if isinstance(self.node_function, Node):
            if not self.is_leave_node:
                raise Exception("Expression graphs can't have child nodes")

    @cached_property
    def is_leave_node(self) -> bool:
        """ Retuns if self is root node, thus doesn't have any child nodes """
        return self.child_right is None and self.child_left is None
