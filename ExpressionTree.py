from __future__ import annotations
import math
from collections import deque
from functools import cached_property
import copy
from dataclasses import dataclass, field, replace
from MObject import Object, Set, ElementrySet, PowerSet, Function, Variable, Quantor, FunctionSet
from typing import Tuple, Dict, List, Generator, Union, NamedTuple
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
        parent_hash = hash(self.parent_node)
        nodes_queue = deque([(self.to_node, 0)])
        while nodes_queue:
            node, cycle_length = nodes_queue.popleft()
            for argument_slot in node.argument_slots:
                sub_cycle_length = 1
                for edge in argument_slot.edge_sequence:
                    child_node = edge.to_node
                    hash_val = hash(child_node)
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
        return self.edge_sequence[0].to_node.node_object

    @cached_property
    def number_of_applications(self) -> Union[int, float, Node]:
        """ Returns the sum of all edges' cycle lengths """
        return sum(edge.cycle_length for edge in self.edge_sequence)

    @classmethod
    def create(cls, edge_sequence: Union[List[Edge], Tuple[Edge, ...]], parent_node: Node, desired_output: Object) -> ArgumentSlot:
        return cls(cls._simplify(edge_sequence, parent_node), parent_node, desired_output)

    def __eq__(self, other: ArgumentSlot):
        """ Strict equality check of every edge in argument sequence """
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

        return _reduce_cycles_over_accounting_for_residu(state_self, state_other)

    def check_validity(self) -> bool:
        """ Checks if edges are valid and if all sequence's edge's nodes output desired object """
        cyclical_flag = True
        for edge in self.edge_sequence:
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

    def __eq__(self, other: Node):
        """
        Strict equality check in every single attribute
        """
        if self is other:
            return True
        if self.math_object != other.math_object:
            return False
        if len(self.argument_slots) != len(other.argument_slots):
            return False
        for self_slot, other_slot in zip(self.argument_slots, other.argument_slots):
            if self_slot == other_slot:
                return False
        return True

    def __hash__(self):
        return hash(tuple([self.math_object.toTuple()] + [hash(slot) for slot in self.argument_slots]))

    @cached_property
    def node_object(self):
        """
        Recursively build up the node tuple using the function at the node
        """
        if not self.argument_slots:
            return self.math_object

        quantor = Quantor.EXISTS if any(child_object.math_object.quantor == Quantor.EXISTS or child_object.math_object.quantor == Quantor.DEFINE for child_object in self.final_child_nodes) else Quantor.FORALL
        # Get the output type by checking if any input is set instead of variable if variable was given. E.g., f(X) will be a set, but the output of x was normally defined as output variables.
        math_obj_out = self.math_object.binding_quantity[1]
        normal_output = _get_normal_output_of_function(math_obj_out)

        # Test for any change in input
        upper_output_type = _get_upper_output_type_value(self, self.math_object.binding_quantity[0])
        if upper_output_type > 0:
            normal_output = math_obj_out
        for _ in range(upper_output_type - 1):
            normal_output = PowerSet(binding_quantity=(normal_output, ), quantor=quantor)

        return replace(normal_output, mathematical_quantity=self.math_object.mathematical_quantity, obj_id=-1, quantor=quantor)

    @cached_property
    def final_child_nodes(self):
        result = []
        for child_chain in self.child_nodes:
            # Most outer application is first in child_chain
            application = child_chain[0][0].math_object
            if len(child_chain) > 1:
                if not isinstance(application, Function):
                    raise ValueError("Can't multicall on a non-function")
            else:
                if child_chain[0][1] != 1:
                    raise ValueError("Non-function node can only be pointed to exactly ones")
                result.append(copy.deepcopy(child_chain[0][0]))
                continue
            normal_output = _get_normal_output_of_function(application.binding_quantity[1])
            quantor = Quantor.EXISTS if any(node.math_object.quantor == Quantor.EXISTS or node.math_object.quantor == Quantor.DEFINE for node, _ in child_chain) else Quantor.FORALL
            upper_output_type = _get_upper_output_type_value(child_chain[-1][0], child_chain[-1][0].math_object.binding_quantity[0])
            if upper_output_type > 0:
                normal_output = application.binding_quantity[1]
            for _ in range(upper_output_type - 1):
                normal_output = PowerSet(binding_quantity=(normal_output,), quantor=quantor)
            normal_output = replace(normal_output, obj_id=-1, quantor=quantor)
            final_node = Node(normal_output, child_nodes=child_chain[-1][0].child_nodes)
            result.append(final_node)
        return result

    def primitive_eq(self, other: Node, print_trace: bool = False):
        """
        Runs primitive equal check between two nodes. They are equal if type and binding quantity are the same
        """
        if print_trace: print(f"Checking {self} == {other}")
        self_obj = self.node_object
        other_obj = other.node_object
        # Two functional application can only equal if their functions are equal and child_nodes are primitively equal
        if self_obj.obj_id == other_obj.obj_id == -1:
            if self.math_object == other.math_object:
                for self_child, other_child in zip(self.final_child_nodes, other.final_child_nodes):
                    if not self_child.primitive_eq(other_child, print_trace=print_trace):
                        if print_trace: print(f"False: child_nodes unequal {self_child} & {other_child}")
                        return False
                if print_trace: print("True: All child nodes and functions are equal")
                return True
            if print_trace: print("False: Different functions")
            return False
        if type(self_obj) is not type(other_obj):
            if print_trace: print(f"False: Type didn't match: {type(self_obj)} & {type(other_obj)}")
            return False
        if self_obj.obj_id != -1 and other_obj.obj_id != -1:
            # Special case
            if self_obj.binding_quantity == other_obj.binding_quantity and (self_obj.quantor == Quantor.FORALL or other_obj.quantor == Quantor.FORALL) and self_obj.mathematical_quantity == other_obj.mathematical_quantity:
                if print_trace: print(f"True: Node object's type and binding status equal. Since both are for all over same domain and have same mathematical binding, the elements are the same {self} == {other}")
                return True
            if self_obj.obj_id != other_obj.obj_id:
                if print_trace: print(f"False: Object ids are not -1 but differ: {self_obj.obj_id} & {other_obj.obj_id}")
                return False
        if print_trace: print(f"True: Node object's type {'and object ids are' if self_obj.obj_id == -1 or other_obj.obj_id == -1 else 'is'} equal")
        return True

    def primitive_contains(self, other: Node, print_trace: bool = False) -> Generator[Node, Node]:
        """
        Runs primitive recursive check on tree structure to yield possible equal nodes as well as parent nodes.
        """
        if print_trace: print(f"Checking {other} contains {self}")
        if self.primitive_eq(other, print_trace=print_trace):
            if print_trace: print(f"{self} == {other}")
            yield self, None
        for child_chain in self.child_nodes:
            if print_trace: print(f"    Checking {child_chain[0][0]}")
            # Generate all possible child_nodes
            recursive_node = child_chain[-1][0]
            #breakpoint()
            for res in recursive_node.primitive_contains(other, print_trace=print_trace):
                if print_trace: print(f"{res[0]}")
                yield res[0], self
            if print_trace and recursive_node.primitive_contains(other) is None:
                print(f"{recursive_node} has no primitive contains of {other}")

            for i in range(2, len(child_chain)):
                # Run with function
                for res in recursive_node.primitive_contains(other, print_trace=print_trace):
                    if print_trace: print(f"{res}")
                    yield res[0], self
                if print_trace and recursive_node.primitive_contains(other) is None:
                    print(f"{recursive_node} has no primitive contains of {other}")

                next_element = child_chain[-i]
                temp_node_w1 = Node(math_object=next_element[0].math_object, child_nodes=[[(recursive_node, 1)]])

                for res in temp_node_w1.primitive_contains(other, print_trace=print_trace):
                    yield res[0], self
                if print_trace and not any(True for _ in temp_node_w1.primitive_contains(other)):
                    print(f"{temp_node_w1} has no primitive contains of {other}")

                # 3. Run with full weight applied function
                recursive_node = Node(math_object=next_element[0].math_object,
                                      child_nodes=[[next_element, (recursive_node, 1)]])

                for res in recursive_node.primitive_contains(other, print_trace=print_trace):
                    yield res[0], self
                if print_trace and not any(True for _ in recursive_node.primitive_contains(other)):
                    print(f"{recursive_node} has no primitive contains of {other}")

        if print_trace: print("Contains check done")

    def get_mappings_dict_for_replacement(self, other: Node, mapping: Dict[Node, Node] = None, print_trace: bool = False) -> Tuple[Dict[Node, Node], bool]:
        """
        Recursively checks what nodes had to be replaced if other would be applied
        """
        if not mapping:
            mapping = {}
        if self.math_object != other.math_object:
            if print_trace: print(f"Can't map {self} - {other} because {self.math_object} != {other.math_object}")
            return mapping, False

        for self_child_chain, other_child_chain in zip(self.child_nodes, other.child_nodes):
            if len(self_child_chain) != len(other_child_chain):
                if print_trace: print(f"Can't map, because child chains don't match: {len(self_child_chain)} & {len(other_child_chain)}")
                return mapping, False
            for (self_node, self_weight), (other_node, other_weight) in zip(self_child_chain, other_child_chain):
                if self_weight != other_weight:
                    if print_trace: print(f"Can't map, because chain weights missmatch: {self_node}, {self_weight} & {other_node}, {other_weight}")
                    return mapping, False

                if self_node.math_object != other_node.math_object:
                    if self_node.node_object.quantor >= other_node.node_object.quantor:
                        if print_trace: print(f"Map {self_node} - {other_node} because of quantor hierarchy on tuple {self_node.node_object} & {other_node.node_object}")
                        mapping[self_node] = other_node
                    else:
                        if print_trace: print(f"Can't map {self_node} - {other_node}, because self is of lower quantor hierarchy {self_node.node_object} & {other_node.node_object}")
                        return mapping, False
                else:
                    mapping, possible = self_node.get_mappings_dict_for_replacement(other_node, mapping, print_trace)
                    if not possible:
                        return mapping, False

        return mapping, True

    def remap_objects(self, mapping: Dict[Node, Node], memo: Dict[Node, Node] = None) -> Node:
        """ Rebuilds ExpressionTree by replacing nodes with mapping nodes. Use memo parameter to stop rebuilding the same nodes multiple times """
        if memo is None:
            memo = {}

        if self in mapping:
            return mapping[self]
        if self in memo:
            return memo[self]

        new_child_nodes = []
        for child_chain in self.child_nodes:
            new_chain = []
            for child, weight in child_chain:
                new_child = child.remap_objects(mapping, memo)
                new_chain.append((new_child, weight))
            new_child_nodes.append(new_chain)

        new_node = Node(math_object=self.math_object)
        new_node.child_nodes = new_child_nodes

        new_node._simplify_child_nodes()

        memo[self] = new_node
        return new_node

    def id_less_equal(self, other: Node):
        """ Checks if other node is exactly the same as self, but without checking for ids """
        if self.math_object != other.math_object:
            return False
        if len(self.child_nodes) != len(other.child_nodes):
            return False
        for self_child_chain, other_child_chain in zip(self.child_nodes, other.child_nodes):
            if len(self_child_chain) != len(other_child_chain):
                return False
            for (self_child, self_weight), (other_child, other_weight) in zip(self_child_chain, other_child_chain):
                if self_weight != other_weight:
                    return False
                if not self_child.id_less_equal(other_child):
                    return False
        return True


