from __future__ import annotations
import math
from collections import deque
from functools import cached_property
from dataclasses import dataclass, field, replace
from MObject import Object, Set, Function, Quantor
from typing import Tuple, Dict, List, Generator, Union, NamedTuple, Callable
from Definitions import definitions, operations


@dataclass(frozen=True)
class Edge:
    """
    One directed edge in expression graph
    """
    to_node: Node
    weight: Union[int, float, Node]
    parent_node: Node

    def __eq__(self, other: Edge):
        """ Compare weights. Only compare memory values of to_node and parent_node to avoid reccursion errors on cyclical graphs """
        return self.weight == other.weight and self.to_node is other.to_node and self.parent_node is other.parent_node

    def check_validity(self) -> bool:
        """
        Checks validity of edge by checking if weight is int, infinite, or the node's object's binding status is a natural number.
        If an edge's weight is not 1, it must be a cyclical definition in the graph as it will not be addressed multiple times
        """
        if self.weight != 1:
            if not self.cyclical:
                return False
        if isinstance(self.weight, int):
            return True
        if isinstance(self.weight, float):
            return self.weight == float("inf")
        if isinstance(self.weight, Node):
            node_object = self.weight.node_object
            if len(node_object.binding_quantity) != 1:
                return False
            # TODO: Check that node_object really is variable (wait for object's refactor)
            return node_object.binding_quantity[0] == definitions['integers']
        return False

    # Cyclical check
    @cached_property
    def _cyclical_information(self) -> Tuple[bool, int]:
        """
        Checks if an edge is cyclical, reccursively.
        An edge is cyclical if at some point it to_node's nodes are the same as the one from the argument slot
        The cylce length is the exact number of applications done to return to the original node
        """
        visited = set()
        parent_hash = id(self.parent_node)
        nodes_queue = deque([(self.to_node, 0)])
        while nodes_queue:
            node, cycle_length = nodes_queue.popleft()
            for argument_slot in node.argument_slots:
                sub_cycle_length = 1
                for edge in argument_slot.edge_sequence:
                    child_node = edge.to_node
                    hash_val = id(child_node)
                    new_cycle_length = _add_values(cycle_length, sub_cycle_length)
                    if hash_val == parent_hash:
                        return True, new_cycle_length
                    if hash_val in visited:
                        continue
                    visited.add(hash_val)
                    nodes_queue.append((child_node, new_cycle_length))
                    # Add the cycle length of the edge to the sub_cycle_length to increase cylce_length of next edges to account for
                    sub_cycle_length = _add_values(sub_cycle_length, _mul_values(edge.cycle_length, edge.weight))
        return False, 0

    @cached_property
    def cyclical(self) -> bool:
        return self._cyclical_information[0]

    @cached_property
    def cycle_length(self) -> int:
        return self._cyclical_information[1]



