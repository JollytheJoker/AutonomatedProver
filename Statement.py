from __future__ import annotations
import copy
import uuid
import warnings
from collections import defaultdict
from functools import cached_property
from itertools import product, permutations
from typing import Union, Any, Generator, Dict, List, Tuple
from ExpressionTree import Node, eq, get_unequal_parts_cmr_reduced
from dataclasses import dataclass, field, replace
from enum import Enum
from MObject import Function, Set


# Standart Operations (Relations, Logical, Boolen-Values)
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
    ELEMENTOF = 'in'
    NOTELEMENTOF = 'not in'

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
            case Relation.ELEMENTOF:
                return Relation.NOTELEMENTOF
            case Relation.NOTELEMENTOF:
                return Relation.ELEMENTOF
            case _:
                raise ValueError(f"No negation defined for {self}")

    def __str__(self):
        return str(self.value)


class LogicalOperation(Enum):
    AND = 'and'
    OR = 'or'
    XOR = 'xor'
    EQUAL = '='
    NEQUAL = '!='
    IMPLIES = '=>'
    IMPLIEDBY = '<='
    DOUBLEARROW = '<=>'

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
            case LogicalOperation.XOR:
                return LogicalOperation.DOUBLEARROW
            case LogicalOperation.IMPLIES:
                return LogicalOperation.IMPLIEDBY
            case LogicalOperation.IMPLIEDBY:
                return LogicalOperation.IMPLIES
            case LogicalOperation.DOUBLEARROW:
                return LogicalOperation.XOR
            case _:
                raise ValueError(f"No negation defined for {self}")

    def negate_inner(self) -> bool:
        """ Returns if negating the symbol is enough or inner statements must be negated as well """
        if self is LogicalOperation.EQUAL or self is LogicalOperation.NEQUAL or self is LogicalOperation.DOUBLEARROW or self is LogicalOperation.XOR:
            return False
        return True

    def __str__(self):
        if self is LogicalOperation.AND:
            return '&'
        if self is LogicalOperation.OR:
            return '|'
        if self is LogicalOperation.EQUAL:
            return 'is'
        if self is LogicalOperation.XOR:
            return '⊕'
        if self is LogicalOperation.DOUBLEARROW:
            return '<=>'
        if self is LogicalOperation.IMPLIES:
            return '=>'
        if self is LogicalOperation.IMPLIEDBY:
            return '<='
        return 'is not'


class Bool(Enum):
    TRUE = 'true'
    FALSE = 'false'
    AMBIGUOUS = 'ambiguous'
    NAMBIGUOUS = 'nambiguous'

    @cached_property
    def negation(self) -> Bool:
        if self is Bool.TRUE:
            return Bool.FALSE
        if self is Bool.AMBIGUOUS:
            return Bool.NAMBIGUOUS
        if self is Bool.NAMBIGUOUS:
            return Bool.AMBIGUOUS
        return Bool.TRUE

    def __str__(self):
        if self.value == 'true':
            return 'T'
        if self.value == 'false':
            return 'F'
        if self.value == 'ambiguous':
            return '~'
        return '!~'


# Properties-class
@dataclass(frozen=True)
class OperationProperties:
    """ A data structure that saves canonical properties for an operation in the operations_properties dictionary """
    associative: bool = False
    commutative: bool = False


OPERATION_PROPERTIES = {
    LogicalOperation.AND: OperationProperties(associative=True, commutative=True),
    #LogicalOperation.OR: OperationProperties(associative=True, commutative=True),
    LogicalOperation.XOR: OperationProperties(associative=True, commutative=True),
    #LogicalOperation.DOUBLEARROW: OperationProperties(associative=True, commutative=True)
}


