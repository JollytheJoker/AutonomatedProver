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

    def __call__(self, other: Node) -> Generator[Node]:
        for res in other.primitive_contains(self.expression1):
            mapping, valid = res.get_mappings_dict_for_replacement(other)
            if not valid:
                continue
            yield self.expression2.remap_objects(mapping)

    def apply_inverse(self, other: Node) -> Generator[Node]:
        """Inverse direction"""
        for res, parent_res in other.primitive_contains(self.expression2):
            mapping, valid = self.expression2.get_mappings_dict_for_replacement(res)
            if not valid:
                continue
            final_sub_expression = self.expression1.remap_objects(mapping)
            # Reorder final_sub_expression into original tree
            if parent_res is None:
                yield final_sub_expression
            else:
                parent_copy = parent_res.__copy__()
                parent_copy.child_nodes = [final_sub_expression if child == res else child for child in parent_res.child_nodes]
                yield parent_copy