@dataclass(frozen=True, eq=False)
class ArgumentSlot:
    """
    Sequence of edges
    """
    edge_sequence: Tuple[Edge, ...]
    parent_node: Node
    desired_output: Object

    @cached_property
    def output_object(self) -> Object:
        """ The reccursive output of the last (or in sequence first) edge as an object """
        obj = self.edge_sequence[0].to_node.node_object
        if isinstance(obj, Set):
            return replace(obj, nested_depth=self.nested_depth)
        return obj

    @cached_property
    def number_of_applications(self) -> Union[int, float, Node]:
        """ Returns the sum of all edges' cycle lengths """
        return sum(edge.cycle_length for edge in self.edge_sequence)

    @cached_property
    def nested_depth(self) -> int:
        """ Returns the itteratively calculated nested depth of the argument chain """
        child_node = self.edge_sequence[-1].to_node.node_object
        if isinstance(child_node, Set):
            nested_depth = child_node.nested_depth
            for edge in self.edge_sequence[::-1][:-1]:
                difference = nested_depth - edge.to_node.math_object.binding_quantity[0].nested_depth
                if difference < 0:
                    raise Exception(f"Nested depth doesn't suffice for functions input {edge.to_node.math_object}")
                nested_depth = edge.to_node.math_object.binding_quantity[1].nested_depth + difference
            return nested_depth
        return 1

    @property
    def quantor(self) -> Quantor:
        return Quantor.EXISTS if any(edge.to_node.node_object.quantor == Quantor.EXISTS or edge.to_node.node_object.quantor == Quantor.DEFINE for edge in self.edge_sequence) else Quantor.FORALL

    @classmethod
    def create(cls, edge_sequence: Union[List[Edge], Tuple[Edge, ...]], parent_node: Node, desired_output: Object) -> ArgumentSlot:
        return cls(cls._simplify(edge_sequence, parent_node), parent_node, desired_output)

    def compare(self, other: ArgumentSlot, comparison_function: Callable) -> bool:
        """ General comparison function for given comparator (such as == or id_less_equal) """
        # Primitve filtering
        if self is other:
            return True
        if self.number_of_applications != other.number_of_applications:
            return False

        # Direct check
        if not self.edge_sequence and not other.edge_sequence:
            return True
        if (self.edge_sequence and not other.edge_sequence) or (not self.edge_sequence and other.edge_sequence):
            return False

        # Cylic modulo reduction
        state_self = CycleState(edge_sequence=list(self.edge_sequence))
        state_other = CycleState(edge_sequence=list(other.edge_sequence))

        return _boolean_cmr(state_self, state_other, comparison_function)

    def __eq__(self, other: ArgumentSlot):
        """ Strict equality check of every edge in argument sequence """
        return self.compare(other, eq)

    def id_less_equal(self, other: ArgumentSlot):
        """ Strict equality check of every edge in argument sequence but without regarding objects id """
        return self.compare(other, id_less_eq)

    def check_validity(self) -> bool:
        """ Checks if edges are valid and if all sequence's edge's nodes output desired object """
        cyclical_flag = True
        number_of_edges = len(self.edge_sequence)
        for i, edge in enumerate(self.edge_sequence):
            if i < number_of_edges - 1:
                if not isinstance(edge.to_node.math_object, Function):
                    return False

            # If the last edge wasn't cyclical, we can't have new edges going out from this node as it is never reached again
            if not cyclical_flag:
                return False
            if not edge.cyclical:
                cyclical_flag = False

            if not edge.check_validity():
                return False
            if edge.to_node.node_object != self.desired_output:
                return False
        return True

    def get_pointed_nodes(self) -> Tuple[Node, ...]:
        return tuple(edge.to_node for edge in self.edge_sequence)

    @staticmethod
    def _simplify(edge_sequence: Union[List[Edge], Tuple[Edge, ...]], parent_node: Node) -> Tuple[Edge, ...]:
        """ Combines edges that point to the same node to formalize and canonize """
        new_edge_sequence = []
        i = -1
        while (i := i + 1) < len(edge_sequence):
            new_node = edge_sequence[i].to_node
            new_weight = edge_sequence[i].weight

            while i < len(edge_sequence) and (next_edge := edge_sequence[i + 1]).to_node is new_node:
                new_weight = _add_values(new_weight, next_edge.weight)
                i += 1
            new_edge_sequence.append(Edge(to_node=new_node, weight=new_weight, parent_node=parent_node))

        return tuple(new_edge_sequence)


class CycleState(NamedTuple):
    """ Capsule one state of a graph for one cycle on CMR-algorithm """
    edge_sequence: List[Edge]
    full_cycle_length: int | None = None
    idx: int = 0
    shift: int = 0

