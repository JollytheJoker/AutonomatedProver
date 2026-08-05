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
        for res in other.primitive_contains(self.expression1, return_self=False):
            mapping, valid = res.get_mappings_dict_for_replacement(other)
            if not valid:
                continue
            yield self.expression2.remap_objects(mapping)

    def apply_inverse(self, other: Node) -> Generator[Node]:
        """Inverse direction"""
        for res in other.primitive_contains(self.expression2, return_self=False):
            if not "dz" in str(res): breakpoint()
            mapping, valid = res.get_mappings_dict_for_replacement(other)
            if not valid:
                continue
            yield self.expression1.remap_objects(mapping)
