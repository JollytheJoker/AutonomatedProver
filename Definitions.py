from MObject import Set, Function, Quantor


# GENERAL GLOBAL DEFINITIONS
definitions = {
    "integers": Set(association='N'),
    "reels": Set(association='R')
}

# Helper
_helper = {
    "NxN": Set(quantor=Quantor.DEFINE, binding_quantity=(definitions["integers"], definitions["integers"]), association='NxN'),
}

operations = {
    "add": Function(quantor=Quantor.DEFINE, binding_quantity=(_helper["NxN"], definitions["integers"]), association='+'),
    "sub": Function(quantor=Quantor.DEFINE, binding_quantity=(_helper["NxN"], definitions["integers"]), association='-'),
    "mul": Function(quantor=Quantor.DEFINE, binding_quantity=(_helper["NxN"], definitions["integers"]), association='*')
}

# TODO: Implement Successor methode and axioms for addition