@dataclass(frozen=True, eq=False)
class Node:
    """
    One node in the expression graph. Contains its argument slots
    """
    math_object: Object
    argument_slots: Tuple[ArgumentSlot, ...] = field(default_factory=tuple)

    @cached_property
    def node_object(self):
        """ Recursively build up the node tuple using the function at the node """
        if not self.argument_slots:
            return self.math_object

        quantor = Quantor.EXISTS if any(
            argument_slots.quantor == Quantor.EXISTS or argument_slots.quantor == Quantor.DEFINE for argument_slots in
            self.argument_slots) else Quantor.FORALL
        standart_output = _get_object_instance_of_functions_standart_output(self.math_object)

        # Get the output type by checking if any input is set instead of variable if variable was given. E.g., f(X) will be a set, but the output of x was normally defined as output variables.
        difference = _get_nested_depth_difference(self, self.math_object.binding_quantity[0])

        standart_output.__setattr__("obj_id", None)
        if isinstance(standart_output, Set):
            return replace(standart_output, nested_depth=standart_output.nested_depth + difference, quantor=quantor)
        return replace(standart_output, quantor=quantor)

    def check_validity(self) -> bool:
        """ If node has argument slots checks if math_object is of type function """
        if self.argument_slots:
            if not isinstance(self.math_object, Function):
                return False
            if len(self.argument_slots) == len(self.math_object.binding_quantity):
                return False
        return True

    def __call__(self, *args) -> Node:
        """
        Makes node creation easier for user.
        When calling on a node with arguments, given objects are automatically input into argument slots.
        """
        if not isinstance(self.math_object, Function):
            raise TypeError("Node's math_object must be of type function to be called")
        if len(args) != len(self.math_object.binding_quantity):
            raise TypeError(f"{self.math_object} must be given exacltly {self.math_object.binding_quantity} arguments")
        new_argument_slots = []
        for i, arg, binding in enumerate(zip(args, self.math_object.binding_quantity)):
            if isinstance(arg, Object):
                # If arg is an object, we add it as a direct new node argument of the function
                if arg != binding:
                    raise TypeError(f"{self.math_object} must be given object of type {binding} at position {i}")
                arg_slot = ArgumentSlot(edge_sequence=(Edge(to_node=Node(arg), weight=1, parent_node=self), ), parent_node=self, desired_output=binding)
                new_argument_slots.append(arg_slot)
            if isinstance(arg, Node):
                # If arg is a node, we add it as a direct argument of the function
                if arg.math_object != binding:
                    raise TypeError(f"{self.math_object} must be given object of type {binding} at position {i}")
                arg_slot = ArgumentSlot(edge_sequence=(Edge(to_node=arg, weight=1, parent_node=self), ), parent_node=self, desired_output=binding)
                new_argument_slots.append(arg_slot)
            # TODO: implement other input types for node creation
            raise NotImplementedError("Other inputs for functions aren't yet implemented")
        return Node(self.math_object, argument_slots=tuple(new_argument_slots))

    def __str__(self) -> str:
        """ Recursively prints the node and its children in a tree structure """
        if self.argument_slots:
            res = f'{self.math_object}('
            for arg_slot in self.argument_slots:
                if any(edge.cyclical for edge in arg_slot.edge_sequence):
                    # TODO: implement __str__ function for cyclical edges
                    raise NotImplementedError("__str__ function for cyclical edge containing slots isn't yet implemented")
                res += str(arg_slot.edge_sequence[0].to_node) + ', '
            return res[:-2] + ')'
        return f'{self.math_object}'

    def __hash__(self):
        return hash(tuple([hash(self.math_object)] + [hash(arg_slot) for arg_slot in self.argument_slots]))

    def compare(self, other: Node, comparison_function: Callable) -> bool:
        """ General comparison function for given comparator (such as == or id_less_equal) """
        if self is other:
            return True
        if self.math_object != other.math_object:
            return False
        if len(self.argument_slots) != len(other.argument_slots):
            return False
        for self_slot, other_slot in zip(self.argument_slots, other.argument_slots):
            if not comparison_function(self_slot, other_slot):
                return False
        return True

    def __eq__(self, other: Node) -> bool:
        """ Strict equality check in every single attribute """
        return self.compare(other, eq)

    def id_less_eq(self, other: Node) -> bool:
        """ Checks if the other node is exactly the same as self, but without checking for ids """
        return self.compare(other, id_less_eq)

    def primitive_eq(self, other: Node, print_trace: bool = False):
        """ Runs primitive equal check between two nodes. They are equal if type and binding quantity are the same """
        if print_trace: print(f"Checking {self} == {other}")
        if self is other:
            return True

        self_obj = self.node_object
        other_obj = other.node_object
        if type(self_obj) is not type(other_obj):
            if print_trace: print(f"False: Type didn't match: {type(self_obj)} & {type(other_obj)}")
            return False

        # Two applications (thus obj_id = -1) can only equal if their functions are equal and child_nodes are primitively equal
        if self_obj.obj_id == other_obj.obj_id == -1:
            if self.math_object == other.math_object:
                if len(self.argument_slots) != len(other.argument_slots):
                    return False
                for self_argument_slot, other_argument_slot in zip(self.argument_slots, other.argument_slots):
                    self_argument_slot_output_object = self_argument_slot.output_object
                    other_argument_slot_output_object = other_argument_slot.output_object

                    if type(self_argument_slot_output_object) is not type(other_argument_slot_output_object):
                        if print_trace: print(f"False: Argumentchains output types unequal {type(self_argument_slot_output_object)} & {type(other_argument_slot_output_object)}")
                        return False
                    if self_argument_slot_output_object.binding_quantity != other_argument_slot_output_object.binding_quantity:
                        if print_trace: print(f"False: Argumentchains' binding_quantity unequal {self_argument_slot_output_object} & {other_argument_slot_output_object}")
                        return False
                    if isinstance(self_argument_slot_output_object, Set) and isinstance(other_argument_slot_output_object, Set):
                        if self_argument_slot_output_object.nested_depth != other_argument_slot_output_object.nested_depth:
                            if print_trace: print(f"False: Nested depth of argumentchains is unequal {self_argument_slot_output_object} & {other_argument_slot_output_object}")
                            return False

                if print_trace: print("True: All argument_chains and functions are equal")
                return True
            if print_trace: print("False: Different functions")
            return False

        # Special case: Obj_ids
        if self_obj.obj_id != -1 and other_obj.obj_id != -1:
            if self_obj.binding_quantity == other_obj.binding_quantity and (self_obj.quantor == Quantor.FORALL or other_obj.quantor == Quantor.FORALL):
                if print_trace: print(f"True: Node object's type and binding status equal. Since both are for all over same domain, the objects are the same {self} == {other}")
                return True
            if self_obj.obj_id != other_obj.obj_id:
                if print_trace: print(f"False: Object ids are not -1 but differ: {self_obj.obj_id} & {other_obj.obj_id}")
                return False

        # Direct primitve comparison
        if self_obj.binding_quantity != other_obj.binding_quantity:
            return False
        if isinstance(self_obj, Set) and isinstance(other_obj, Set):
            if self_obj.nested_depth != other_obj.nested_depth:
                return False

        if print_trace: print(f"True: Node object's type {'and object ids are' if self_obj.obj_id == -1 or other_obj.obj_id == -1 else 'is'} equal")
        return True

    def primitive_contains(self, other: Node, visited: set = None, print_trace: bool = False) -> Generator[Tuple[Node, Union[Node, None]]]:
        """
        Runs primitive recursive check on tree structure to yield possible equal nodes as well as parent nodes.
        Reccursively checks for all from root_node reachable nodes if they are primitvely_equal to the other node.
        """
        if print_trace: print(f"Checking {other} contains {self}")
        if not visited:
            visited = set()
        if id(self) in visited:
            return

        visited.add(id(self))
        if self.primitive_eq(other, print_trace):
            if print_trace: print(f"{self} == {other}")
            yield self, None

        # Generate all possible sub_graphs going on from this
        for argument_slot in self.argument_slots:
            for edge in argument_slot.edge_sequence:
                new_node = edge.to_node

                for res, parent in new_node.primitive_contains(other, visited, print_trace):
                    yield res, parent

        if print_trace: print("Contains check done")


    def get_mappings_dict_for_replacement(self, other: Node, mapping: Dict[Node, Node] = None, print_trace: bool = False) -> Tuple[Dict[Node, Node], bool]:
        """ Recursively checks what nodes had to be replaced to make self, the other node """
        if not mapping:
            mapping = {}
        self_math_object = self.math_object
        other_math_object = self.math_object

        # LEAVE-NODES
        if not self.argument_slots:
            # Self is a leave-node, hence other must also be leave-node with the same math_object for possible mapping
            if other.argument_slots:
                return mapping, False
            if self_math_object == other_math_object and other_math_object.quantor == Quantor.FORALL:
                mapping[self] = other

        if not other.argument_slots:
            # Other is leave-node. It's math_object must be the same as self's node object
            if self.node_object == other_math_object and other_math_object.quantor == Quantor.FORALL:
                mapping[self] = other

        # SIMPLE EQUALITY CHECKS
        if self_math_object != other_math_object:
            if print_trace: print(f"Can't map {self} - {other} because {self.math_object} != {other.math_object}")
            return mapping, False
        if len(self.argument_slots) != len(other.argument_slots):
            if print_trace: print(
                f"Can't map, because child chains don't match: {len(self.argument_slots)} & {len(other.argument_slots)}")
            return mapping, False

        # CMR until either equal or leave-node
        for self_argument_slot, other_argument_slot in zip(self.argument_slots, other.argument_slots):
            state_self = CycleState(edge_sequence=list(self_argument_slot.edge_sequence))
            state_other = CycleState(edge_sequence=list(other_argument_slot.edge_sequence))

            self_reduced, other_reduced, valid_cmr = cmr(state_self, state_other, eq)
            if valid_cmr:
                mapping, valid = self_reduced.get_mappings_dict_for_replacement(other_reduced, mapping, print_trace)
                if not valid:
                    return mapping, False
            else:
                if self_reduced and other_reduced:
                    mapping[self_reduced] = other_reduced

        return mapping, True

    def remap_objects(self, mapping: Dict[Node, Node], memo: Dict[Node, Node] = None) -> Node:
        """ Rebuilds ExpressionTree by replacing nodes with mapping nodes. Use memo parameter to stop rebuilding the same nodes multiple times """
        if memo is None:
            memo = {}

        if self in mapping:
            return mapping[self]
        if self in memo:
            return memo[self]

        new_argument_slots = []
        for argument_slot in self.argument_slots:
            new_edge_sequence = []
            for edge, weight in argument_slot.edge_sequence:
                new_node = edge.to_node.remap_objects(mapping, memo)
                new_edge_sequence.append(Edge(new_node, weight, argument_slot.parent_node))
            new_argument_slots.append(replace(argument_slot, edge_sequence=tuple(new_edge_sequence)))

        new_node = Node(math_object=self.math_object, argument_slots=tuple(new_argument_slots))

        memo[self] = new_node
        return new_node


