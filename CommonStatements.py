import copy
from typing import Union, List, Tuple
from ExpressionTree import Node
from MObject import Function, Set, Quantor
from Statement import Relation, Statement, LogicalOperation, MetaObject, Bool
from Definitions import definitions
from Knuth_Bendix_Algorithm import knuth_bendix_algorithm, kbo_compare, simplify_statement_on_system, simplify_fully

# Must be refactored after expression tree change
'''def _attach_at_leaf(root_node: Node, new_child: Node) -> Node:
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
    return Statement(continuity_left, continuity_right, Relation.SUBSET)'''

# ---------------------- BASIC AXIOMS ----------------------

# (\land & \lor will be refered to 'o')#
logical_axioms: List[Tuple[Statement, Statement]] = []

# Define 3 placeholders
a = Statement(MetaObject(Statement, name='A'))
b = Statement(MetaObject(Statement, name='B'))
c = Statement(MetaObject(Statement, name='C'))

# NEUTRAL
# a and true = a
lhs = Statement(LogicalOperation.AND, a, Statement(Bool.TRUE))
logical_axioms.append((lhs, a))

# a or false = a
lhs = Statement(LogicalOperation.OR, a, Statement(Bool.FALSE))
logical_axioms.append((lhs, a))

# a and false = false
lhs = Statement(LogicalOperation.AND, a, Statement(Bool.FALSE))
logical_axioms.append((lhs, Statement(Bool.FALSE)))

# a or true = true
lhs = Statement(LogicalOperation.OR, a, Statement(Bool.TRUE))
logical_axioms.append((lhs, Statement(Bool.TRUE)))

# DUPLICATES
# a o a = a
lhs = Statement(LogicalOperation.AND, a, a)
logical_axioms.append((lhs, a))

lhs = Statement(LogicalOperation.OR, a, a)
logical_axioms.append((lhs, a))

# COMPLEMENT
# a and not a = false
lhs = Statement(LogicalOperation.AND, a, a.negation)
logical_axioms.append((lhs, Statement(Bool.FALSE)))

# a or not a = true
lhs = Statement(LogicalOperation.OR, a, a.negation)
logical_axioms.append((lhs, Statement(Bool.TRUE)))

# Kommutativity a o b = b o a
lhs = Statement(LogicalOperation.AND, a, b)
rhs = Statement(LogicalOperation.AND, b, a)
logical_axioms.append((lhs, rhs))

lhs = Statement(LogicalOperation.OR, a, b)
rhs = Statement(LogicalOperation.OR, b, a)
logical_axioms.append((lhs, rhs))

# Associativity (a o b) o c = a o (b o c)
lhs = Statement(LogicalOperation.AND, Statement(LogicalOperation.AND, a, b), c)
rhs = Statement(LogicalOperation.AND, a, Statement(LogicalOperation.AND, b, c))
logical_axioms.append((lhs, rhs))

lhs = Statement(LogicalOperation.OR, Statement(LogicalOperation.OR, a, b), c)
rhs = Statement(LogicalOperation.OR, a, Statement(LogicalOperation.OR, b, c))
logical_axioms.append((lhs, rhs))

# Distibutivity (a or b) and c = (a and c) or (b and c)
lhs = Statement(LogicalOperation.AND, Statement(LogicalOperation.OR, a, b), c)
rhs = Statement(LogicalOperation.OR, Statement(LogicalOperation.AND, a, c), Statement(LogicalOperation.AND, b, c))
logical_axioms.append((lhs, rhs))


test_statement = Statement(LogicalOperation.AND, a, Statement(LogicalOperation.OR, a, b))

print("KNUTH-BENDIX-SOLUTION")
system = knuth_bendix_algorithm(logical_axioms)
for key, value in system:
    print(f'Key: {key}, Value: {value}')

print(simplify_fully(test_statement, logical_axioms))



'''print(lhs)
print(logical_axioms[-3][1], logical_axioms[-3][0])

s1 = Statement(LogicalOperation.AND, a, b)
s2 = Statement(LogicalOperation.AND, b, a)
print(kbo_compare(s1, s2))
print(kbo_compare(s2, s1))

print(next(lhs.simplify(logical_axioms[-3][1], logical_axioms[-3][0])))'''

'''breakpoint()
print(next(logical_axioms[-5][0].simplify(logical_axioms[-3][0], logical_axioms[-3][1])))'''


# TODO: implement ZFC



# INGEGER DEFINITIONS AND OPERATIONS




