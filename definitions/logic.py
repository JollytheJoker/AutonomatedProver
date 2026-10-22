from typing import List, Tuple
from Statement import Statement, LogicalOperation, MetaObject, Bool


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

# (P and Q) xor R \equiv (P xor R) and (Q xor R)
lhs = Statement(LogicalOperation.XOR, Statement(LogicalOperation.AND, P, Q), R)
rhs = Statement(LogicalOperation.AND, Statement(LogicalOperation.XOR, P, R), Statement(LogicalOperation.XOR, Q, R))
logical_axioms.append((lhs.canonical, rhs.canonical))


"""
---------- LOGICAL IMPLICATIONS ----------
Results from axioms on (xor, and, not) for all defined operations
"""