def _get_normal_output_of_function(obj: Object) -> Object:
    """ Returns an instance of a functions normal output """
    if isinstance(obj, Variable):
        raise Exception("Can't map onto one variable")
    elif isinstance(obj, ElementrySet) or isinstance(obj, Set):
        return Variable(binding_quantity=(obj, ), quantor=Quantor.FORALL)
    elif isinstance(obj, PowerSet):
        max_nested_depth = max(s.nested_depth if isinstance(s, PowerSet) else 0 for s in obj.binding_quantity)
        return replace(obj, nested_depth=max_nested_depth - 1) if max_nested_depth > 0 else Set(binding_quantity=obj.binding_quantity, quantor=Quantor.FORALL)
    elif isinstance(obj, FunctionSet):
        return Function(binding_quantity=obj.binding_quantity, quantor=Quantor.FORALL)
    else:
        raise Exception(f"Unknown type {type(obj)}")


def _get_upper_output_type_value(node: Node, expected: Object) -> int:
    """ Checks if any input's depth exceeds expected and returns the difference; e.g. set is given instead of variable """
    upper_output_type = 0
    if isinstance(expected, Variable):
        raise Exception("Can't map from one variable")
    if isinstance(expected, ElementrySet):
        if len(node.child_nodes) != 1:
            raise Exception("Must have exactly one child node if elementry set is used")
        for child_chain in node.child_nodes:
            for child_node, _ in child_chain:
                if isinstance(child_node.math_object, PowerSet):
                    upper_output_type = max(upper_output_type, child_node.math_object.nested_depth + 1)
                if isinstance(child_node.math_object, Set) or isinstance(child_node.math_object, ElementrySet):
                    upper_output_type = max(upper_output_type, 1)
    if isinstance(expected, Set):
        for i, child_chain in enumerate(node.child_nodes):
            binding_quantity = expected.binding_quantity[i]
            for child_node, _ in child_chain:
                child_node_obj = child_node.math_object
                if type(child_node_obj) is not type(binding_quantity):
                    if isinstance(child_node_obj, Set) and isinstance(binding_quantity, Variable):
                        upper_output_type = max(upper_output_type, 1)
                    elif isinstance(child_node_obj, PowerSet) and isinstance(binding_quantity, Variable):
                        upper_output_type = max(upper_output_type, 1 + child_node_obj.nested_depth)
                    elif isinstance(child_node_obj, PowerSet) and isinstance(binding_quantity, Set):
                        upper_output_type = max(upper_output_type, child_node_obj.nested_depth)
                    elif isinstance(child_node_obj, PowerSet) and isinstance(binding_quantity, PowerSet):
                        if child_node_obj.nested_depth < binding_quantity.nested_depth:
                            raise Exception("Input nested depth must be equal or exceed defined nested depth")
                        upper_output_type = max(upper_output_type, child_node_obj.nested_depth - binding_quantity.nested_depth)
    if isinstance(expected, PowerSet):
        if len(node.child_nodes) != 1:
            raise Exception("Must have exactly one child node if powerset is used")
        for child_chain in node.child_nodes:
            for child_node, _ in child_chain:
                if not isinstance(child_node.math_object, PowerSet):
                    raise Exception("Input must be of higher or same nested depth")
                if child_node.math_object.nested_depth < expected.nested_depth:
                    raise Exception("Input must be of higher or same nested depth")
                upper_output_type = max(child_node.math_object.nested_depth - expected.nested_depth, upper_output_type)
    return upper_output_type