# UNION OF DIFFERENT OBJECT FUNCTIONS
def eq(obj, other):
    if isinstance(obj, Edge) or isinstance(obj, ArgumentSlot) or isinstance(obj, Node) or isinstance(obj, Object):
        return obj == other
    raise Exception(f"Can not compare {obj} and {other}, '=' isn't defined for {type(obj)}")

def id_less_eq(obj, other):
    if isinstance(obj, ArgumentSlot) or isinstance(obj, Node):
        return obj.id_less_equal(other)
    raise Exception(f"Can not compare {obj} and {other}, id_less_equal is not defined for {type(obj)}")

# HELPER FUNCTIONS FOR NODE OBJECT CREATION
def _get_object_instance_of_functions_standart_output(obj: Object) -> Object:
    """ Returns an instance of an element in the functions standart output """
    if isinstance(obj, Function):
        image_set = obj.binding_quantity[1]
        if isinstance(image_set, Set):
            if image_set.nested_depth == 0:
                raise Exception("Can't map onto one variable")
            return replace(image_set, nested_depth=image_set.nested_depth - 1)
        else:
            raise Exception(f"Unmappable type {type(image_set)}")
    raise Exception(f"Can only give instance for function-type arguments")

def _get_nested_depth_difference(node: Node, expected: Object) -> int:
    """ Given one expected object calculates by how much expected objects nested_depht must be changed if any node's input slots leaf values is of higher nested_depth """
    depth_difference = 0
    if isinstance(expected, Set):
        if expected.nested_depth == 0:
            raise Exception("Can't map from one variable")
        if len(node.argument_slots) != len(expected.binding_quantity):
            raise Exception(f"Functions argument slots don't match the inputs binding_quantity. Given {len(node.argument_slots)} arguments, but accepts {len(expected.binding_quantity)}")
        for argument_slot, binding_set in zip(node.argument_slots, expected.binding_quantity):
            if argument_slot.nested_depth < binding_set.nested_depth:
                raise Exception(f"Input is of to low nested_depth {argument_slot.nested_depth} to {binding_set.nested_depth}")
            depth_difference = max(depth_difference, binding_set.nested_depth - argument_slot.nested_depth)
        return depth_difference
    raise Exception(f"Function can't map from non-set. Given type: {type(node)}")