@dataclass(frozen=True)
class Statement:
    """
    Statements are tree strucutures (ast) that will be used to express logical relation of different nodes terms.
    Leave nodes must be terms (so of type node of the expression trees).
    Logical functions such as (land and lor) are nodes in that graph with two child nodes.
    Statements or leave nodes must be passed into a relation to make them into boolean expressions.
    """
    node_function: Union[LogicalOperation, Relation, Node, Bool, MetaObject]
    child_left: Union[Statement, None] = None
    child_right: Union[Statement, None] = None

    def __post_init__(self):
        """
        Checks if definition is valid.
        If children are nodes, then node_function must be a realation.
        If the node_function is a logical operation, then child nodes can't be expression graphs
        If the node_function is an expression graph, they must be a leave node
        Updates and adds new objects to a precedence list
        """
        # Update precedence
        if not isinstance(self.node_function, Node):
            add_precedence(self.node_function)
        else:
            # Add all nodes math_object's to precedence list
            for node in self.node_function.get_all_nodes():
                add_precedence(node.math_object)

        if isinstance(self.node_function, LogicalOperation):
            if not self.child_right or not self.child_left:
                raise Exception("Logical operations must have children nodes")
            if _is_of_type(self.child_right.node_function, Node) or _is_of_type(self.child_left.node_function, Node):
                raise Exception("Logical operations must have boolean children")

        if isinstance(self.node_function, Relation):
            if not self.child_right or not self.child_left:
                raise Exception("Relations must have children nodes")
            if not _is_of_type(self.child_right.node_function, Node) or not _is_of_type(self.child_left.node_function,
                                                                                        Node):
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
        return f'({str(self.child_left)} {str(self.node_function)} {str(self.child_right)})'

    @cached_property
    def output_type(self) -> type:
        """ Returns the output type of this node """
        if isinstance(self.node_function, LogicalOperation) or isinstance(self.node_function, Relation) or isinstance(
                self.node_function, Bool):
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
        We need to implement the distribution axiom here to avoid having partially negated statements.
        Relations are directly negated.
        Every math object will get negated in the quantor propitiating through the quantor chain
        """
        if isinstance(self.node_function, LogicalOperation):
            '''if self.node_function is LogicalOperation.XOR:
                # not (A xor B) = (A and B) xor (not A and not B)
                return Statement(LogicalOperation.XOR,
                                 Statement(LogicalOperation.AND, self.child_left, self.child_right),
                                 Statement(LogicalOperation.AND, self.child_left.negation, self.child_left.negation))

            if self.node_function is LogicalOperation.AND:
                # not (A and B) = (A and not B) xor (not A and B)
                return Statement(LogicalOperation.XOR,
                                 Statement(LogicalOperation.AND, self.child_left, self.child_right.negation),
                                 Statement(LogicalOperation.AND, self.child_left.negation, self.child_right))'''

            if self.node_function.negate_inner():
                if self.child_left is None:
                    new_left = None
                else:
                    new_left = self.child_left.negation
                if self.child_right is None:
                    new_right = None
                else:
                    new_right = self.child_right.negation

                return replace(self, node_function=self.node_function.get_negation(), child_left=new_left,
                               child_right=new_right).canonical
            return replace(self, node_function=self.node_function.get_negation(), child_left=self.child_left,
                           child_right=self.child_right).canonical

        if isinstance(self.node_function, Relation):
            return replace(self, node_function=self.node_function.get_negation()).canonical

        if isinstance(self.node_function, Node) or isinstance(self.node_function, MetaObject):
            return replace(self, node_function=self.node_function.negation).canonical

        if isinstance(self.node_function, Bool):
            return replace(self, node_function=self.node_function.negation).canonical

        raise Exception(f"Can't negate type {type(self.node_function)}")

    @cached_property
    def kbo_weight(self) -> int:
        """ Returns the statement's weight for KBO through reccursion """
        # Spacial-Case Node
        if isinstance(self.node_function, Node):
            weight = self.node_function.kbo_weight
        else:
            weight = 1

        if self.child_left:
            weight += self.child_left.kbo_weight
        if self.child_right:
            weight += self.child_right.kbo_weight
        return weight

    @cached_property
    def kbo_precedence(self) -> int:
        """ Returns the kbo precedence of this statement node object """
        return get_precedence(self.node_function)

    @cached_property
    def canonical(self) -> Statement:
        """ Returns a canonical version of this statement """
        return canonicalize_ac(self)

    @cached_property
    def tree_size(self) -> int:
        """ Returns the size of the tree """
        res = 1

        if self.child_left:
            res += self.child_left.tree_size

        if self.child_right:
            res += self.child_right.tree_size

        return res

    def get_leave_nodes(self) -> List[Statement]:
        """ Returns a list of all the (possilby indirect) leaves nodes """
        if self.is_leave_node:
            return [self]

        child_left_leave_nodes = self.child_left.get_leave_nodes()
        child_right_leave_nodes = self.child_right.get_leave_nodes()

        return child_left_leave_nodes + child_right_leave_nodes

    def get_nodes(self) -> List[Statement]:
        """ Returns a list of all the nodes in the tree """
        if self.child_left:
            left_nodes = self.child_left.get_nodes()
        else:
            left_nodes = []

        if self.child_right:
            right_nodes = self.child_right.get_nodes()
        else:
            right_nodes = []

        return [self] + left_nodes + right_nodes

    def __eq__(self, other: Statement) -> bool:
        """ Strict equality check, going down the expression tree """
        if other is None:
            return False

        if not _eq_node_function(self.node_function, other.node_function):
            return False

        return self.child_right == other.child_right and self.child_left == other.child_left

    def __hash__(self) -> int:
        return hash((hash(self.node_function), hash(self.child_left), hash(self.child_right)))

    def _increasing_meta_mapping(self) -> Statement:
        """ Maps arbitrary metaobjects to increasing globally equal meta objects (so with names 0, 1, 2 etc. ) """
        self_shadow = self.create_shadow()
        mapped_nodes = set()
        name_idx = 0
        replacement_list = []

        # Leave_nodes are ordered in get_leave_nodes methode (from left to right)
        for leave_node in self_shadow.get_leave_nodes():
            if isinstance(leave_node.node_function, MetaObject) and leave_node not in mapped_nodes and leave_node.negation not in mapped_nodes:
                replacement_list.append((leave_node, Statement(replace(leave_node.node_function, name=str(name_idx), negated=False))))
                mapped_nodes.add(leave_node)

                replacement_list.append((leave_node.negation, Statement(replace(leave_node.node_function, name=str(name_idx), negated=True))))
                mapped_nodes.add(leave_node.negation)
                name_idx += 1

        return self_shadow.replace_with_list(replacement_list).canonical

    @cached_property
    def nameless_hash(self) -> int:
        """ Returns the hash of the increasing_meta_mappings object """
        return hash(self._increasing_meta_mapping())

    def meta_nameless_eq(self, other: Statement) -> bool:
        """ Checks if self is equal to the other statement, under mapping metaobjects into central once, such that A => T, B => T are equal in this function """
        return self.nameless_hash == other.nameless_hash

    def primitive_eq(self, other: Statement) -> bool:
        """ Checks for quantative equivalence of two statements """
        if isinstance(other.node_function, MetaObject):
            return other.node_function.obj_type == Statement

        if isinstance(self.node_function, Node) and not _is_of_type(other.node_function, Node):
            return False

        elif isinstance(self.node_function, Bool) and not _is_of_type(other.node_function, Bool):
            return False

        elif isinstance(self.node_function, MetaObject):
            # Special case
            if self.node_function.obj_type == Statement:
                return True

            if not _is_of_type(self.node_function, type(other.node_function)):
                return False
            # If other also is metaobject and has the same name, negation status can't be different
            if isinstance(other.node_function, MetaObject):
                if self.node_function.name == other.node_function.name and not self.node_function.negated == other.node_function.negated:
                    return False

        elif isinstance(self.node_function, Node) and isinstance(other.node_function, Node):
            return self.node_function.primitive_eq(other.node_function)

        elif not self.node_function == other.node_function:
            return False

        return _primitive_eq_child_nodes(self.child_left, other.child_left) and _primitive_eq_child_nodes(
            self.child_right, other.child_right)

    def primitive_contains(self, other: Statement) -> Generator[Statement]:
        """ Checks if given statement is contained within this statement """
        if self.primitive_eq(other):
            yield self

        for res in self.child_left.primitive_contains(other):
            yield res

        for res in other.child_right.primitive_contains(self):
            yield res

    def get_replacement_list(self, other: Statement, allow_bool_val_replacement: int,
                             allow_self_node_size_increase: bool,
                             replacement_list: Union[List[Tuple[Statement, Statement]], None] = None) -> List[
        Union[Tuple[Statement, Statement], Tuple[None, None]]]:
        """ Returns the necessary replacements on this statement to make a step that is only primitvely equal completely equal """
        if replacement_list is None:
            replacement_list = []

        if _eq_node_function(self.node_function, other.node_function):
            if (self.child_left is None) ^ (other.child_left is None) or (self.child_right is None) ^ (
                    other.child_right is None):
                return [(None, None)]

            if self.child_left and other.child_left:
                replacement_list = self.child_left.get_replacement_list(other.child_left, allow_bool_val_replacement,
                                                                        allow_self_node_size_increase, replacement_list)
            if self.child_right and other.child_right:
                replacement_list = self.child_right.get_replacement_list(other.child_right, allow_bool_val_replacement,
                                                                         allow_self_node_size_increase,
                                                                         replacement_list)
        elif self is not other:
            if self.tree_size < other.tree_size:
                if not allow_self_node_size_increase:
                    return [(None, None)]

            # Check if self gets identified with ambiguous
            if other.node_function is Bool.AMBIGUOUS and self.node_function is not Bool.AMBIGUOUS:
                if not allow_self_node_size_increase:
                    return [(None, None)]

            # Check if booleans get identified
            #   -> 0 => no boolean variables are allowed to be replaced with metaobjects
            #   -> 1 => only self metaobjects can be replaced with boolean variables
            #   -> 2 => only other metaobjects can be replaced with boolean variables
            #   -> 3 => boolean variable replacement is allowed
            if isinstance(self.node_function, Bool):
                if allow_bool_val_replacement < 2:
                    return [(None, None)]

            if isinstance(other.node_function, Bool):
                if allow_bool_val_replacement % 2 == 0:
                    return [(None, None)]

            replacement_list.append(_ordered_replacement_tuple(other, self))

            # Also add negation to list
            if isinstance(self.node_function, MetaObject) or isinstance(other.node_function, MetaObject):
                replacement_list.append(_ordered_replacement_tuple(other.negation, self.negation))

        return replacement_list

    def get_replacement_lists_recc(self, other: Statement, allow_bool_val_replacement: int,
                                   allow_self_node_size_increase: bool) -> Generator[List[Tuple[Statement, Statement]]]:
        """ Runs the get_replacement_list function reccursively through tree structure """
        if self.primitive_eq(other):
            yield self.get_replacement_list(other, allow_bool_val_replacement, allow_self_node_size_increase)

        if self.child_left:
            for res in self.child_left.get_replacement_lists_recc(other, allow_bool_val_replacement,
                                                                  allow_self_node_size_increase):
                yield res

        if self.child_right:
            for res in self.child_right.get_replacement_lists_recc(other, allow_bool_val_replacement,
                                                                   allow_self_node_size_increase):
                yield res

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

    def strong_replace_with_list(self, replacement_list: List[Tuple[Statement, Statement]]) -> Statement:
        """ Repeatedly replaces self with given replacement list until can't be replaced further """
        # TODO: Create recursion free version via interpreting replacement list as graph
        tmp = copy.copy(self)
        self_rep = self.replace_with_list(replacement_list)
        while tmp != self_rep:
            tmp = self_rep
            self_rep = self_rep.replace_with_list(replacement_list)

        return self_rep

    def reverse_replace(self, replacement_list: List[Tuple[Statement, Statement]]) -> Statement:
        """
        Reverts the changes that were applied through a replacement list on this statement.
        replacement_list can be the concatenation of multiple replacements.
        Since replacements are not necessarily injective, the result my differ from the original version.
        To make the inverse replacement functional, we define a representative for every input that mapped
        to the same result.
        This function therefore not only reverses the replacement but also reduces the information in a
        statement, collapsing different nodes into the same, if they were mapped to the same node originally.
        """
        reverse_mapping_dict = defaultdict(set)
        for s, t in replacement_list:
            # Skip boolean values, they should not be reverted
            if isinstance(t.node_function, Bool):
                continue

            reverse_mapping_dict[t].add(s)

        # Get unreferenced nodes. They effectively act as root_nodes of the graph representation of the reverse_mappings_dict
        root_nodes = set()
        unpacked_values = set()
        for value in reverse_mapping_dict.values():
            unpacked_values |= value

        for key in reverse_mapping_dict.keys():
            if key not in unpacked_values:
                root_nodes.add(key)

        def traverse(_node, _dictionary):
            """ Gets the leave nodes in dictionary from one given node """
            if _node in _dictionary.keys():
                frontier = _dictionary[_node]

                res = set()
                for f in frontier:
                    res |= traverse(f, _dictionary)
                return res

            else:
                return {_node}

        revert_replacement_list = []  # To reverse to original used nodes and collapse different nodes (mapping to the same output) into one
        finished_root_nodes = set()  # Since we both create the replacement of the root node and its negation to get a continuous representative, we will skip the negation later

        for root_node in root_nodes:
            if root_node in finished_root_nodes:
                continue

            # Get leave nodes from this root node
            leave_nodes = sorted(traverse(root_node, reverse_mapping_dict) | {n.negation for n in
                                                                              traverse(root_node.negation,
                                                                                       reverse_mapping_dict)},
                                 key=lambda x: x.tree_size)

            # Choose representative for all leave nodes
            representative = leave_nodes[0]

            # To original
            revert_replacement_list.append((root_node, representative))
            revert_replacement_list.append((root_node.negation, representative.negation))

            # Collapse (non-injective fix)
            for node in leave_nodes[1:]:
                # Note: Since .negation is a cached property, we don't have to introduce a new variable, and can reference it as a once computed attribute
                revert_replacement_list.append((node, representative))
                revert_replacement_list.append((node.negation, representative.negation))

            finished_root_nodes.add(root_node)
            finished_root_nodes.add(root_node.negation)

        # Reversion
        return self.replace_with_list(revert_replacement_list)

    def _static_simplify(self, match_statement: Statement, simplification: Statement) -> Tuple[Statement, bool]:
        """ Replaces all the parts of self that exactly match the match_statement with simplification """
        if self == match_statement:
            return simplification, True

        if self.child_left is not None:
            new_left, left_changed = self.child_left._static_simplify(match_statement, simplification)
        else:
            new_left, left_changed = self.child_left, False

        if self.child_right is not None:
            new_right, right_changed = self.child_right._static_simplify(match_statement, simplification)
        else:
            new_right, right_changed = self.child_right, False

        return replace(self, child_left=new_left, child_right=new_right), left_changed or right_changed

    def simplify(self, match_statement: Statement, simplification: Statement, allow_bool_val_replacement: int = 0,
                 allow_self_node_size_increase: bool = True) -> Generator[Statement]:
        """
        Checks ats from this node for match_statement structure.
        If inherits match_statement structure, we will replace it
        with the simplification accordingly (under preservation of the replacement list)
        allow_bool_var_replacement:
            -> 0 => no boolean variables are allowed to be replaced with metaobjects
            -> 1 => only self metaobjects can be replaced with boolean variables
            -> 2 => only other metaobjects can be replaced with boolean variables
            -> 3 => boolean variable replacement is allowed
        """
        for res, _ in self.simplify_return_replacement_list(match_statement, simplification, allow_bool_val_replacement,
                                                            allow_self_node_size_increase):
            yield res

    def simplify_return_replacement_list(self, match_statement: Statement, simplification: Statement,
                                         allow_bool_val_replacement: int = 0,
                                         allow_self_node_size_increase: bool = True) -> Generator[
        Tuple[Statement, List[Tuple[Statement, Statement]]]]:
        """ Checks ats from this node for match_statement structure. If inherits match_statement structure, we will replace it with the simplification accordingly (under preservation of the replacement list) """
        for replacement_list in self.get_replacement_lists_recc(match_statement, allow_bool_val_replacement,
                                                                allow_self_node_size_increase):
            replacement_list, valid = _replacement_list_valid(replacement_list)
            if not valid:
                continue

            # Check for boolean replacement
            boolean_assigned_nodes = _get_boolean_assigned_nodes(replacement_list)
            match allow_bool_val_replacement:
                case 0:
                    if boolean_assigned_nodes:
                        continue
                case 1:
                    if any(nodes in boolean_assigned_nodes for nodes in match_statement.get_nodes()):
                        continue
                case 2:
                    if any(nodes in boolean_assigned_nodes for nodes in self.get_nodes()):
                        continue

            new_self = self.replace_with_list(replacement_list)
            new_match = match_statement.replace_with_list(replacement_list)
            new_simplification = simplification.replace_with_list(replacement_list)

            # Replace match_statement with simplification
            result, applied_match_statement = new_self._static_simplify(new_match, new_simplification)
            if applied_match_statement:
                yield result.canonical, replacement_list

    def create_shadow(self) -> Statement:
        """ Returns a shadow version of the statement that removes names from undefined objects and creates shadow objects of them to avoid id-mismatches when they weren't defined properly independent upon creation """
        shadow_replacements: List[Tuple[Statement, Statement]] = []
        shadowed_names = set()

        for leave_node in self.get_leave_nodes():
            shadow = leave_node.create_shadow_node(shadowed_names)

            if shadow:
                shadowed_names.add(leave_node.node_function.name)
                shadow_replacements.append((leave_node, shadow))
                shadow_replacements.append((leave_node.negation, shadow.negation))

        return self.replace_with_list(shadow_replacements)

    def create_shadow_node(self, shadowed_names: set[str]) -> Union[Statement, None]:
        """ Only create the shadow version on the current node function """
        if isinstance(self.node_function, MetaObject):
            meta_name = self.node_function.name
            if meta_name in shadowed_names:
                return

            shadowed_names.add(meta_name)
            shadow_meta = self.node_function.create_shadow()
            return Statement(shadow_meta)


