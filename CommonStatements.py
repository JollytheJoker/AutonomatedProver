import copy
from typing import Union
from ExpressionTree import Node
from MObject import Function, ElementrySet, Set, PowerSet, FunctionSet, Quantor, Variable
from Statement import Relation, Statement


def _attach_at_leaf(root_node: Node, new_child: Node) -> Node:
    """ Puts the new_child at the most inner node if there is always at most 1 child"""
    copied_root = copy.deepcopy(root_node)
    current = copied_root
    while current.child_nodes:
        if len(current.child_nodes) > 1:
            raise ValueError("Can at most have one parameter for continuity")
        current = current.child_nodes[0]
    current.child_nodes = [new_child]
    return copied_root

def ball_func(on_set: Union[ElementrySet, Set, PowerSet, FunctionSet], reel_nums: ElementrySet):
    return Function(quantor=Quantor.DEFINE, binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(FunctionSet(quantor=Quantor.FORALL, binding_quantity=(on_set, on_set)), reel_nums, on_set)), PowerSet(quantor=Quantor.FORALL, binding_quantity=(on_set, ))), assosiation=f'B_{"{"}{str(on_set.assosiation)}{"}"}')


def continuous(func: Function | Node, metr_input: Function, metr_output: Function, real_nums: ElementrySet):
    """ Returns a statement such that the node is continuous """
    if isinstance(func, Function):
        func = Node(func)
    in_set = metr_input.binding_quantity[0]
    out_set = metr_output.binding_quantity[0]
    B_in = ball_func(in_set, real_nums)
    B_out = ball_func(out_set, real_nums)
    epsilon = Variable(quantor=Quantor.FORALL, binding_quantity=(real_nums,))
    delta = Variable(quantor=Quantor.EXISTS, binding_quantity=(real_nums,))
    point = Variable(quantor=Quantor.FORALL, binding_quantity=(in_set, ))

    # We want to put the point as a parameter for the most inner function

    ball_node = Node(B_in, child_nodes=[Node(metr_input), Node(delta), Node(point)])
    continuity_left = _attach_at_leaf(func, ball_node)

    inner_application = _attach_at_leaf(func, Node(point))
    continuity_right = Node(B_out, child_nodes=[Node(metr_output), Node(epsilon), inner_application])

    return Statement(continuity_left, continuity_right, Relation.SUBSET)