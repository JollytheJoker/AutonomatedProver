import pytest
from MObject import ElementrySet, Set, Variable, Function, Quantor


def test_object_createion():
    """Tests if all objects are created correctly"""
    # Elementry Sets
    u1 = ElementrySet(assosiation="X")
    assert u1.assosiation == "X"
    assert u1.binding_quantity == ()
    assert str(u1) == "X"
    u2 = ElementrySet(assosiation="Y")

    # Sets
    s1 = Set(assosiation="A", binding_quantity=(u1,), quantor=Quantor.DEFINE)
    assert s1.binding_quantity == (u1,)
    with pytest.raises(ValueError):
        Set(binding_quantity=())

    with pytest.raises(ValueError):
        Set(binding_quantity=(u1, u1))

    # Variables
    v1 = Variable(assosiation="x", binding_quantity=(u1,), quantor=Quantor.DEFINE)
    assert v1.binding_quantity == (u1,)
    with pytest.raises(ValueError):
        Variable(binding_quantity=())

    with pytest.raises(ValueError):
        Variable(binding_quantity=(u1, u1))

    # Functions
    f1 = Function(assosiation="f", binding_quantity=(u1, u2), quantor=Quantor.DEFINE)
    assert f1.binding_quantity == (u1, u2)
    with pytest.raises(ValueError):
        Function(binding_quantity=())

    with pytest.raises(ValueError):
        Function(binding_quantity=(u1,))


def test_id_generation_determinism():
    """Tests if objects with same signature have different ids"""
    u1 = ElementrySet()
    u2 = ElementrySet()

    assert u2.obj_id == u1.obj_id + 1