@dataclass(frozen=True, eq=False)
class MetaObject:
    """ Represents a placeholder for any object of given type """
    obj_type: type
    name: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    negated: bool = False

    def is_of_type(self, target_type: type) -> bool:
        return issubclass(self.obj_type, target_type)

    def create_shadow(self) -> MetaObject:
        """ Returns a shadow version of the metaobject that removes names from undefined objects and creates shadow objects of them to avoid id-mismatches when they weren't defined properly independent upon creation """
        return MetaObject(self.obj_type, negated=self.negated)

    @cached_property
    def negation(self) -> MetaObject:
        return MetaObject(self.obj_type, self.name, negated=(not self.negated))

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.obj_type == other.obj_type and self.negated == other.negated

    def __hash__(self):
        return hash((self.obj_type, self.name, self.negated))

    def __str__(self):
        if self.negated:
            return f'¬{self.name}'
        return self.name


"""
PRIVATE PRECEDENCE TUPLE LIST (TOP TO BOTTOM)
LogicalOperation > Relation > Function > Set > MetaObjects(Statement) > Bool
"""
_precedence = [
    [LogicalOperation.AND,
     LogicalOperation.OR,
     LogicalOperation.EQUAL,
     LogicalOperation.NEQUAL],

    [Relation.SUBSET,
     Relation.SUBSETQ,
     Relation.SUPPERSET,
     Relation.SUPPERSETQ,
     Relation.LE,
     Relation.LEQ,
     Relation.GE,
     Relation.GEQ,
     Relation.EQUAL,
     Relation.NEQUAL],

    [],  # Functions
    [],  # Sets
    [],  # MetaObjects

    [Bool.TRUE,
     Bool.FALSE]
]
_precedence_type_ordering: List[type] = [LogicalOperation, Relation, Function, Set, MetaObject, Bool]


