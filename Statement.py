from __future__ import annotations

import uuid
from functools import cached_property
from typing import Union, Any, Generator, Dict, List, Tuple
from ExpressionTree import Node
from dataclasses import dataclass, field, replace
from enum import Enum


class Relation(Enum):
    SUBSETQ = r'\subseteq'
    SUBSET = r'\subset'
    SUPPERSETQ = r'\supseteq'
    SUPPERSET = r'\supset'
    LEQ = '<='
    LE = '<'
    GEQ = '>='
    GE = '>'
    EQUAL = '='
    NEQUAL = '!='

    def get_negation(self) -> Relation:
        match self:
            case Relation.SUBSETQ:
                return Relation.SUPPERSETQ
            case Relation.SUBSET:
                return Relation.SUPPERSET
            case Relation.SUPPERSETQ:
                return Relation.SUBSETQ
            case Relation.SUPPERSET:
                return Relation.SUBSET
            case Relation.LEQ:
                return Relation.GE
            case Relation.LE:
                return Relation.GEQ
            case Relation.GEQ:
                return Relation.LE
            case Relation.GE:
                return Relation.LEQ
            case Relation.EQUAL:
                return Relation.NEQUAL
            case Relation.NEQUAL:
                return Relation.EQUAL
            case _:
                raise ValueError(f"No negation defined for {self}")


class LogicalOperation(Enum):
    AND = 'and'
    OR = 'or'
    EQUAL = '='
    NEQUAL = '!='

    def get_negation(self) -> LogicalOperation:
        match self:
            case LogicalOperation.AND:
                return LogicalOperation.OR
            case LogicalOperation.OR:
                return LogicalOperation.AND
            case LogicalOperation.EQUAL:
                return LogicalOperation.NEQUAL
            case LogicalOperation.NEQUAL:
                return LogicalOperation.EQUAL
            case _:
                raise ValueError(f"No negation defined for {self}")

    def negate_inner(self) -> bool:
        """ Returns if negating the symbol is enough or inner statements must be negated as well """
        if self is LogicalOperation.EQUAL or self is LogicalOperation.NEQUAL:
            return False
        return True

class Bool(Enum):
    TRUE = 'true'
    FALSE = 'false'

    @cached_property
    def negation(self) -> Bool:
        if self is Bool.TRUE:
            return Bool.FALSE
        return Bool.TRUE


