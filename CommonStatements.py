import copy
from typing import Union
from ExpressionTree import Node
from MObject import Function, ElementrySet, Set, PowerSet, FunctionSet, Quantor, Variable
from Statement import Relation, Statement
from Definitions import definitions


def _attach_at_leaf(root_node: Node, new_child: Node) -> Node:
    """ Puts the new_child at the most inner node if there is always at most 1 child"""
    copied_root = copy.deepcopy(root_node)
    current = copied_root
    while current.child_nodes:
        if len(current.child_nodes) > 1:
            raise ValueError("Can at most have one parameter for continuity")
        current = current.child_nodes[0][-1][0]
    current.child_nodes = [[(new_child, 1)]]
    return copied_root


def ball_func(on_set: Union[ElementrySet, Set, PowerSet, FunctionSet]):
    """ A ball function for a given set """
    # Check if this ball function was added to definitions
    if f'B_{"{"}{str(on_set.association)}{"}"}' in definitions.keys():
        return definitions[f'B_{"{"}{str(on_set.association)}{"}"}']
    else:
        definitions[f'B_{"{"}{str(on_set.association)}{"}"}'] = Function(quantor=Quantor.DEFINE, binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(FunctionSet(quantor=Quantor.FORALL, binding_quantity=(on_set, on_set)), definitions["reels"], on_set)), PowerSet(quantor=Quantor.FORALL, binding_quantity=(on_set, ))), association=f'B_{"{"}{str(on_set.association)}{"}"}')
    return definitions[f'B_{"{"}{str(on_set.association)}{"}"}']


def continuous(func: Function | Node, metr_input: Function, metr_output: Function):
    """ Returns a statement such that the node is continuous """
    if isinstance(func, Function):
        func = Node(func)
    in_set = metr_input.binding_quantity[0]
    out_set = metr_output.binding_quantity[0]
    B_in = ball_func(in_set)
    B_out = ball_func(out_set)
    epsilon = Variable(quantor=Quantor.FORALL, binding_quantity=(definitions['reels'],))
    delta = Variable(quantor=Quantor.EXISTS, binding_quantity=(definitions['reels'],))
    point = Variable(quantor=Quantor.FORALL, binding_quantity=(in_set, ))

    # We want to put the point as a parameter for the most inner function

    ball_node = Node(B_in, child_nodes=[[(Node(metr_input), 1)], [(Node(delta), 1)], [(Node(point), 1)]])
    continuity_left = _attach_at_leaf(func, ball_node)

    inner_application = _attach_at_leaf(func, Node(point))
    continuity_right = Node(B_out, child_nodes=[[(Node(metr_output), 1)], [(Node(epsilon), 1)], [(inner_application, 1)]])
    return Statement(continuity_left, continuity_right, Relation.SUBSET)