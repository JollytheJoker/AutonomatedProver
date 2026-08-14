from __future__ import annotations
from functools import cached_property
import copy
from dataclasses import dataclass, field, replace
from MObject import Object, Set, ElementrySet, PowerSet, Function, Variable, Quantor, FunctionSet
from typing import Tuple, Dict, List, Generator, Union
from Definitions import definitions


@dataclass
class Node:
    """
    One node in the expression tree graph. Contains the child nodes for recursive build up
    """
    math_object: Object
    child_nodes: List[List[Tuple[Node, Union[int, float, Object]]]] = field(default_factory=list)

    def __post_init__(self):
        if len(self.child_nodes) > 0 and not isinstance(self.math_object, Function):
            raise Exception("Can only call functions")
        if len(self.child_nodes) > 1:
            if len(self.math_object.binding_quantity[0]) != len(self.child_nodes):
                raise Exception("Function has not the given number of inputs")
        # Check child_nodes
        for child_node in self.child_nodes:
            for sub_node, weight in child_node:
                if weight == 1:
                    continue
                # Check if weight object is integer
                if isinstance(weight, Object):
                    if not isinstance(weight, Variable) or not weight.binding_quantity[0] == definitions['integers']:
                        raise ValueError("Edge's weight must be integer variable")
        self.object_tuple = self.math_object.toTuple()
        self._simplify_child_nodes()
        #self._set_final_child_nodes()
        #self._set_node_object()

    def __str__(self) -> str:
        """Recursively prints the node and its children in a tree structure"""
        if self.child_nodes:
            argument_strings = []
            for child_chain in self.child_nodes:  # z.B. [(f, 5), (g, 2), (x, 1)]
                child_str = ""
                for node, weight in child_chain[:-1]:
                    child_str += f'{str(node)}{"^" + str(weight) if weight != 1 else ""}('
                child_str += str(child_chain[-1][0])
                child_str += ")" * (len(child_chain) - 1)
                argument_strings.append(child_str)
            return f"{self.math_object}({', '.join(argument_strings)})"
        return f'{self.math_object}'

    def __eq__(self, other: Node):
        """
        Strict equality check in every single attribute
        """
        if self is other:
            return True
        if self.math_object != other.math_object:
            return False
        if len(self.child_nodes) != len(other.child_nodes):
            return False
        for self_child_chain, other_child_chain in zip(self.child_nodes, other.child_nodes):
            if len(self_child_chain) != len(other_child_chain):
                return False
            if any(self_node != other_node for self_node, other_node in zip(self_child_chain, other_child_chain)):
                return False
        return True

    def __copy__(self) -> 'Node':
        return Node(math_object=self.math_object, child_nodes=self.child_nodes)

    def __hash__(self):
        return hash(self.node_object.toTuple())

    @cached_property
    def node_object(self):
        """
        Recursively build up the node tuple using the function at the node
        """
        if not self.child_nodes:
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

    def _simplify_child_nodes(self):
        """ Simplifies the list of arguments in child_chain """
        # TODO
        pass

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

