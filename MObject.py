from __future__ import annotations
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import Tuple, Union, Dict


class Quantor(Enum):
    FORALL = r'\forall'
    EXISTS = r'\exists'
    DEFINE = r'D'

    def unified_equal(self, other: 'Quantor') -> bool:
        """ Unifies exsits and define quantor into one 'type' and compares that """
        if self == Quantor.FORALL: return other == Quantor.FORALL
        return other == Quantor.DEFINE or other == Quantor.EXISTS

_ID_COUNTER: Dict[Tuple[Tuple[Object, ...], Quantor], int] = {}
def _generate_id(binding: Tuple[Object, ...], quantor: Quantor) -> int:
    key = (binding, quantor)
    if key not in _ID_COUNTER:
        _ID_COUNTER[key] = 1
    else:
        _ID_COUNTER[key] += 1
    return _ID_COUNTER[key]


@dataclass(frozen=True)
class Object(ABC):
    """Represents a mathematical object in the discourse space.

    Attributes:
        binding_quantity: Set of bound sets/spaces (B).
        quantor: Logical quantifier state (Q).
        obj_id: Unique identifier (id).
        association: Easy to read name.
    """
    binding_quantity: Tuple[Set, ...] = field(default_factory=tuple)
    quantor: Quantor = Quantor.DEFINE
    association: str = ''

    @cached_property
    def obj_id(self) -> Union[int, None]:
        return _generate_id(self.binding_quantity, self.quantor)

    @property
    @abstractmethod
    def as_tuple(self) -> Tuple:
        """ Tuple of the objects abstract representation """
        pass

    def __eq__(self, other: Object) -> bool:
        if type(self) is not type(other):
            return False
        # Only check for id's if any object was defined TODO: Is that really correct?
        if self.quantor == Quantor.DEFINE or other.quantor == Quantor.DEFINE:
            return self.binding_quantity == other.binding_quantity and self.quantor == other.quantor and self.obj_id == other.obj_id
        return self.binding_quantity == other.binding_quantity and self.quantor == other.quantor


@dataclass(frozen=True, eq=False)
class Set(Object):
    """ Mathematical set """
    nested_depth: int = field(default=1)

    def __post_init__(self):
        if self.nested_depth != 1 and not self.binding_quantity:
            raise Exception("Must give binding quantity (as bound) for variable or powerset definition")

    @property
    def as_tuple(self) -> Tuple:
        """ Tuple of the objects abstract representation (type, binding_quantity, nested_depth, quantor, id) """
        return type(self), self.binding_quantity, self.nested_depth, self.quantor, self.obj_id

    def __repr__(self):
        return f'(M, {self.binding_quantity}, {self.nested_depth}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.association:
            return f'{self.association}'
        if self.nested_depth > 0:
            if self.binding_quantity:
                return f'{self.quantor} Set_{self.obj_id} ⊆ {"" if self.nested_depth == 1 else f"P^{self.nested_depth - 1}("}{str(self.binding_quantity[0]) if len(self.binding_quantity) == 1 else "x".join(str(b) for b in self.binding_quantity)}{"" if self.nested_depth == 1 else ")"}'
            return f'{self.quantor} ElementrySet_{self.obj_id}'
        return f'{self.quantor} Variable_{self.obj_id} ∈ {"x".join(str(binding) for binding in self.binding_quantity)}'


@dataclass(frozen=True, eq=False)
class Function(Object):
    """ A base function that has exactly two values in its binding quantity an in- and output set """
    def __post_init__(self):
        if len(self.binding_quantity) != 2:
            raise Exception("Must give exactly two binding quantities, one input and one output")

    @property
    def as_tuple(self) -> Tuple:
        """ Tuple of the objects abstract representation (type, binding_quantity, quantor, id). """
        return type(self), self.binding_quantity, self.quantor, self.obj_id

    def __repr__(self):
        return f'(F, {self.binding_quantity}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.association:
            return f'{self.association}'
        return f'{self.quantor} Function_{self.obj_id}: {str(self.binding_quantity[0])} -> {str(self.binding_quantity[1])}'