def add_precedence(obj: Union[LogicalOperation, Relation, Function, Set, MetaObject, Bool]):
    try:
        idx = _precedence_type_ordering.index(type(obj))
    except Exception:
        raise Exception(f'Unexpected type {type(obj)}')

    if obj in _precedence[idx]:
        return

    _precedence[idx].append(obj)


def get_precedence(obj: Union[LogicalOperation, Relation, Function, Set, MetaObject, Bool]) -> int:
    try:
        precedence_idx = _precedence_type_ordering.index(type(obj))
        precedence = 0
        for i in range(precedence_idx):
            precedence += len(_precedence[i])
    except Exception:
        raise Exception(f'Unexpected type {type(obj)}')

    try:
        return -(precedence + _precedence[precedence_idx].index(obj))
    except ValueError:
        raise ValueError(f"Didn't add {obj} to precedence")


# AC-CANONIZATION FOR OPERATIONS PROPERTIES
def canonicalize_ac(statement: Statement) -> Statement:
    """
    Canonizes a statement using its node_functions properties given in operation_properties.
    Resolves into four cases:
    1. (neither commutative nor associative): return Statement
    2. (commutative but not associative): swap child-order after KBO
    3. (associative but not commutative): get flattened arguments and set brackets normalized
    4. (associative and commutative): get flattened, sorted arguments and set brackets normalized
    """
    if statement.is_leave_node:
        return statement

    left = canonicalize_ac(statement.child_left)
    right = canonicalize_ac(statement.child_right)

    if statement.node_function not in OPERATION_PROPERTIES:
        return replace(statement, child_left=left, child_right=right)

    # Commutativity only
    properties = OPERATION_PROPERTIES[statement.node_function]
    if properties.commutative and not properties.associative:
        if kbo_compare(statement.child_left, statement.child_right) == 1:
            return replace(statement, child_left=right, child_right=left)
        return replace(statement, child_left=left, child_right=right)

    # Operator is associative
    flattened_statements = flatten(statement)

    if properties.commutative:
        # Sorts after kbo comparison
        n = len(flattened_statements)
        for i in range(n):
            for j in range(0, n - i - 1):
                if kbo_compare(flattened_statements[j + 1], flattened_statements[j]) == -1:
                    flattened_statements[j], flattened_statements[j + 1] = flattened_statements[j + 1], flattened_statements[j]

    return rebuild(statement.node_function, flattened_statements)


