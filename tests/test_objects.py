import pytest
from MObject import Set, Function, Quantor


def test_object_creation():
    """Tests if all objects are created correctly"""
    # Sets
    x = Set(association="X", binding_quantity=tuple())
    a = Set(association="A", binding_quantity=(x,))
    assert a.binding_quantity == (x,)

    # Variables
    v1 = Set(association="x", binding_quantity=(x,), nested_depth=0)
    assert v1.binding_quantity == (x,)
    with pytest.raises(Exception):
        Set(binding_quantity=(), nested_depth=0)

    # Power sets
    p1 = Set(binding_quantity=(x, ), nested_depth=1)
    assert p1.nested_depth == 1
    with pytest.raises(Exception):
        Set(binding_quantity=tuple(), nested_depth=2, quantor=Quantor.DEFINE)

    # Functions
    f1 = Function(association="f", binding_quantity=(x, x))
    assert f1.binding_quantity == (x, x)
    with pytest.raises(Exception):
        Function(binding_quantity=())

    with pytest.raises(Exception):
        Function(binding_quantity=(x,))


def test_id_generation_determinism():
    """Tests if objects with the same signature have different ids"""
    s1 = Set(binding_quantity=())
    s2 = Set(binding_quantity=())

    assert s1.obj_id != s2.obj_id