def _get_cycle_nodes(start_node: Node, desired_length: int = -1) -> List[Node]:
    """ Returns the list of nodes that lead to the cycle as parents """
    # Use simple BFS. TODO: Upgrade to bidirectional BFS for efficiency
    # TODO: Issue what if two different paths of same lenght lead to start_node; need to return multiple paths
    queue = deque([(start_node, 0)])
    parent_nodes: Dict[Node, Union[None, Node]] = {start_node: None}
    visited = {id(start_node)}

    while queue:
        node, cycle_length = queue.popleft()

        if node is start_node:
            if cycle_length == desired_length or desired_length == -1:
                path = []
                while node:
                    path.append(node)
                    node = parent_nodes[node]
                return path

        for argument_slot in node.argument_slots:
            sub_cycle_length = 1

            for edge in argument_slot.edge_sequence:
                child_node = edge.to_node
                hash_val = id(child_node)
                if hash_val in visited:
                    continue

                new_cycle_length = _add_values(cycle_length, sub_cycle_length)
                visited.add(hash_val)
                parent_nodes[child_node] = node
                queue.append((child_node, new_cycle_length))
                # Add the cycle length of the edge to the sub_cycle_length to increase cylce_length of next edges to account for
                sub_cycle_length = _add_values(sub_cycle_length, _mul_values(edge.cycle_length, edge.weight))
    raise Exception("No cycle found")