def generate_ac_invariants(statement: Statement) -> Generator[Statement]:
    """ Returns all the invariants of a statement that when canonicalized give the original statement """
    statement = statement.canonical

    if statement.is_leave_node or statement.node_function not in OPERATION_PROPERTIES.keys():
        yield statement
        return

    property_entry = OPERATION_PROPERTIES[statement.node_function]

    invariants_left = list(generate_ac_invariants(statement.child_left))
    invariants_right = list(generate_ac_invariants(statement.child_right))

    if not property_entry.associative:

        for left in invariants_left:
            for right in invariants_right:
                yield replace(statement, child_left=left, child_right=right)

                if property_entry.commutative:
                    yield replace(statement, child_left=right, child_right=left)
        return
    
    # Associative
    def parenthesize_invariants(root_node, args: List[Statement]):
        """ Creates all parenthesize-form for given flattens args list"""
        if len(args) == 1:
            yield args[0]
            return

        # Include increasing split on left or right side, then use function recursively
        # E.g. (a, b, c, d, e) we set the split at 2 => (a, b | c, d, e), so left uses a, b and right c, d, e
        for split in range(1, len(args)):
            for left_invariant in parenthesize_invariants(root_node, args[:split]):
                for right_invariant in parenthesize_invariants(root_node, args[split:]):
                    yield replace(root_node, child_left=left_invariant, child_right=right_invariant)

    arguments = flatten(statement)
    argument_invariants = [list(generate_ac_invariants(arg)) for arg in arguments]

    # Generate all combinations (cartesian product) of all individual argument_invariants using itertools' product function
    for argument_combination in product(*argument_invariants):
        orderings = permutations(argument_combination) if property_entry.commutative else [argument_combination]

        for ordering in orderings:
            for parenthesized_statement in parenthesize_invariants(statement, list(ordering)):
                yield parenthesized_statement


