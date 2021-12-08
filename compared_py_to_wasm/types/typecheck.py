# typecheck.py
#

from compared_py_to_wasm.models.model import *
from compared_py_to_wasm.parses.parse import lineno
from collections import ChainMap
from contextlib import contextmanager

valid_types = { 'int', 'float', 'char', 'bool' }

# Class that holds the environment for checking.  It's almost
# like the environment for the interpreter.
class CheckContext:
    def __init__(self):
        self.env = ChainMap()
        self.ok = True

    # Use this method to report an error message
    def error(self, lineno, message):
        print(f'{lineno}: {message}')
        self.ok = False

    def lookup(self, name):
        return self.env.get(name)

    def define(self, name, value):
        if name in self.env.maps[0]:
            return False
        self.env[name] = value
        return True

    @contextmanager
    def new_scope(self):
        self.env = self.env.new_child()
        try:
            yield
        finally:
            self.env = self.env.parents
        
# Top-level function used to check programs
def check_program(model):
    context = CheckContext()
    # Insert type definitions
    context.define('int', ('type', 'int'))
    context.define('float', ('type', 'float'))
    context.define('char', ('type', 'char'))
    context.define('bool', ('type', 'bool'))
    check(model, context)
    return context.ok

# Internal function used to check nodes with an environment.  Critical
# point: Everything is focused on types.  The result of an expression
# is a type.  The inputs to different operations are types.

