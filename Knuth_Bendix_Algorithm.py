from typing import List, Tuple, Set
from Statement import Statement, kbo_compare, create_shadow_version


def knuth_bendix_algorithm(axiom_system: List[Tuple[Statement, Statement]]) -> List[Tuple[Statement, Statement]]:
    """ Applies Knuth's Bendix algorithm to an axiom system where equality is given between the statement and reduces it to a directed, confulent, transformation system such that the rewritting system terminates and gives equivalent results """
    temporary_res = []

    # TODO: Switch from hash solution to other, still efficient one. Alternatively fix hash issue for nodes
    seen: Set[Tuple[Statement, Statement]] = set()
    processing: Set[Tuple[Statement, Statement]] = set(axiom_system)

    while axiom_system:
        s, t = axiom_system[0]
        axiom_system.pop(0)

        try:
            processing.remove((s, t))
            seen.add((s, t))
        except KeyError:
            pass

        # Simplify on the current rule book
        simplify_fully(s, temporary_res)
        simplify_fully(t, temporary_res)

        if s == t:
            continue

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


def _get_critical_pairs_for_rules(rule1: Tuple[Statement, Statement], rule2: Tuple[Statement, Statement]) -> List[
    Tuple[Statement, Statement]]:
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


def reducde_statement_modulo_directed_axioms(statement: Statement, system: List[Tuple[Statement, Statement]]):
    s_old = statement
    s_new = statement

    def simplify(_s, _t):
        # Since a system is confluent we can just take the next simplification
        try:
            return next(s_new.simplify(_s, _t, allow_self_node_size_increase=False, allow_bool_val_replacement=2))
        except StopIteration:
            return s_new

    for s, t in system:
        s_new = simplify(*create_shadow_version(s, t))

    while s_new != s_old:
        s_old = s_new

        for s, t in system:
            s_new = simplify(*create_shadow_version(s, t))

    return s_new


def reducde_statement_modulo_directed_axioms_return_replacement_list(statement: Statement, system: List[Tuple[Statement, Statement]], allow_boolean_replacement: bool = True) -> Tuple[Statement, List[Tuple[Statement, Statement]]]:
    s_old = statement
    s_new = statement
    replacement_list = []

    def simplify(_s, _t):
        # Since a system is confluent we can just take the next simplification
        try:
            return next(s_new.simplify_return_replacement_list(_s, _t, allow_self_node_size_increase=False, allow_bool_val_replacement=2 if allow_boolean_replacement else 0))
        except StopIteration:
            return s_new, []

    for s, t in system:
        s_new, replacement_list_tmp = simplify(*create_shadow_version(s, t))
        replacement_list.extend(replacement_list_tmp)

    while s_new != s_old:
        s_old = s_new

        for s, t in system:
            s_new, replacement_list_tmp = simplify(*create_shadow_version(s, t))
            replacement_list.extend(replacement_list_tmp)

    # Fix replacement list
    '''fixed_replacement_list = []
    for s, t in replacement_list:
        t_prev = t
        t_new = t.replace_with_list(replacement_list)

        while t_prev != t_new:
            t_prev = t_new
            t_new = t_new.replace_with_list(replacement_list)

        if t != t_new:
            t_red, rep = reducde_statement_modulo_directed_axioms_return_replacement_list(t_new, system, False)
            fixed_replacement_list.append((s, t_red.reverse_replace(rep)))
        else:
            fixed_replacement_list.append((s, t))'''

    return s_new, replacement_list
