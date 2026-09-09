from typing import List, Tuple, Set
from Statement import Statement


def knuth_bendix_algorithm(axiom_system: List[Tuple[Statement, Statement]]) -> List[Tuple[Statement, Statement]]:
    """ Applies Knuth's Bendix algorithm to an axiom system where equality is given between the statement and reduces it to a directed, confulent, transformation system such that the rewritting system terminates and gives equivalent results """
    temporary_res = []

    # TODO: Switch from hash solution to other, still efficient one. Alternatively fix hash issue for nodes
    seen: Set[Tuple[Statement, Statement]] = set()
    processing: Set[Tuple[Statement, Statement]] = set(axiom_system)

    while axiom_system:
        s, t = axiom_system[0]
        axiom_system.pop(0)

        processing.remove((s, t))
        seen.add((s, t))

        # Simplify on the current rule book
        simplify_fully(s, temporary_res)
        simplify_fully(t, temporary_res)

        # Get ordering
        comparison = kbo_compare(s, t)
        match comparison:
            case 1:
                new_rule = (s, t)
                temporary_res.append((s, t))
            case -1:
                new_rule = (t, s)
                temporary_res.append((t, s))
            case _:
                raise Exception(f'{str(s)}={str(t)} on KBO-Basis')


        # Generate critical pairs
        for rule in temporary_res[:-1]:
            extention = _get_critical_pairs_for_rules(rule, new_rule)

            # Simplify critical pairs on the current system
            critical_pairs = []
            for p1, p2 in extention:
                p1 = simplify_fully(p1, temporary_res)
                p2 = simplify_fully(p2, temporary_res)
                # Only add if the statements in reduced form are unequal
                if p1 != p2 and (p1, p2) not in processing:
                    critical_pairs.append((p1, p2))
                    processing.add((p1, p2))

            axiom_system.extend(critical_pairs)

    # Clear redudantent rules by simplifing
    final_rule_system = []

    for i, (r1, r2) in enumerate(temporary_res):
        r1 = simplify_fully(r1, temporary_res[:i] + temporary_res[i + 1:])
        r2 = simplify_fully(r2, temporary_res[:i] + temporary_res[i + 1:])

        if r1 == r2:
            continue

        for old_r1, old_r2 in final_rule_system:
            if old_r1 == r1:
                if old_r2 == r2:
                    break

                raise Exception(f"System is not confluent: {str(r1)}->{str(r2)} and {str(old_r1)}->{str(old_r2)}")
        else:
            final_rule_system.append((r1, r2))

    return final_rule_system


def _get_critical_pairs_for_rules(rule1: Tuple[Statement, Statement], rule2: Tuple[Statement, Statement]) -> List[Tuple[Statement, Statement]]:
    """ Generates all the critical pairs within two rules by comparing their leftside structure """
    critical_pairs = []
    for rule2_application in rule1[0].simplify(rule2[0], rule2[1]):
        if rule1[1] != rule2_application:
            critical_pairs.append((rule1[1], rule2_application))

    for rule1_application in rule2[0].simplify(rule1[0], rule1[1]):
        if rule2[1] != rule1_application:
            critical_pairs.append((rule2[1], rule1_application))

    return critical_pairs

def simplify_statement_on_system(s: Statement, system: List[Tuple[Statement, Statement]]):
    for (statement, reduction) in system:
        # Since our temporary axiom system should not have any critical pairs, we only generate one simplification or the choice doesn't matter, since the convergence is all the same
        try:
            s_new = next(s.simplify(statement, reduction))
            # Programm only simplifies if new is of smaller kbo
            if kbo_compare(s, s_new) == 1:
                s = s_new
        except StopIteration:
            # Leave s the same since no simplification was found
            pass

    return s

def simplify_fully(s: Statement, system: List[Tuple[Statement, Statement]]):
    s_old = s
    while (s_new := simplify_statement_on_system(s_old, system)) != s_old:
        s_old = s_new
    return s_old


def kbo_compare(lhs: Statement, rhs: Statement):
    if lhs.kbo_weight != rhs.kbo_weight:
        return 1 if lhs.kbo_weight > rhs.kbo_weight else -1

    if lhs.kbo_precedence != rhs.kbo_precedence:
        return 1 if lhs.kbo_precedence > rhs.kbo_precedence else -1

    if lhs.child_left and rhs.child_left:
        child_compare = kbo_compare(lhs.child_left, rhs.child_left)
        if child_compare != 0:
            return child_compare

    if lhs.child_right and rhs.child_right:
        return kbo_compare(lhs.child_right, rhs.child_right)

    return 0
