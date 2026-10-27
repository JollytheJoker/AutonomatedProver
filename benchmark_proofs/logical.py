from typing import List, Tuple
from Statement import Statement, LogicalOperation, MetaObject, Bool


P = Statement(MetaObject(Statement, name='P'))
Q = Statement(MetaObject(Statement, name='Q'))
R = Statement(MetaObject(Statement, name='R'))
S = Statement(MetaObject(Statement, name='S'))

# TODO: Canonicalize

# P \land Q \implies P
Statement(LogicalOperation.IMPLIES, Statement(LogicalOperation.AND, P, Q), P)

# P \land Q \implies Q
Statement(LogicalOperation.IMPLIES, Statement(LogicalOperation.AND, P, Q), Q)

# P \implies (P \lor Q)
Statement(LogicalOperation.IMPLIES, P, Statement(LogicalOperation.OR, P, Q))

# ((P \implies Q) \land P) \implies Q
partial = Statement(LogicalOperation.AND, Statement(LogicalOperation.IMPLIES, P, Q), P)
Statement(LogicalOperation.IMPLIES, partial, Q)

# ((P \implies Q) \land not Q) \implies not P
partial = Statement(LogicalOperation.AND, Statement(LogicalOperation.IMPLIES, P, Q), Q.negation)
Statement(LogicalOperation.IMPLIES, partial, P.negation)

# ((P \implies Q) \land (Q \implies R)) \implies (P \implies R)
lhs = Statement(LogicalOperation.AND, Statement(LogicalOperation.IMPLIES, P, Q), Statement(LogicalOperation.IMPLIES, Q, R))
rhs = Statement(LogicalOperation.IMPLIES, P, R)
Statement(LogicalOperation.IMPLIES, lhs, rhs)

# (P \implies Q) <=> (not Q \implies not P)
Statement(LogicalOperation.DOUBLEARROW, Statement(LogicalOperation.IMPLIES, P, Q), Statement(LogicalOperation.IMPLIES, Q.negation, P.negation))

# (P \implies Q) <=> (not P \lor Q)
Statement(LogicalOperation.DOUBLEARROW, Statement(LogicalOperation.IMPLIES, P, Q), Statement(LogicalOperation.OR, P.negation, Q))

# (P <=> Q) <=> ((P \implies Q) \land (Q \implies P))
Statement(LogicalOperation.DOUBLEARROW,
          Statement(LogicalOperation.DOUBLEARROW, P, Q),
          Statement(LogicalOperation.AND, Statement(LogicalOperation.IMPLIES, P, Q), Statement(LogicalOperation.IMPLIES, Q, P)))

# P \land Q <=> Q \land P TODO
Statement(LogicalOperation.DOUBLEARROW,
          Statement(LogicalOperation.AND, P, Q),
          Statement(LogicalOperation.AND, Q, P))

# P \lor Q <=> Q \lor P
Statement(LogicalOperation.DOUBLEARROW,
          Statement(LogicalOperation.OR, P, Q),
          Statement(LogicalOperation.OR, Q, P))

# (P xor Q) xor (P xor Q)
Statement(LogicalOperation.XOR,
          Statement(LogicalOperation.XOR, P, Q),
          Statement(LogicalOperation.XOR, P, Q))

# P \land (Q xor Q)
Statement(LogicalOperation.AND, P, Statement(LogicalOperation.XOR, Q, Q))

# (P xor Q) \land (R xor S) = (P \land R) xor (P \land S) xor (Q \land R) xor (Q \land S)
Statement(LogicalOperation.EQUAL,
          Statement(LogicalOperation.AND, Statement(LogicalOperation.XOR, P, Q), Statement(LogicalOperation.XOR, R, S)),
          Statement(LogicalOperation.XOR,
                    Statement(LogicalOperation.XOR, Statement(LogicalOperation.AND, P, R), Statement(LogicalOperation.AND, P, S)),
                    Statement(LogicalOperation.XOR, Statement(LogicalOperation.AND, Q, R), Statement(LogicalOperation.AND, Q, S))))

# (P \land Q) \land (P xor Q)
Statement(LogicalOperation.AND,
          Statement(LogicalOperation.AND, P, Q),
          Statement(LogicalOperation.XOR, P, Q))