def flatten(statement: Statement) -> List[Statement]:
    """ Returns a flattened list of statement arguments that have the specific node_function """
    terms = []

    def collect(sub_statement: Statement):
        if sub_statement.node_function == statement.node_function:
            if sub_statement.child_left: collect(sub_statement.child_left)
            if sub_statement.child_right: collect(sub_statement.child_right)
        else:
            terms.append(sub_statement.canonical)

    collect(statement.child_left)
    collect(statement.child_right)

    return terms


def rebuild(common_operation, statement_list: List[Statement]) -> Statement:
    """ Rebuilds into a binary statement tree given statement list using right-associativity """
    if len(statement_list) == 1:
        return statement_list[0]

    root_statement = statement_list[-1]

    for statement in statement_list[:-1]:
        root_statement = Statement(common_operation, statement, root_statement)

    return root_statement


# KBO
def kbo_compare(lhs: Statement, rhs: Statement):
    """ Returns 1 if lhs has higher kbo weight. If rhs has higher returns -1. 0 otherwise"""
    if lhs is rhs:
        return 0

    if lhs.kbo_weight != rhs.kbo_weight:
        return 1 if lhs.kbo_weight > rhs.kbo_weight else -1

    if lhs.kbo_precedence != rhs.kbo_precedence:
        return 1 if lhs.kbo_precedence > rhs.kbo_precedence else -1

    if lhs.child_left and rhs.child_left:
        child_compare = kbo_compare(lhs.child_left, rhs.child_left)
        if child_compare != 0:
            return child_compare

    if lhs.child_right and rhs.child_right:
        return kbo_compare(lhs.child_right, rhs.child_right)

    return 0


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