# SIMPLE OPERATIONS ON NUMBERS AND COMPARISONS
def _is_greater(lhs: Union[int, float, Node], rhs: Union[int, float, Node]) -> bool:
    """ Returns if lhs is greater or equal than rhs by simply looking at numbers or node strucutre"""
    if isinstance(lhs, float): return True
    if isinstance(rhs, float): return False
    if isinstance(lhs, int) and isinstance(rhs, int): return lhs >= rhs
    if not isinstance(lhs, Node): return _is_greater(_to_node(lhs), rhs)
    if not isinstance(rhs, Node): return _is_greater(lhs, _to_node(rhs))
    # TODO: Implement Node comparison on integer valued expressions
    return True


def _add_values(weight1: Union[int, float, Node], weight2: Union[int, float, Node]) -> Union[int, float, Node]:
    """ Helper function to add together two nodes """
    if isinstance(weight1, Node):
        return operations["add"](weight1, _to_node(weight2))
    if isinstance(weight2, Node):
        return operations["add"](_to_node(weight1), weight2)
    return weight1 + weight2


def _sub_values(weight1: Union[int, float, Node], weight2: Union[int, float, Node]) -> Union[int, float, Node]:
    """ Helper function to subtract two nodes """
    if isinstance(weight1, Node):
        return operations["sub"](weight1, _to_node(weight2))
    if isinstance(weight2, Node):
        return operations["sub"](_to_node(weight1), weight2)
    return weight1 - weight2