@dataclass(frozen=True)
class Statement:
    """
    Statements are tree strucutures (ast) that will be used to express logical relation of different nodes terms.
    Leave nodes must be terms (so of type node of the expression trees).
    Logical functions such as (land and lor) are nodes in that graph with two child nodes.
    Statements or leave nodes must be passed into a relation to make them into boolean expressions.
    """
    node_function: Union[LogicalOperation, Relation, Node, Bool, MetaObject]
    child_right: Union[Statement, None] = None
    child_left: Union[Statement, None] = None

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
            if _is_of_type(self.child_right.node_function, Node) or _is_of_type(self.child_left.node_function, Node):
                raise Exception("Logical operations must have boolean children")

        if isinstance(self.node_function, Relation):
            if not self.child_right or not self.child_left:
                raise Exception("Relations must have children nodes")
            if not _is_of_type(self.child_right.node_function, Node) or not _is_of_type(self.child_left.node_function, Node):
                raise Exception("Relation must have children of type nodes (so an expression graph)")

        if self.is_leave_node:
            return

        if _is_of_type(self.node_function, Node):
            raise Exception("Expression graphs can't have child nodes")

        if _is_of_type(self.node_function, Bool) and not self.is_leave_node:
            raise Exception("Boolean values can't have child nodes")

        if _is_of_type(self.node_function, MetaObject) and not self.is_leave_node:
            raise Exception("MetaObject values can't have child nodes")

    def __str__(self):
        if self.is_leave_node:
            return str(self.node_function)
        return f'{self.child_left} {self.node_function} {self.child_right}'

    @cached_property
    def output_type(self) -> type:
        """ Returns the output type of this node """
        if isinstance(self.node_function, LogicalOperation) or isinstance(self.node_function, Relation) or isinstance(self.node_function, Bool):
            return Bool
        if isinstance(self.node_function, MetaObject):
            return self.node_function.obj_type

        return type(self.node_function)

    @cached_property
    def is_leave_node(self) -> bool:
        """ Retuns if self is the root node, thus doesn't have any child nodes """
        return self.child_right is None and self.child_left is None

    @cached_property
    def negation(self) -> Statement:
        """
        Returns a negated version of this statement.
        We need to implement the distrubution axiom here to avoid having parialy negated statements.
        Relations are directly negated.
        Every math object will get negated in the quantor propergting through the quantor chain
        """
        if isinstance(self.node_function, LogicalOperation):
            if self.node_function.negate_inner():
                if self.child_left is None:
                    new_left = None
                else:
                    new_left = self.child_left.negation
                if self.child_right is None:
                    new_right = None
                else:
                    new_right = self.child_right.negation

                return replace(self, node_function=self.node_function.get_negation(), child_left=new_left, child_right=new_right)
            return replace(self, node_function=self.node_function.get_negation(), child_left=self.child_left, child_right=self.child_right)

        if isinstance(self.node_function, Relation):
            try:
                return replace(self, node_function=self.node_function.get_negation())
            except ValueError:
                # Need to negate quantors
                return replace(self, child_left=self.child_left.negation, child_right=self.child_right.negation)

        if isinstance(self.node_function, Node):
            return replace(self, node_function=self.node_function.negation)

        raise Exception(f"Can't negate type {type(self.node_function)}")

    @cached_property
    def term_order(self) -> int:
        """ Returns the term order of this statement """
        # TODO: Implement
        return id(self)

    def __eq__(self, other: Statement) -> bool:
        """ Strict equality check, going down the expression tree """
        if not _eq_node_function(self.node_function, other.node_function):
            return False

        return self.child_right == other.child_right and self.child_left == other.child_left

    def __hash__(self) -> int:
        return hash((hash(self.node_function), hash(self.child_left), hash(self.child_right)))

    def primitive_eq(self, other: Statement) -> bool:
        """ Checks for quantative equivalence of two statements """
        if isinstance(self.node_function, Node) and not _is_of_type(other.node_function, Node):
            return False

        elif isinstance(self.node_function, Bool) and not _is_of_type(other.node_function, Bool):
            return False

        elif isinstance(self.node_function, MetaObject):
            if not _is_of_type(self.node_function, type(other.node_function)):
                return False

        elif not self.node_function == other.node_function:
            return False

        return _primitive_eq_child_nodes(self.child_left, other.child_left) and _primitive_eq_child_nodes(self.child_right, other.child_right)

    def primitive_contains(self, other: Statement) -> Generator[Statement]:
        """ Checks if given statement is contained within this statement """
        if self.primitive_eq(other):
            yield self

        for res in self.child_left.primitive_contains(other):
            yield res

        for res in other.child_right.primitive_contains(self):
            yield res

    def get_replacement_list(self, other: Statement, replacement_list: Union[List[Tuple[Statement, Statement]], None] = None) -> List[Tuple[Statement, Statement]]:
        """ Retunrs the necessary replacements on this statement to make a step that is only primitvely equal completely equal """
        if not replacement_list:
            replacement_list = []

        # TODO: Requires more depth for node replacement!!!
        if _eq_node_function(self.node_function, other.node_function):
            replacement_list = self.child_left.get_replacement_list(other.child_left, replacement_list)
            replacement_list = self.child_right.get_replacement_list(other.child_right, replacement_list)
        else:
            replacement_list.append((other, self))

        return replacement_list

    def replace_with_list(self, replacement_list: List[Tuple[Statement, Statement]]) -> Statement:
        """ Replaces this statement's AST parts that are equivalent to any first-tuple-value in the replacement dict """
        for (key, val) in replacement_list:
            if self == key:
                return val

        if self.child_right is not None:
            new_right = self.child_right.replace_with_list(replacement_list)
        else:
            new_right = None
        if self.child_left is not None:
            new_left = self.child_left.replace_with_list(replacement_list)
        else:
            new_left = None

        return replace(self, node_function=self.node_function, child_left=new_left, child_right=new_right)

    def simplify(self, match_statement: Statement, simplification: Statement) -> Generator[Statement]:
        """ Checks ats from this node for match_statement structure. If enherits match_statement structure, we will replace it with the simplifaction accordingly """
        if self.primitive_eq(match_statement):
            replacement_list = self.get_replacement_list(match_statement)
            yield simplification.replace_with_list(replacement_list)

        if isinstance(self.child_left, Statement):
            for res in self.child_left.simplify(match_statement, simplification):
                yield res

        if isinstance(self.child_right, Statement):
            for res in self.child_right.simplify(match_statement, simplification):
                yield res


@dataclass(frozen=True, eq=False)
class MetaObject:
    """ Represents a placeholder for any object of given type """
    obj_type: type
    name: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    negated: bool = False

    def is_of_type(self, target_type: type) -> bool:
        return issubclass(self.obj_type, target_type)

    @cached_property
    def negation(self) -> MetaObject:
        return MetaObject(self.obj_type, self.name, negated=(not self.negated))

    def __eq__(self, other) -> bool:
        return self.name == other.name

    def __hash__(self):
        return hash((self.obj_type, self.name, self.negated))


# Helper functions for type comparisons
def _is_of_type(obj: Any, target_type: type) -> bool:
    if isinstance(obj, target_type):
        return True
    if isinstance(obj, MetaObject):
        return obj.is_of_type(target_type)
    return False

# Helper/wrapper for equality checks
def _primitive_eq_child_nodes(child1: Union[Statement, None], child2: Union[Statement, None]) -> bool:
    """
    Helper function to compare two child nodes primitively.
    If both statements, we just return their primitive equivalence.
    None and something not None will always return False.
    """
    if child1 is None and child2 is None:
        return True
    if child1 is None or child2 is None:
        return False

    return child1.primitive_eq(child2)

def _eq_node_function(node_function1: Union[LogicalOperation, Relation, Node, Bool, MetaObject], node_function2: Union[LogicalOperation, Relation, Node, Bool, MetaObject]) -> bool:
    if isinstance(node_function1, Node):
        if not isinstance(node_function2, Node):
            return False
        return node_function1 == node_function2

    if isinstance(node_function1, MetaObject):
        if not isinstance(node_function2, MetaObject):
            return False
        return node_function1.obj_type == node_function2.obj_type

    if not node_function1 == node_function2:
        return False

    return True

def replace_statement_with_other(statement1: Statement, statement2: Statement) -> Statement:
    replacement_list = statement1.get_replacement_list(statement2)
    return statement1.replace_with_list(replacement_list)