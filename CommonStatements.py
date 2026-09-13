from dataclasses import replace
from typing import List, Tuple
from xml.dom.pulldom import START_ELEMENT

from ExpressionTree import Node
from MObject import Set, Function, Quantor
from Statement import Statement, LogicalOperation, MetaObject, Bool, Relation
from Knuth_Bendix_Algorithm import knuth_bendix_algorithm, kbo_compare, simplify_statement_on_system, simplify_fully


# ---------------------- BASIC AXIOMS ----------------------

# (\land & \lor will be refered to 'o')#
logical_axioms: List[Tuple[Statement, Statement]] = []

# Define 3 placeholders
a = Statement(MetaObject(Statement, name='A'))
b = Statement(MetaObject(Statement, name='B'))
c = Statement(MetaObject(Statement, name='C'))

# AXIOMS
# a xor false = a
lhs = Statement(LogicalOperation.XOR, a, Statement(Bool.FALSE))
logical_axioms.append((lhs, a))

# a xor a = false
lhs = Statement(LogicalOperation.XOR, a, a)
logical_axioms.append((lhs, Statement(Bool.FALSE)))

# a and true = a
lhs = Statement(LogicalOperation.AND, a, Statement(Bool.TRUE))
logical_axioms.append((lhs, a))

# a and false = false
lhs = Statement(LogicalOperation.AND, a, Statement(Bool.FALSE))
logical_axioms.append((lhs, Statement(Bool.FALSE)))

# a and a = a
lhs = Statement(LogicalOperation.AND, a, a)
logical_axioms.append((lhs, a))

# Distibutivity (a xor b) and c = (a and c) xor (b and c)
lhs = Statement(LogicalOperation.AND, Statement(LogicalOperation.XOR, a, b), c)
rhs = Statement(LogicalOperation.XOR, Statement(LogicalOperation.AND, a, c), Statement(LogicalOperation.AND, b, c))
logical_axioms.append((lhs, rhs))


'''print("KNUTH-BENDIX-SOLUTION")
system = knuth_bendix_algorithm(logical_axioms)
for key, value in system:
    print(f'Key: {key}, Value: {value}')


test_statement = Statement(LogicalOperation.XOR, a, Statement(LogicalOperation.XOR, a, a))
test_statement = test_statement.canonical

print(simplify_fully(test_statement, system))'''



# TODO: implement ZFC



# TODO: INGEGER DEFINITIONS AND OPERATIONS

# ---------------------- SET & FUNCTIONAL DEFINITIONS ----------------------
def inverse(f: Function) -> Tuple[Function, Statement]:
    """ Returns an instance of an inverse function and the statement that makes the function the functions inverse """
    in_set = f.input_set
    out_set = f.output_set

    f_inv = replace(f, binding_quantity=(out_set, in_set))
    in_el = Set((in_set,), Quantor.FORALL, '', 0)
    out_el = Set((out_set,), Quantor.FORALL, '', 0)

    f_node = Node(f)
    f_inv_node = Node(f_inv)
    in_el_node = Node(in_el)
    out_el_node = Node(out_el)

    # f^-1(f(x)) = x
    A = Statement(Relation.EQUAL, Statement(f_inv_node(f_node(in_el_node))), Statement(in_el_node))

    # f(f^-1(y)) = y
    B = Statement(Relation.EQUAL, Statement(f_node(f_inv_node(out_el_node))), Statement(out_el_node))

    return f_inv, Statement(LogicalOperation.AND, A, B)

# ---------------------- TOPOLOGICAL DEFINITIONS ----------------------
def topolgy(X: Set) -> Set:
    """ Returns a topology set tau for this statement X """
    if not isinstance(X, Set):
        raise TypeError('X is not a set')

    if X.nested_depth == 0:
        raise Exception('X is not true set (most likely variable)')

    return replace(X, nested_depth=X.nested_depth + 1)

def _is_topology(X: Set, tau: Set) -> bool:
    """ Checks if tau could be topology of X (equivalent to nested depth of tau is X's + 1) """
    if tau.binding_quantity == X.binding_quantity:
        return tau.nested_depth == X.nested_depth + 1

    return tau.binding_quantity == (X,) and tau.nested_depth == 1

def continuous(f: Function, topology_in: Set, topology_out: Set) -> Statement:
    """ Returns the statement that a function f is continous """
    f_inv, inv_statement = inverse(f)

    U = Set((f.output_set,), Quantor.FORALL)

    # U open
    u_in = Statement(Relation.ELEMENTOF, Statement(Node(U)), Statement(Node(topology_out)))
    # f^-1(U) open
    f_in = Statement(Relation.ELEMENTOF, Statement(Node(f_inv)(Node(U))), Statement(Node(topology_in)))

    return Statement(Relation.IMPLIES, u_in, f_in)


# UNORDERED TUPLES FOR DEFINITION UNFOLDING
DEFINITIONS: List[Tuple[Statement | Statement]] = []