def _mul_values(weight1: Union[int, float, Node], weight2: Union[int, float, Node]) -> Union[int, float, Node]:
    """ Helper function to multiply together two nodes """
    if isinstance(weight1, Node):
        return operations["mul"](weight1, _to_node(weight2))
    if isinstance(weight2, Node):
        return operations["mul"](_to_node(weight1), weight2)
    return weight1 * weight2


def _int_to_node(val: int) -> Node:
    """ Converts integer value to node strucutre """
    # TODO: Has to implemented
    return Node(Set(binding_quantity=(definitions["integers"], ), nested_depth=0))


def _to_node(val: Union[int, float, Node]) -> Node:
    """ Wraper function nto convert integer value or node to ode strucutre """
    if isinstance(val, Node):
        return val
    return _int_to_node(val)


# HELPER FUNCTIONS FOR CRM-ALGORITHM
def _evaluate_node(node: Node, n: int) -> int:
    """ Evaluates a node with common operations on reels and only one object varible """
    # TODO
    raise NotImplementedError("No evaluation implemented yet")


def _same_cycle_chain(cycle1: List[Node], cycle2: List[Node], comparison_func: Callable) -> bool:
    """
    Checks if two given cycles are the same.
    Function hearby assumes that both lists are of the same length and the last element is the same.
    To prevent reccursion calls in __eq__ methode next_sequence nodes aren't processed when child_nodes.
    """
    for i, (self_node, other_node) in enumerate(zip(cycle1[:-1], cycle2[:-1])):
        if len(self_node.argument_slots) != len(other_node.argument_slots):
            return False
        next_node_self = cycle1[i + 1]
        next_node_other = cycle2[i + 1]
        for self_argument_slot, other_argument_slot in zip(self_node.argument_slots, other_node.argument_slots):
            if next_node_self in self_argument_slot.get_pointed_nodes() or next_node_other in other_argument_slot.get_pointed_nodes():
                # Don't check child nodes in currently checked cycle to stop reccursion errors
                continue
            if not comparison_func(self_argument_slot, other_argument_slot):
                return False
    return True

def _lcm_phase_reduction_valid(cycle1: List[Node], cycle2: List[Node], comparison_func: Callable) -> bool:
    """ Helper function to check if two given cycles are the same using lcm reduction """
    cycle1_length = len(cycle1)
    cycle2_length = len(cycle2)
    try:
        lcm = math.lcm(cycle1_length, cycle2_length)
    except ValueError:
        raise NotImplementedError("Comparisons of variable length edges is not yet supported")

    lcm_cycle_self = cycle1 * int(lcm / cycle1_length)
    lcm_cycle_other = cycle2 * int(lcm / cycle2_length)
    if not _same_cycle_chain(lcm_cycle_self, lcm_cycle_other, comparison_func):
        return False
    return True


def _boolean_cmr(state1: CycleState, state2: CycleState, comparison_func: Callable[[Union[Node, ArgumentSlot, Edge, Object], Union[Node, ArgumentSlot, Edge, Object]], bool]) -> bool:
    """ Gets boolean cmr return """
    return cmr(state1, state2, comparison_func)[2]


