from typing import List, Dict, Tuple
from Statement import Statement


def knuth_bendix_algorithm(axiom_system: List[Tuple[Statement, Statement]]) -> List[Tuple[Statement, Statement]]:
    """ Applies Knuth's Bendix algorithm to an axiom system where equality is given between the statement and reduces it to a directed, confulent, transformation system such that the rewritting system terminates and gives equivalent results """
    temporary_res = []

    while axiom_system:
        s, t = axiom_system[0]
        # Simplify on the current rule book
        for (statement, reduction) in temporary_res:
            s = s.simplify(statement, reduction)
            t = t.simplify(statement, reduction)

        # Get ordering
        if s.term_order > t.term_order:
           temporary_res.append((s, t))
        else:
            temporary_res.append((t, s))

        # Generate critical pairs
        for i, rule1 in enumerate(temporary_res[:-1]):
            for rule2 in temporary_res[(i + 1):]:
                axiom_system.extend(_get_critical_pairs_for_rules(rule1, rule2))

    return temporary_res


def _get_critical_pairs_for_rules(rule1: Tuple[Statement, Statement], rule2: Tuple[Statement, Statement]) -> List[Tuple[Statement, Statement]]:
    """ Generates all the critical pairs within two rules by comparing their leftside structure """
    # TODO: Simplify applied states even more using other rules
    critical_pairs = []
    for rule2_application in rule1[0].simplify(rule2[0], rule2[1]):
        if rule1[1] != rule2_application:
            critical_pairs.append((rule1[1], rule2_application))

    for rule1_application in rule2[0].simplify(rule1[0], rule1[1]):
        if rule2[1] != rule1_application:
            critical_pairs.append((rule2[1], rule1_application))

    return critical_pairs

