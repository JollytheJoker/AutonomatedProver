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
        Returns the reduced quantor of both (e.g., min (for all, exists) => exists).
        If none of the quantors is for all, it will return None, since we can't garentee a match
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
        _ID_COUNTER[key] = 1
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
    binding_quantity: Tuple[Union['ElementrySet', 'Set', 'PowerSet', 'FunctionSet'], ...] = field(default_factory=tuple)
    mathematical_quantity: FrozenSet = field(default_factory=frozenset)
    quantor: Quantor = Quantor.DEFINE
    obj_id: int = field(default=0)
    assosiation: str = ''

    def __post_init__(self):
        if self.obj_id == 0:
            generated_id = _generate_id(self.binding_quantity, self.mathematical_quantity, self.quantor)
            object.__setattr__(self, 'obj_id', generated_id)

    def toTuple(self) -> Tuple:
        """
        :return: Tuple of the objects abstract representation (type, binding_quantity, mathematical_quantity, quantor, id).
        """
        return type(self), self.binding_quantity, self.mathematical_quantity, self.quantor, self.obj_id

    def __eq__(self, other: Object) -> bool:
        if type(self) != type(other):
            return False
        return self.binding_quantity == other.binding_quantity and self.mathematical_quantity == other.mathematical_quantity and self.quantor == other.quantor and self.obj_id == other.obj_id


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

    def __len__(self):
        return 1

@dataclass(frozen=True)
class Set(Object):
    """A set, which is contained in another set or in the cross-product of other sets"""

    def __post_init__(self):
        super().__post_init__()
        if len(self.binding_quantity) == 0:
            raise Exception("Must give at least one binding quantity")

    def __repr__(self):
        return f'(M, {self.binding_quantity}, {(repr(quantity) for quantity in self.mathematical_quantity)}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.assosiation:
            return f'{self.assosiation}'
        return f'{self.quantor} Set_{self.obj_id} which is subset of {str(self.binding_quantity[0]) if len(self.binding_quantity) == 1 else "x".join(str(b) for b in self.binding_quantity)}'

    def __len__(self):
        return len(self.binding_quantity)

@dataclass(frozen=True)
class PowerSet(Object):
    """A powerSet is a set that contains every subset of a set"""
    nested_depth: int = 0

    def __post_init__(self):
        super().__post_init__()
        if len(self.binding_quantity) == 0:
            raise Exception("Must give at least one binding quantity")
        if self.nested_depth == 0:
            object.__setattr__(self, 'nested_depth', max(s.nested_depth if isinstance(s, PowerSet) else 0 for s in self.binding_quantity) + 1)

    def __repr__(self):
        return f'(P, {self.binding_quantity}, {(repr(quantity) for quantity in self.mathematical_quantity)}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.assosiation:
            return self.assosiation
        return f'{self.quantor} PowerSet_{self.obj_id} of {str(self.binding_quantity[0]) if len(self.binding_quantity) == 1 else "x".join(str(b) for b in self.binding_quantity)}'

    def __len__(self):
        return 1

@dataclass(frozen=True)
class FunctionSet(Object):
    """A function set is a set that contains every possible mapping from set A to set B"""

    def __post_init__(self):
        super().__post_init__()
        if len(self.binding_quantity) != 2:
            raise Exception("Must give at exactly two binding quantity, one output and one input set")

    def __repr__(self):
        return f'(FS, {self.binding_quantity}, {(repr(quantity) for quantity in self.mathematical_quantity)}, {self.quantor}, {self.obj_id})'

    def __str__(self):
        if self.assosiation:
            return self.assosiation
        return f'{self.quantor} FunctionSet_{self.obj_id} of functions from {str(self.binding_quantity[0])} to {str(self.binding_quantity[1])}'

    def __len__(self):
        return 1

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

