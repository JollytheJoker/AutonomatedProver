from dataclasses import replace
from GraphBuilder import GraphBuilder
from Prover import Prover
from MObject import Function, Set, Quantor, Object
from CommonStatements import continuous, DEFINITIONS, topolgy, _is_topology, transitiv, logical_axioms, inverse
from ExpressionTree import Node
from Statement import Relation, LogicalOperation, Bool, Statement, canonicalize_ac
from Knuth_Bendix_Algorithm import reducde_statement_modulo_directed_axioms


def test_transitivity_prove():
    """ Show that ((A => B) & (B => C)) => (A => C) """
    prover = Prover((), transitiv(LogicalOperation.IMPLIES))

    print(prover.prove())


test_transitivity_prove()