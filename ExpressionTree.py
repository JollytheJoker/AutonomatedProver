from __future__ import annotations
from dataclasses import dataclass, field, replace
from MObject import Object, Set, ElementrySet, PowerSet, Function, Variable, Quantor, FunctionSet
from typing import Tuple, Dict, List, Generator


@dataclass
class Node:
    """
    One node in the expression tree graph. Contains the child nodes for recursive build up
    """
    math_object: Object
    node_object: Object = field(default_factory=Object, init=False)
    child_nodes: List['Node'] = field(default_factory=list)
    is_root: bool = field(default=False)

    def __post_init__(self):
        if len(self.child_nodes) > 0 and not isinstance(self.math_object, Function):
            raise Exception("Can only call functions")
        if len(self.child_nodes) > 1:
            if len(self.math_object.binding_quantity[0]) != len(self.child_nodes):
                raise Exception("Function has not the given number of inputs")

        self.object_tuple = self.math_object.toTuple()
        self.set_node_tuple()

    def __str__(self) -> str:
        """Recursively prints the node and its children in a tree structure"""
        if self.child_nodes:
            child_str = ', '.join(str(child) for child in self.child_nodes)
            return f'{self.math_object}({child_str})'
        return f'{self.math_object}'

    def __eq__(self, other: Node):
        """
        Strict equality check in every single attribute
        """
        if self.math_object != other.math_object:
            return False
        if self.child_nodes == other.child_nodes:
            return True
        return False

    def __copy__(self) -> 'Node':
        return Node(math_object=self.math_object, child_nodes=self.child_nodes, is_root=self.is_root)

    def __hash__(self):
        return hash(self.node_object.toTuple())

    def set_node_tuple(self):
        """
        Recursively build up the node tuple using the function at the node
        """
        if not self.child_nodes:
            self.node_object = self.math_object
            return

        quantor = Quantor.FORALL
        for node in self.child_nodes:
            node.set_node_tuple()
            # Update quantor
            nodeTuple = node.node_object.toTuple()
            if nodeTuple[3] == Quantor.DEFINE or nodeTuple[3] == Quantor.EXISTS:
                quantor = Quantor.EXISTS

        # Get the output type by checking if any input is set instead of variable if variable was given. E.g., f(X) will be a set, but the output of x was normally defined as output variables.
        math_obj_out = self.math_object.binding_quantity[1]
        if isinstance(math_obj_out, Variable):
            raise Exception("Can't map onto one variable")
        elif isinstance(math_obj_out, ElementrySet) or isinstance(math_obj_out, Set):
            normal_output = Variable(binding_quantity=(math_obj_out, ), quantor=Quantor.FORALL)
        elif isinstance(math_obj_out, PowerSet):
            max_nested_depth = max(s.nested_depth if isinstance(s, PowerSet) else 0 for s in math_obj_out.binding_quantity)
            normal_output = replace(math_obj_out, nested_depth=max_nested_depth - 1) if max_nested_depth > 0 else Set(binding_quantity=math_obj_out.binding_quantity, quantor=Quantor.FORALL)
        elif isinstance(math_obj_out, FunctionSet):
            normal_output = Function(binding_quantity=math_obj_out.binding_quantity, quantor=Quantor.FORALL)
        else:
            raise Exception(f"Unknown type {type(math_obj_out)}")

        # Test for any change in input
        math_obj_in = self.math_object.binding_quantity[0]
        upper_output_type = 0
        if isinstance(math_obj_in, Variable):
            raise Exception("Can't map from one variable")
        if isinstance(math_obj_in, ElementrySet):
            if len(self.child_nodes) != 1:
                raise Exception("Must have exactly one child node if elementry set is used")
            if isinstance(self.child_nodes[0].math_object, PowerSet):
                upper_output_type = self.child_nodes[0].math_object.nested_depth + 1
            if isinstance(self.child_nodes[0].math_object, Set) or isinstance(self.child_nodes[0].math_object, ElementrySet):
                upper_output_type = 1
        if isinstance(math_obj_in, Set):
            for i, child_node in enumerate(self.child_nodes):
                binding_quantity = math_obj_in.binding_quantity[i]
                child_node_obj = child_node.math_object
                if type(child_node_obj) != type(binding_quantity):
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
        if isinstance(math_obj_in, PowerSet):
            if len(self.child_nodes) != 1:
                raise Exception("Must have exactly one child node if powerset is used")
            if not isinstance(self.child_nodes[0].math_object, PowerSet):
                raise Exception("Input must be of higher or same nested depth")
            if self.child_nodes[0].math_object.nested_depth < math_obj_in.nested_depth:
                raise Exception("Input must be of higher or same nested depth")
            upper_output_type = self.child_nodes[0].math_object.nested_depth - math_obj_in.nested_depth

        if upper_output_type > 0:
            normal_output = math_obj_out
        for _ in range(upper_output_type - 1):
            normal_output = PowerSet(binding_quantity=(normal_output, ), quantor=quantor)

        self.node_object = replace(normal_output, mathematical_quantity=self.math_object.mathematical_quantity, obj_id=-1, quantor=quantor)

    def primitive_eq(self, other: Node, print_trace: bool = False):
        """
        Runs primitive equal check between two nodes. They are equal if type and binding quantity are the same
        """
        if print_trace: print(f"Checking {self} == {other}")
        # Two functional application can only equal if their functions are equal and child_nodes are primitively equal
        if self.node_object.obj_id == other.node_object.obj_id == -1:
            if self.math_object == other.math_object:
                for self_child, other_child in zip(self.child_nodes, other.child_nodes):
                    if not self_child.primitive_eq(other_child, print_trace=print_trace):
                        if print_trace: print(f"False: child_nodes unequal {self_child} & {other_child}")
                        return False
                if print_trace: print("True: All child nodes and functions are equal")
                return True
            if print_trace: print("False: Different functions")
            return False
        if type(self.node_object) is not type(other.node_object):
            if print_trace: print(f"False: Type didn't match: {type(self.node_object)} & {type(other.node_object)}")
            return False
        if self.node_object.obj_id != -1 and other.node_object.obj_id != -1:
            # Special case
            if self.node_object.binding_quantity == other.node_object.binding_quantity and (self.node_object.quantor == Quantor.FORALL or other.node_object.quantor == Quantor.FORALL) and self.node_object.mathematical_quantity == other.node_object.mathematical_quantity:
                if print_trace: print(f"True: Node object's type and binding status equal. Since both are for all over same domain and have same mathematical binding, the elements are the same {self} == {other}")
                return True
            if self.node_object.obj_id != other.node_object.obj_id:
                if print_trace: print(f"False: Object ids are not -1 but differ: {self.node_object.obj_id} & {other.node_object.obj_id}")
                return False
        if print_trace: print(f"True: Node object's type {'and object ids are' if self.node_object.obj_id == -1 or other.node_object.obj_id == -1 else 'is'} equal")
        return True

    def primitive_contains(self, other: Node, print_trace: bool = False) -> Generator[Node, Node]:
        """
        Runs primitive recursive check on tree structure to yield possible equal nodes as well as parent nodes.
        """
        if print_trace: print(f"Checking {other} contains {self}")
        if self.primitive_eq(other, print_trace=print_trace):
            if print_trace: print(f"{self} == {other}")
            yield self, None
        for child_node in self.child_nodes:
            for res in child_node.primitive_contains(other, print_trace=print_trace):
                yield res[0], self
            if print_trace:
                if not child_node.primitive_contains(other):
                    print(f"{child_node} has no primitive contains of {other}")
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

        for i, (self_node, other_node) in enumerate(zip(self.child_nodes, other.child_nodes)):
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

    def remap_objects(self, mapping: Dict[Node, Node]) -> Node:
        if self in mapping:
            return mapping[self]

        new_children = [child.remap_objects(mapping) for child in self.child_nodes]

        copy_node = self.__copy__()
        copy_node.child_nodes = new_children

        return copy_node

    def id_less_equal(self, other: Node):
        """ Checks if other node is exaclty the same as self, but without checking for ids """
        if self.math_object != other.math_object:
            return False
        if len(self.child_nodes) != len(other.child_nodes):
            return False
        for self_child, other_child in zip(self.child_nodes, other.child_nodes):
            if not self_child.id_less_equal(other_child):
                return False
        return True