def _eq_node_function(node_function1: Union[LogicalOperation, Relation, Node, Bool, MetaObject],
                      node_function2: Union[LogicalOperation, Relation, Node, Bool, MetaObject]) -> bool:
    if isinstance(node_function1, Node):
        if not isinstance(node_function2, Node):
            return False
        return node_function1 == node_function2

    if isinstance(node_function1, MetaObject):
        if not isinstance(node_function2, MetaObject):
            return False
        return node_function1 == node_function2

    if not node_function1 == node_function2:
        return False

    return True


def _ordered_replacement_tuple(obj1: Statement, obj2: Statement) -> Union[
    Tuple[None, None], Tuple[Statement, Statement]]:
    """ Orders the objects such that a replacement is valid in a sense, where we don't generalize (A statements that holds if f(x)=1 can't be replaced with A, but vise versa) """
    if isinstance(obj2.node_function, MetaObject):
        # The other can neither use the statement nor negation in its expression
        obj1_leave_nodes_unpacked = [n.node_function for n in obj1.get_leave_nodes()]
        if obj2.node_function in obj1_leave_nodes_unpacked or obj2.node_function.negation in obj1_leave_nodes_unpacked:
            # Invalid repalcement
            return None, None

        return obj2, obj1

    if isinstance(obj1.node_function, MetaObject):
        obj2_leave_nodes_unpacked = [n.node_function for n in obj2.get_leave_nodes()]
        if obj1.node_function in obj2_leave_nodes_unpacked or obj1.node_function.negation in obj2_leave_nodes_unpacked:
            # Invalid repalcement
            return None, None

        return obj1, obj2

    if not isinstance(obj1.node_function, Node) or not isinstance(obj2.node_function, Node):
        return None, None

    uneq_expr1, uneq_expr2, _ = get_unequal_parts_cmr_reduced(obj1.node_function, obj2.node_function, eq)
    if uneq_expr1.argument_slots and uneq_expr2.argument_slots:
        return None, None

    if uneq_expr1.node_object.binding_quantity != uneq_expr2.node_object.binding_quantity:
        return None, None

    if not uneq_expr1.argument_slots:
        # expr2 is some kind of application
        return obj1, obj2

    return obj2, obj1


