from __future__ import annotations
from typing import Generator, Dict
from ExpressionTree import Node
from dataclasses import dataclass, field, replace
from enum import Enum


class Relation(Enum):
    SUBSET = r'\subseteq'
    EQUAL = '='
    LEQ = '<='
    GEQ = '>='


@dataclass
class Statement:
    expression1: Node
    expression2: Node
    relation: Relation

    def __call__(self, other: Node, print_trace: bool = False) -> Generator[Node]:
        if print_trace: print(f"Checking {str(self)}({other})")
        for res, parent_res in other.primitive_contains(self.expression1, print_trace=print_trace):
            if print_trace: print(f"Checking subtree {res}")
            mapping, valid = self.expression1.get_mappings_dict_for_replacement(res)
            if not valid:
                continue
            final_sub_expression = self.expression2.remap_objects(mapping)
            if print_trace: print(f"Remapped subtree to {final_sub_expression}")
            # Reorder final_sub_expression into original tree
            if parent_res is None:
                if print_trace: print("Subtree is final-tree")
                yield final_sub_expression
            else:
                new_child_nodes = []
                for child_chain in parent_res.child_nodes:
                    new_chain = []
                    for child_node, weight in child_chain:
                        if child_node == res:
                            new_chain.append((final_sub_expression, weight))
                        else:
                            new_chain.append((child_node, weight))
                    new_child_nodes.append(new_chain)

                parent_copy = Node(math_object=parent_res.math_object, child_nodes=new_child_nodes)

                if print_trace: print(f"Reordered subtree into main tree to {parent_copy}")
                yield parent_copy
        else:
            if print_trace: print("Done \n")

    def apply_inverse(self, other: Node, print_trace: bool = False) -> Generator[Node]:
        """Inverse direction"""
        if print_trace: print(f"Checking {self}^-1({other})")
        for res, parent_res in other.primitive_contains(self.expression2, print_trace=print_trace):
            if print_trace: print(f"Checking subtree {res}")
            mapping, valid = self.expression2.get_mappings_dict_for_replacement(res, print_trace=print_trace)
            if not valid:
                continue
            final_sub_expression = self.expression1.remap_objects(mapping)
            if print_trace: print(f"Remapped subtree to {final_sub_expression}")
            # Reorder final_sub_expression into original tree
            if parent_res is None:
                if print_trace: print("Subtree is final-tree")
                yield final_sub_expression
            else:
                new_child_nodes = []
                for child_chain in parent_res.child_nodes:
                    new_chain = []
                    for child_node, weight in child_chain:
                        if child_node == res:
                            new_chain.append((final_sub_expression, weight))
                        else:
                            new_chain.append((child_node, weight))
                    new_child_nodes.append(new_chain)

                parent_copy = Node(math_object=parent_res.math_object, child_nodes=new_child_nodes)

                if print_trace: print(f"Reordered subtree into main tree to {parent_copy}")
                yield parent_copy
        else:
            if print_trace: print("Done \n")

    def __str__(self):
        return f'{str(self.expression1)} {self.relation} {self.expression2}'

