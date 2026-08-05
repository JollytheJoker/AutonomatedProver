from __future__ import annotations
from typing import Generator, Dict

from colorama import colorama_text

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
            if self.expression1 != res:
                continue
            mapping, valid = self.expression1.get_mappings_dict_for_replacement(other)
            if not valid:
                continue
            yield self.expression2.remap_objects(mapping)