def _replacement_list_valid(replacement_lst: List[Tuple[Statement, Statement]]) -> \
        Tuple[List[Tuple[Statement, Statement]], bool]:
    """ Checks if any key is used twice with different values. On already seen replacements (A, B) & (A, C), try to find replacement (B, C) or (C, B) """
    # TODO: Can we update to only hasha search to increase runtime from O(n^2) to O(n)?
    updated_lst = []
    updated_lst_hash_pairings = set()

    def add_to_updated(_key, _value):
        if (hash(_key), hash(_value)) in updated_lst_hash_pairings:
            return
        updated_lst.append((_key, _value))
        updated_lst_hash_pairings.add((hash(_key), hash(_value)))

    for key, value in replacement_lst:
        if not key or not value:
            return [], False

        for old_key, old_value in updated_lst:
            # Special-case: Can't substitute A with something and at the same time the logical negation that is unequal
            if isinstance(key.node_function, MetaObject) and isinstance(old_key.node_function, MetaObject):
                key_node_function = key.node_function
                old_key_node_function = old_key.node_function
                if key_node_function == old_key_node_function.negation:
                    if value == old_value.negation:
                        continue

                    # Try to do another substitution A->B, not A->C (B!=not C), but B->not C (possible) => A->not C, not A -> C, B->not C
                    value_replacement = _ordered_replacement_tuple(value, old_value.negation)
                    if value_replacement[0] is None or value_replacement[1] is None:
                        return [], False

                    # Update new replacement
                    if hash(value_replacement[0]) == hash(value):
                        if (hash(key), hash(value)) in updated_lst_hash_pairings: updated_lst.remove((key, value))
                        add_to_updated(key, value_replacement[1])  # A->not C (new)
                        add_to_updated(*value_replacement)  # B->not C (new)
                        add_to_updated(old_key, old_value)  # not A->C

                    # Redo check in the other ordering
                    value_replacement = _ordered_replacement_tuple(value.negation, old_value)
                    if value_replacement[0] is None or value_replacement[1] is None:
                        return [], False

                    if hash(value_replacement[0]) == hash(old_value):
                        if (hash(old_key), hash(old_value)) in updated_lst_hash_pairings: updated_lst.remove(
                            (old_key, old_value))
                        add_to_updated(old_value, value_replacement[1])
                        add_to_updated(*value_replacement)
                        add_to_updated(key, value)

                    return [], False

            if key == old_key:
                if value == old_value:
                    continue

                # Again try to resolve issue A->B, A->C (B!=C), but B->C (possible) => A->C, B->C
                value_replacement = _ordered_replacement_tuple(value, old_value)
                if value_replacement == (None, None):
                    return [], False

                # Update with new replacement
                add_to_updated(*value_replacement)
                if hash(value_replacement[0]) == hash(value):
                    if (hash(key), hash(value)) in updated_lst_hash_pairings: updated_lst.remove((key, value))
                    add_to_updated(old_key, old_value)
                else:
                    if (hash(old_key), hash(old_value)) in updated_lst_hash_pairings: updated_lst.remove(
                        (old_key, old_value))
                    add_to_updated(key, value)

        add_to_updated(key, value)

    # Find conflicts
    resolved_state = False

    while not resolved_state:
        replacement_dict = {key: value for key, value in updated_lst}
        replacement_lst_resolved = []
        resolved_state = True

        for key, value in updated_lst:
            conflict_solution_replacement = []
            if any(hash(key) == hash(node) for node in value.get_leave_nodes()):
                return [], False

            for node in value.get_leave_nodes():

                if node in replacement_dict.keys():
                    resolved_state = False
                    node_updated = replacement_dict[node]
                    conflict_solution_replacement.append((node, node_updated))

            replacement_lst_resolved.append((key, value.replace_with_list(conflict_solution_replacement)))
        updated_lst = replacement_lst_resolved

    return updated_lst, True


def _get_boolean_assigned_nodes(replacement_lst: List[Tuple[Statement, Statement]]) -> List[Statement]:
    """ Returns all the nodes that got identified with a boolean value directly or indirectly (e.g. A->B, B->T) => [A, B] """
    projected_bijective_reversed_replacement = {}
    for s, t in replacement_lst:
        if isinstance(t.node_function, Bool):
            continue

        if t not in projected_bijective_reversed_replacement.keys():
            projected_bijective_reversed_replacement[t] = {s}
        else:
            projected_bijective_reversed_replacement[t].add(s)

    boolean_assigned = {s for s, t in replacement_lst if isinstance(t.node_function, Bool)}
    added_boolean = boolean_assigned.copy()

    while added_boolean:
        added_boolean = {s for s_bool in added_boolean for s, t in
                         projected_bijective_reversed_replacement.get(s_bool, [])} - boolean_assigned

        boolean_assigned |= added_boolean

    return list(boolean_assigned)


def create_shadow_version(*statements: Statement) -> Tuple[Statement, ...]:
    """
    Creates a shadow version of multiple statements at once,
    where all the statements are replaced with the same scoped-shadow variable,
    e.g. A & B; A | B, we will replace A with the same new metaobject
    """
    replacement_list: List[Tuple[Statement, Statement]]

    shadow_replacements: List[Tuple[Statement, Statement]] = []
    shadowed_names = set()

    for statement in statements:
        for leave_node in statement.get_leave_nodes():
            shadow = leave_node.create_shadow_node(shadowed_names)

            if shadow:
                shadowed_names.add(leave_node.node_function.name)
                shadow_replacements.append((leave_node, shadow))
                shadow_replacements.append((leave_node.negation, shadow.negation))

    return tuple(statement.replace_with_list(shadow_replacements) for statement in statements)


# Negation axioms
negation_axioms: Dict[LogicalOperation, Tuple[Statement, Statement]] = {}
P = Statement(MetaObject(Statement, name='P'))
Q = Statement(MetaObject(Statement, name='Q'))

# not (P & Q) = (not P xor not Q) xor (not P and not Q)
lhs = Statement(LogicalOperation.AND, P, Q)
rhs = Statement(LogicalOperation.XOR,
                Statement(LogicalOperation.XOR, P.negation, Q.negation),
                Statement(LogicalOperation.AND, P.negation, Q.negation))
negation_axioms[LogicalOperation.AND] = (lhs, rhs)

# not (P xor Q) = (P and Q) xor (not P and not Q)
lhs = Statement(LogicalOperation.XOR, P, Q)
rhs = Statement(LogicalOperation.XOR,
                Statement(LogicalOperation.AND, P, Q),
                Statement(LogicalOperation.AND, P.negation, Q.negation))
negation_axioms[LogicalOperation.XOR] = (lhs, rhs)