@dataclass(frozen=True)
class Expression:
    root_node: Node


def _get_cycle_nodes(start_node: Node, desired_length: int = -1) -> List[Node]:
    """ Returns the list of nodes that lead to the cycle as paremters """
    # Use simple BFS. TODO: Upgrade to bidirectional BFS for efficiency
    queue = deque([(start_node, 0)])
    parent_nodes = {start_node: None}
    visited = {hash(start_node)}

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
                hash_val = hash(child_node)
                new_cycle_length = _add_values(cycle_length, sub_cycle_length)
                if hash_val in visited:
                    continue
                visited.add(hash_val)
                parent_nodes[child_node] = node
                queue.append((child_node, new_cycle_length))
                # Add the cycle length of the edge to the sub_cycle_length to increase cylce_length of next edges to account for
                sub_cycle_length = _add_values(sub_cycle_length, _mul_values(edge.cycle_length, edge.weight))
    raise Exception("No cycle found")


def _is_greater(lhs: Union[int, float, Node], rhs: Union[int, float, Node]) -> bool:
    """ Returns if lhs is greater or equal than rhs by simply looking at numbers or node strucutre"""
    if isinstance(lhs, float): return True
    if isinstance(rhs, float): return False
    if isinstance(lhs, int) and isinstance(rhs, int): return lhs >= rhs
    if not isinstance(lhs, Node): return _is_greater(_int_to_node(lhs), rhs)
    if not isinstance(rhs, Node): return _is_greater(lhs, _int_to_node(rhs))
    # TODO: Implement Node comparison on integer valued expressions
    return True


