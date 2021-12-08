# interp.py
#


from compared_py_to_wasm.models.model import *

from collections import ChainMap

class Context:
    def __init__(self):
        self.env = ChainMap()          # Storage of variables
        self.has_main = False

        
valid_types = { 'int', 'float', 'char', 'bool' }


def interpret_program(model):
    context = Context()
    ...
    return


def interpret(node, context, next):
    if isinstance(node, Integer):
        return lambda: next(('int', int(node.value)))


def interpret_lhs(node, value, context, next):
    if isinstance(node, Name):
        decl = context.lookup(node.value)


if __name__ == '__main__':
    pass

    

