from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Union, FrozenSet, Dict


class Quantor(Enum):
    FORALL = r'\forall'
    EXISTS = r'\exists'
    DEFINE = r'D'

    def min(self, other: 'Quantor') -> 'Quantor' | None:
        """
        Returns the reduced quantor of both (e.g. min(for all, exists) => exists).
        If none of the quantors is for all it will return None, since we can't garentee a match
        """
        if self == Quantor.FORALL and other == Quantor.FORALL:
            return Quantor.FORALL
        if (self == Quantor.EXISTS or self == Quantor.DEFINE) and (other == Quantor.EXISTS or other == Quantor.DEFINE):
            return None
        return self if other == Quantor.FORALL else other


_ID_COUNTER: Dict[Tuple[Tuple[Object, ...], FrozenSet, Quantor], int] = {}
def _generate_id(binding: Tuple[Object, ...], math_cond: FrozenSet, quantor: Quantor) -> int:
    key = (binding, math_cond, quantor)
    if key not in _ID_COUNTER:
        _ID_COUNTER[key] = 0
    else:
        _ID_COUNTER[key] += 1
    return _ID_COUNTER[key]


@dataclass(frozen=True)
class Object:
    """Represents a mathematical object in the discourse space.

    Attributes:
        binding_quantity: Set of bound sets/spaces (B).
        mathematical_quantity: Set/List of mathematical conditions (M).
        quantor: Logical quantifier state (Q).
        obj_id: Unique identifier (id).
    """
    binding_quantity: Tuple[Union['ElementrySet', 'Set', 'ConcatenatedSet'], ...] = field(default_factory=tuple)
    mathematical_quantity: FrozenSet = field(default_factory=frozenset)
    quantor: Quantor = Quantor.DEFINE
    obj_id: int = field(default=0, init=False)
    assosiation: str = ''

    def __post_init__(self):
        generated_id = _generate_id(self.binding_quantity, self.mathematical_quantity, self.quantor)
        object.__setattr__(self, 'obj_id', generated_id)

    def toTuple(self) -> Tuple:
        """
        :return: Tuple of the objects abstract representation (type, binding_quantity, mathematical_quantity, quantor, id).
        """
        return type(self), self.binding_quantity, self.mathematical_quantity, self.quantor, self.obj_id


@dataclass(frozen=True)
class ElementrySet(Object):
    """An elementary base set with empty binding requirements."""
    binding_quantity = tuple()
    quantor = Quantor.DEFINE

    def __repr__(self):
        return f'(U, (), {(repr(quantity) for quantity in self.mathematical_quantity)}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.assosiation:
            return f'{self.assosiation}'
        return f'Urmenge_{self.obj_id}'


@dataclass(frozen=True)
class Set(Object):
    """A set, which is contained in another set, which binding quantites must have size 1"""

    def __post_init__(self):
        super().__post_init__()
        if len(self.binding_quantity) != 1:
            raise Exception("Must give exactly one binding quantity, one upper set")

    def __repr__(self):
        return f'(M, {self.binding_quantity}, {(repr(quantity) for quantity in self.mathematical_quantity)}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.assosiation:
            return f'{self.assosiation}'
        return f'{self.quantor} Set_{self.obj_id} which is subset of {str(self.binding_quantity[0])}'


@dataclass(frozen=True)
class ConcatenatedSet(Object):
    """A set that creates the cross product of multiple sets. It's binding quantities thus have size > 1"""
    def __post_init__(self):
        super().__post_init__()
        if len(self.binding_quantity) < 2:
            raise Exception("Concatenated set must include at least 2 elements in binding quantaties.")
        
    def __repr__(self):
        return f'(C, {self.binding_quantity}, {(repr(quantity) for quantity in self.mathematical_quantity)}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.assosiation:
            return self.assosiation
        return f'{self.quantor} {'x'.join(str(s) for s in self.binding_quantity)}'

    def __len__(self) -> int:
        return len(self.binding_quantity)


@dataclass(frozen=True)
class Variable(Object):
    """A base variable that has exactly one value in its binding quantity"""

    def __post_init__(self):
        super().__post_init__()
        if len(self.binding_quantity) != 1:
            raise Exception("Must give exactly one binding quantity, one according set")

    def __repr__(self):
        return f'(V, {self.binding_quantity}, {(repr(quantity) for quantity in self.mathematical_quantity)}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.assosiation:
            return f'{self.assosiation}'
        return f'{self.quantor} Variable_{self.obj_id} which lies in {str(self.binding_quantity[0])}'


@dataclass(frozen=True)
class Function(Object):
    """A base function that has exactly two values in its binding quantity an in- and output set"""

    def __post_init__(self):
        super().__post_init__()
        if len(self.binding_quantity) != 2:
            raise Exception("Must give exactly two binding quantities, one input and one output")

    def __repr__(self):
        return f'(F, {self.binding_quantity}, {(repr(quantity) for quantity in self.mathematical_quantity)}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.assosiation:
            return f'{self.assosiation}'
        return f'{self.quantor} Function_{self.obj_id}: {str(self.binding_quantity[0])} -> {str(self.binding_quantity[1])}'