def _add_values(weight1: Union[int, float, Node], weight2: Union[int, float, Node]) -> Union[int, float, Node]:
    """ Helper function to add together two nodes """
    if isinstance(weight1, Variable):
        return operations["add"](weight1, _to_node(weight2))
    if isinstance(weight2, Variable):
        return operations["add"](_to_node(weight1), weight2)
    return weight1 + weight2


def _sub_values(weight1: Union[int, float, Node], weight2: Union[int, float, Node]) -> Union[int, float, Node]:
    """ Helper function to subtract two nodes """
    if isinstance(weight1, Variable):
        return operations["sub"](weight1, _to_node(weight2))
    if isinstance(weight2, Variable):
        return operations["sub"](_to_node(weight1), weight2)
    return weight1 - weight2


def _mul_values(weight1: Union[int, float, Node], weight2: Union[int, float, Node]) -> Union[int, float, Node]:
    """ Helper function to multiply together two nodes """
    if isinstance(weight1, Variable):
        return operations["mul"](weight1, _to_node(weight2))
    if isinstance(weight2, Variable):
        return operations["mul"](_to_node(weight1), weight2)
    return weight1 * weight2


def _int_to_node(val: int) -> Node:
    """ Converts integer value to node strucutre """
    # TODO: Has to implemented
    return Node(Variable(binding_quantity=(definitions["integers"], )))


