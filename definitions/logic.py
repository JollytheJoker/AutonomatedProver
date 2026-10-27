import copy
from copy import replace
from typing import List, Tuple
from Prover import find_implicit_simplifications_from_axioms_definitions
from Statement import Statement, LogicalOperation, MetaObject, Bool, create_shadow_version, generate_ac_invariants, \
    OPERATION_PROPERTIES, OperationProperties

"""
---------- LOGICAL DEFINITIONS ---------- 
Explicitly implemented: and, xor, not, forall, exists
"""
logical_definitions: List[Tuple[Statement, Statement]] = []

P = Statement(MetaObject(Statement, name='P'))
Q = Statement(MetaObject(Statement, name='Q'))

# P \implies Q \equiv \not P xor (P \land Q)
rhs = Statement(LogicalOperation.XOR, P.negation, Statement(LogicalOperation.AND, P, Q))
logical_definitions.append((Statement(LogicalOperation.IMPLIES, P, Q), rhs))

# P \impliedby Q \equiv \not Q xor (Q \and P)
rhs = Statement(LogicalOperation.XOR, Q.negation, Statement(LogicalOperation.AND, Q, P))
logical_definitions.append((Statement(LogicalOperation.IMPLIEDBY, P, Q), rhs))

# P \doulbearrow Q \equiv (P \land Q) xor (not P \land not Q)
rhs = Statement(LogicalOperation.XOR, Statement(LogicalOperation.AND, P, Q), Statement(LogicalOperation.AND, P.negation, Q.negation))
logical_definitions.append((Statement(LogicalOperation.DOUBLEARROW, P, Q), rhs))

# P \or Q \equiv (P xor Q) xor (P \land Q)
rhs = Statement(LogicalOperation.XOR, Statement(LogicalOperation.XOR, P, Q), Statement(LogicalOperation.AND, P, Q))
logical_definitions.append((Statement(LogicalOperation.OR, P, Q), rhs))

"""
---------- LOGICAL AXIOMS ----------
Axioms are used for simplifications on terms
Axioms on Operations: and, xor, not (should give confluent system)
Explicitly implemented: 
not forall P(x) = exists not P(x) (vise versa)
AC-canonicalization (Associativity, Commutativity)
"""
logical_axioms: List[Tuple[Statement, Statement]] = []

# Define 3 placeholders
P = Statement(MetaObject(Statement, name='P'))
Q = Statement(MetaObject(Statement, name='Q'))
R = Statement(MetaObject(Statement, name='R'))

# P xor false = P
lhs = Statement(LogicalOperation.XOR, P, Statement(Bool.FALSE))
logical_axioms.append((lhs.canonical, P))

# P xor P = false
lhs = Statement(LogicalOperation.XOR, P, P)
logical_axioms.append((lhs.canonical, Statement(Bool.FALSE)))

# P xor not P = true
lhs = Statement(LogicalOperation.XOR, P, P.negation)
logical_axioms.append((lhs.canonical, Statement(Bool.TRUE)))

# P and true = P
lhs = Statement(LogicalOperation.AND, P, Statement(Bool.TRUE))
logical_axioms.append((lhs.canonical, P))

# P and false = false
lhs = Statement(LogicalOperation.AND, P, Statement(Bool.FALSE))
logical_axioms.append((lhs.canonical, Statement(Bool.FALSE)))

# P and P = P
lhs = Statement(LogicalOperation.AND, P, P)
logical_axioms.append((lhs.canonical, P))

# P and not P = false
lhs = Statement(LogicalOperation.AND, P, P.negation)
logical_axioms.append((lhs.canonical, Statement(Bool.FALSE)))

# Distributive
# (P xor Q) and R \equiv (P and R) xor (Q and R)
lhs = Statement(LogicalOperation.AND, Statement(LogicalOperation.XOR, P, Q), R)
rhs = Statement(LogicalOperation.XOR, Statement(LogicalOperation.AND, P, R), Statement(LogicalOperation.AND, Q, R))
logical_axioms.append((lhs.canonical, rhs.canonical))


"""
---------- LOGICAL IMPLICATIONS ----------
Results from axioms on (xor, and, not) for all defined operations
"""
implicit_axioms = []
mapped_s = set()
for i in range(len(logical_definitions)):
    # Check for operation properties
    operation = logical_definitions[i][0]
    definition = logical_definitions[i][1]

    # Commutativity
    commutative = False

    original = definition.canonical
    switched = definition.replace_with_list([
                                (operation.child_left, operation.child_right),
                                (operation.child_right, operation.child_left),
                                (operation.child_left.negation, operation.child_right.negation),
                                (operation.child_right.negation, operation.child_left.negation)
    ])
    switched = switched.canonical

    if switched == original:
        print(f"{operation} is commutative")
        commutative = True

    # Associativity
    associative = False
    '''parent_operation, parent_definition = create_shadow_version(operation, definition)
    child_node, child_definition = create_shadow_version(operation, definition)

    # Version 1 (child_node in left of parent)
    version1 = parent_definition.replace_with_list([
        (parent_operation.child_left, child_definition),
        (parent_operation.child_left.negation, child_definition.negation)
    ])
    version1 = version1

    # Version 2 (lots of substitutions)
    version2_child = child_definition.replace_with_list([
        (child_node.child_left, child_node.child_right),
        (child_node.child_right, parent_operation.child_right),
        (child_node.child_left.negation, child_node.child_right.negation),
        (child_node.child_right.negation, parent_operation.child_right.negation)
    ])
    version2_child = version2_child

    version2 = parent_definition.replace_with_list([
        (parent_operation.child_left, child_node.child_left),
        (parent_operation.child_right, version2_child),
        (parent_operation.child_left.negation, child_node.child_left.negation),
        (parent_operation.child_right.negation, version2_child.negation)
    ])
    version2 = version2

    print()
    print("Parent_operation: ", parent_operation)
    print("child_node: ", child_node)
    print("Version 1: ", version1)
    print(parent_operation.replace_with_list([
        (parent_operation.child_left, child_node),
        (parent_operation.child_left.negation, child_node.negation)
    ]).canonical)
    print("Version 2: ", version2)
    child2 = child_node.replace_with_list([
        (child_node.child_left, child_node.child_right),
        (child_node.child_right, parent_operation.child_right),
        (child_node.child_left.negation, child_node.child_right.negation),
        (child_node.child_right.negation, parent_operation.child_right.negation)
    ])
    print(parent_operation.replace_with_list([
        (parent_operation.child_left, child_node.child_left),
        (parent_operation.child_right, child2),
        (parent_operation.child_left.negation, child_node.child_left.negation),
        (parent_operation.child_right.negation, child2.negation)
    ]).canonical)'''

    OPERATION_PROPERTIES[operation.node_function] = OperationProperties(associative=associative, commutative=commutative)

    for j in range(len(logical_axioms)):
        shadow_def = create_shadow_version(logical_definitions[i][0], logical_definitions[i][1])
        shadow_ax = create_shadow_version(logical_axioms[j][0], logical_axioms[j][1])

        for s, t in find_implicit_simplifications_from_axioms_definitions(shadow_def[0], shadow_def[1], shadow_ax[0], shadow_ax[1]):
            if s.nameless_hash not in mapped_s:
                mapped_s.add(s.nameless_hash)
                implicit_axioms.append((s, t))

print(f"Found {len(implicit_axioms)} direct implications from axioms")
for s, t in implicit_axioms:
    print(f"{s}->{t}")