def check(node, context):
    # Carefully notice that we are only interested in the type.
    # The value is disregarded.
    if isinstance(node, Integer):
        return "int"

    elif isinstance(node, Float):
        return "float"

    elif isinstance(node, Character):
        return "char"

    elif isinstance(node, Boolean):
        return "bool"

    elif isinstance(node, BinOp):
        ltype = check(node.left, context)
        rtype = check(node.right, context)
        if (   (ltype in { 'int', 'float' }
                and node.op not in { '+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!=' })
               or (ltype == 'bool'
                   and node.op not in { '&&', '||', '==', '!='})
               or (ltype == 'char'
                   and node.op not in { '<', '>', '<=', '>=', '==', '!=' })):
            context.error(lineno(node), f'Unsupported binary operator: {ltype} {node.op} {rtype}')
            return 'error'
        if ltype != rtype:
            context.error(lineno(node), f'Type error in binary operator. {ltype} {node.op} {rtype}')
            return 'error'
        if node.op in {'<', '>', '<=', '>=', '==', '!=', '&&', '!='}:
            return 'bool'
                    
        return ltype

    elif isinstance(node, UnaryOp):
        optype = check(node.operand, context)
        if (   (optype in { 'int', 'float' }
                and node.op not in { '+', '-' })
               or (optype == 'bool'
                   and node.op not in { '!' })
               or (optype == 'char')):
            context.error(lineno(node), f'Unsupported unary operator: {node.op} {optype}')
            return 'error'
        return optype

    elif isinstance(node, Grouping):
        return check(node.expression, context)

    elif isinstance(node, Statements):
        resulttype = None
        for stmt in node.statements:
            resulttype = check(stmt, context)
        return resulttype

    elif isinstance(node, ConstDeclaration):
        result_type = check(node.value, context)
        if node.type and node.type != result_type:
            context.error(lineno(node), f'Type error in assignment {node.type} = {result_type}')
        if not context.define(node.name, ('const', result_type)):
            context.error(lineno(node), f'Duplicate definition of {node.name}')
        return None

    elif isinstance(node, VarDeclaration):
        if node.value:
            result_type = check(node.value, context)
        else:
            result_type = None
        if node.type and node.value and node.type != result_type:
            context.error(lineno(node), f'Type error in assignment {node.type} = {result_type}')
        elif node.type is None and not node.value:
            context.error(lineno(node), f'Missing type on declaration of {node.name}')
        elif node.type and node.type not in valid_types:
            context.error(lineno(node), f'Unknown type {node.type}')
        context.define(node.name, ('var', result_type if result_type else node.type))
        return None

    elif isinstance(node, Name):
        decl = context.lookup(node.value)
        if not decl:
            context.error(lineno(node), f'Undefined name {node.value}')
            return 'error'
        else:
            return decl[1]

    elif isinstance(node, Assignment):
        valuetype = check(node.value, context)
        return check_lhs(node.location, valuetype, context)

    elif isinstance(node, PrintStatement):
        # Note: You don't actually print.  You just check the value to
        # make sure it's good.
        valuetype = check(node.value, context)
        return None

    elif isinstance(node, IfStatement):
        testtype = check(node.test, context)
        if testtype != 'bool':
            context.error(lineno(node), f'Conditional test must be a bool. Got {testtype}')
        with context.new_scope():
            check(node.consequence, context)
        if node.alternative:
            with context.new_scope():
                check(node.consequence, context)
        return None

    elif isinstance(node, WhileStatement):
        testtype = check(node.test, context)
        if testtype != 'bool':
            context.error(lineno(node), f'While test must be a bool. Got {testtype}')
        with context.new_scope():
            context.define('while', True)
            check(node.body, context)
        return None

    elif isinstance(node, BreakStatement):
        if not context.lookup('while'):
            context.error(lineno(node), f'break used outside of a while loop')
        return None

    elif isinstance(node, ContinueStatement):
        if not context.lookup('while'):
            context.error(lineno(node), f'continue used outside of a while loop')
        return None

    elif isinstance(node, ExpressionAsStatement):
        return check(node.expression, context)

    elif isinstance(node, CompoundExpression):
        with context.new_scope():
            return check(node.statements, context)

    elif isinstance(node, Name):
        decl = context.lookup(node.value)
        if not decl:
            context.error(lineno(node), f'{node.value} undefined')
            return 'error'
        return decl[1]
    
    elif isinstance(node, FunctionDeclaration):
        if node.return_type not in valid_types:
            context.error(lineno(node), f'Invalid return type of {node.return_type}')

        if context.lookup('return'):
            context.error(lineno(node), f'Nested functions are not supported')

        context.define(node.name, ('func', node))
        with context.new_scope():        
            for n, p in enumerate(node.parameters, start=1):
                if p.type not in valid_types:
                    context.error(lineno(p), f'Invalid type {p.type} in parameter {n}.')
                context.define(p.name, ('var', p.type))

            context.define('return', node.return_type)
            check(node.body, context)

    elif isinstance(node, FunctionApplication):
        decl = check(node.func, context)
        if decl in valid_types:
            if len(node.arguments) != 1:
                context.error(lineno(node), f"Type conversion to {decl} requires 1 argument.")
                return decl
            return decl
        if not isinstance(decl, FunctionDeclaration):
            context.error(lineno(node.func), f'Not a function')
            return 
        if len(node.arguments) != len(decl.parameters):
            context.error(lineno(node), f"Wrong # arguments in function call. Expected {len(decl.parameters)}, got {len(node.arguments)}")
            return decl.return_type
        for n, (parm, arg) in enumerate(zip(decl.parameters, node.arguments), start=1):
            argtype = check(arg, context)
            if argtype != parm.type:
                context.error(lineno(arg), f'Type error in argument {n}. Expected {parm.type}. Got {argtype}')
        return decl.return_type

    elif isinstance(node, ReturnStatement):
        rettype = check(node.value, context)
        expected = context.lookup('return')
        if not expected:
            context.error(lineno(node), f'return used outside a function')
            return
        if rettype != expected:
            context.error(lineno(node), f'Type error in return. Expected {expected}. Got {rettype}')
        
    else:
        raise RuntimeError(f"Couldn't check {node}")

def check_lhs(node, valuetype, context):
    if isinstance(node, Name):
        decl = context.lookup(node.value)
        if not decl:
            context.error(lineno(node), f'{node.value} not defined')
            return
        if decl[0] != 'var':
            context.error(lineno(node), f"Can't assign to {node.value}")
        if decl[1] != valuetype:
            context.error(lineno(node), f'Type error in assignment. Expected {decl[1]}. Got {valuetype}')
    
# Sample main program
def main(filename):
    from compared_py_to_wasm.parses.parse import parse_file
    model = parse_file(filename)
    check_program(model)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])



        


        