def _to_node(val: Union[int, float, Node]) -> Node:
    """ Wraper function to convert integer value or node to node strucutre """
    if isinstance(val, Node):
        return val
    # TODO
    return _int_to_node(val)


def _evaluate_node(node: Node, n: int) -> int:
    """ Evaluates a node with common operations on reels and only one object varible """
    # TODO
    raise NotImplementedError("No evaluation implemented yet")


def _same_cycle_chain(cycle1: List[Node], cycle2: List[Node]) -> bool:
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
            if self_argument_slot != other_argument_slot:
                return False
    return True

def _lcm_phase_reduction_valid(cycle1: List[Node], cycle2: List[Node]) -> bool:
    """ Helper function to check if two given cycles are the same using lcm reduction """
    cycle1_length = len(cycle1)
    cycle2_length = len(cycle2)
    try:
        lcm = math.lcm(cycle1_length, cycle2_length)
    except ValueError:
        raise NotImplementedError("Comparisons of variable length edges is not yet supported")

    lcm_cycle_self = cycle1 * int(lcm / cycle1_length)
    lcm_cycle_other = cycle2 * int(lcm / cycle2_length)
    if not _same_cycle_chain(lcm_cycle_self, lcm_cycle_other):
        return False
    return True


def _reduce_cycles_over_accounting_for_residu(state1: CycleState, state2: CycleState) -> bool:
    """ CMR-Algorithm for reduction of preidic cyclic graphs """
    if state1.idx >= len(state1.edge_sequence) or state2.idx >= len(state2.edge_sequence):
        return state1.idx == len(state1.edge_sequence) and state2.idx == len(state2.edge_sequence)

    edge1 = state1.edge_sequence[state1.idx]
    edge2 = state2.edge_sequence[state2.idx]
    if not (edge1.cyclical and edge2.cyclical):
        return edge1.to_node.primitive_eq(edge2.to_node)

    # Check cycles
    un_shifted_cycle1 = _get_cycle_nodes(edge1.parent_node, edge1.cycle_length)
    un_shifted_cycle2 = _get_cycle_nodes(edge2.parent_node, edge2.cycle_length)
    cycle1 = un_shifted_cycle1[state1.shift:] + un_shifted_cycle1[:state1.shift]
    cycle2 = un_shifted_cycle2[state2.shift:] + un_shifted_cycle2[:state2.shift]
    if not _lcm_phase_reduction_valid(cycle1, cycle2):
        return False

    # Get or calculate full length
    len1 = state1.full_cycle_length if state1.full_cycle_length else _mul_values(edge1.weight, edge1.cycle_length)
    len2 = state2.full_cycle_length if state2.full_cycle_length else _mul_values(edge2.weight, edge2.cycle_length)

    # Symmetry
    if not _is_greater(len1, len2):
        return _reduce_cycles_over_accounting_for_residu(state2, state1)

    # Calculate overhang and residu
    overhang = _sub_values(len1, len2)
    next_state2 = CycleState(edge_sequence=state2.edge_sequence, idx=state2.idx + 1, shift=0)

    # Find and evaluate residu set
    residu_set = set()
    m = edge1.cycle_length
    for k in range(1, m):
        n = _evaluate_node(edge1.weight, k) % m
        if n in residu_set:
            continue
        residu_set.add(n)

        shifted_state1 = CycleState(edge_sequence=state1.edge_sequence, idx=state1.idx, shift=(state1.shift + n) % m, full_cycle_length=overhang)
        if not _reduce_cycles_over_accounting_for_residu(shifted_state1, next_state2):
            return False

    return True


