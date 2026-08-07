from typing import Union
from ExpressionTree import Node
from MObject import Function, ElementrySet, Set, PowerSet, FunctionSet, Quantor, Variable
from Statement import Relation, Statement


def ball_func(on_set: Union[ElementrySet, Set, PowerSet, FunctionSet], reel_nums: ElementrySet):
    return Function(quantor=Quantor.DEFINE, binding_quantity=(Set(quantor=Quantor.FORALL, binding_quantity=(FunctionSet(quantor=Quantor.FORALL, binding_quantity=(on_set, on_set)), reel_nums, on_set)), PowerSet(quantor=Quantor.FORALL, binding_quantity=(on_set, ))))


def continuous(func: Function, metr_input: Function, metr_output: Function, real_nums: ElementrySet):
    """ Returns a statement such that the node is continuous """
    in_set = func.binding_quantity[0]
    out_set = func.binding_quantity[1]
    B_in = ball_func(in_set, real_nums)
    B_out = ball_func(out_set, real_nums)
    epsilon = Variable(quantor=Quantor.FORALL, binding_quantity=(real_nums,))
    delta = Variable(quantor=Quantor.EXISTS, binding_quantity=(real_nums,))
    point = Variable(quantor=Quantor.FORALL, binding_quantity=(in_set, ))

    continuity_left = Node(func, child_nodes=[Node(B_in, child_nodes=[Node(metr_input), Node(delta), Node(point)])])
    continuity_right = Node(B_out, child_nodes=[Node(metr_output), Node(epsilon), Node(func, child_nodes=[Node(point)])])

    return Statement(continuity_left, continuity_right, Relation.SUBSET)