def cmr(state1: CycleState, state2: CycleState, comparison_func: Callable[[Union[Node, ArgumentSlot, Edge, Object], Union[Node, ArgumentSlot, Edge, Object]], bool]) -> Tuple[Union[Node, None], Union[Node, None], bool]:
    """ Runs cmr algorithm reccursively """
    # TODO: Extend algorithm to work on multiple nodes after slots are equal
    if state1.idx >= len(state1.edge_sequence) or state2.idx >= len(state2.edge_sequence):
        if state1.idx == len(state1.edge_sequence) and state2.idx == len(state2.edge_sequence):
            node1 = _get_cycle_nodes(state1.edge_sequence[-1].to_node)[state1.shift]
            node2 = _get_cycle_nodes(state2.edge_sequence[-1].to_node)[state2.shift]
            return node1, node2, True
        edge1 = state1.edge_sequence[state1.idx]
        edge2 = state2.edge_sequence[state2.idx]
        return _get_cycle_nodes(edge1.parent_node, edge1.cycle_length)[state1.shift], _get_cycle_nodes(edge2.parent_node, edge2.cycle_length)[state1.shift], False

    edge1 = state1.edge_sequence[state1.idx]
    edge2 = state2.edge_sequence[state2.idx]

    # Acyclic case
    if not (edge1.cyclical and edge2.cyclical):
        if not comparison_func(edge1.to_node, edge2.to_node):
            return None, None, False

        next_state1 = CycleState(edge_sequence=state1.edge_sequence, idx=state1.idx + 1, shift=0)
        next_state2 = CycleState(edge_sequence=state2.edge_sequence, idx=state2.idx + 1, shift=0)
        return cmr(next_state1, next_state2, comparison_func)

    # Check cycles
    un_shifted_cycle1 = _get_cycle_nodes(edge1.parent_node, edge1.cycle_length)
    un_shifted_cycle2 = _get_cycle_nodes(edge2.parent_node, edge2.cycle_length)
    cycle1 = un_shifted_cycle1[state1.shift:] + un_shifted_cycle1[:state1.shift]
    cycle2 = un_shifted_cycle2[state2.shift:] + un_shifted_cycle2[:state2.shift]
    if not _lcm_phase_reduction_valid(cycle1, cycle2, comparison_func):
        return None, None, False

    # Get or calculate full length
    len1 = state1.full_cycle_length if state1.full_cycle_length else _mul_values(edge1.weight, edge1.cycle_length)
    len2 = state2.full_cycle_length if state2.full_cycle_length else _mul_values(edge2.weight, edge2.cycle_length)

    # Symmetry
    if not _is_greater(len1, len2):
        node2, node1, valid = cmr(state2, state1, comparison_func)
        return node1, node2, valid

    # Calculate overhang and residu
    overhang = _sub_values(len1, len2)
    next_state2 = CycleState(edge_sequence=state2.edge_sequence, idx=state2.idx + 1, shift=0)

    # Find and evaluate residu set
    residu_set = set()
    m = edge1.cycle_length
    valid = True
    unvalid_case_node_tuple: set[Tuple[Node, Node]] = set()
    for k in range(1, m):
        n = _evaluate_node(edge1.weight, k) % m
        if n in residu_set:
            continue
        residu_set.add(n)

        shifted_state1 = CycleState(edge_sequence=state1.edge_sequence, idx=state1.idx, shift=(state1.shift + n) % m, full_cycle_length=overhang)
        node1, node2, this_valid = cmr(shifted_state1, next_state2, comparison_func)
        if not this_valid:
            valid = False
            unvalid_case_node_tuple.add((node1, node2))

    if not valid:
        if len(unvalid_case_node_tuple) == 1:
            pair = list(unvalid_case_node_tuple)[0]
            return pair[0], pair[1], False
        return None, None, False

    return un_shifted_cycle1[state1.shift], un_shifted_cycle2[state2.shift], True


