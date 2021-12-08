# wasm.py
#

from compared_py_to_wasm.models.model import *
from collections import ChainMap
from contextlib import contextmanager

_typemap = {
    'int': 'i32',
    'float': 'f64',
    'bool': 'i32',
    'char': 'i32',
    }

class WasmFunction:
    def __init__(self, name, parameters, ret_type):
        self.name = name
        self.parameters = parameters
        self.ret_type = ret_type
        self.code = [ ]
        self.locals = [ ]

    def __str__(self):
        out = f'(func ${self.name} (export "{self.name}")\n'
        for parm in self.parameters:
            out += f'(param ${parm.name} {_typemap[parm.type]})\n'
        if self.ret_type:
            out += f'(result {_typemap[self.ret_type]})\n'
            out += f'(local $return {_typemap[self.ret_type]})\n'
        out += '\n'.join(self.locals)
        out += '\nblock $return\n'
        out += '\n'.join(self.code)
        out += '\nend\n'
        if self.ret_type:
            out += 'local.get $return\n'
        out += ')\n'
        return out
        
# Class representing the world of Wasm
class WabbitWasmModule:
    def __init__(self):
        self.module = [ '(module' ]
        self.env = ChainMap()
        self.function = WasmFunction('_init', [], None)
        self.scope = 'global'
        self.nlabels = 0
        self.have_main = False        
        self.module.append('(import "env" "_printi" (func $_printi ( param i32 )))')
        self.module.append('(import "env" "_printf" (func $_printf ( param f64 )))')
        self.module.append('(import "env" "_printb" (func $_printb ( param i32 )))')
        self.module.append('(import "env" "_printc" (func $_printc ( param i32 )))')
                
    def __str__(self):
        return '\n'.join(self.module) + '\n)\n'

    @contextmanager
    def new_scope(self):
        self.env = self.env.new_child()
        yield
        self.env = self.env.parents
        
    def define(self, name, value):
        self.env[name] = value

    def lookup(self, name):
        return self.env[name]

    def new_label(self):
        self.nlabels += 1
        return f'label{self.nlabels}'
    
# Top-level function for generating code from the model
def generate_program(model):
    mod = WabbitWasmModule()
    generate(model, mod)
    if mod.have_main:
        mod.function.code.append('call $main')
        mod.function.code.append('drop')
    mod.module.append(str(mod.function))
    return str(mod)

# Internal function for generating code on each node
def generate(node, mod):
    if isinstance(node, Integer):
        mod.function.code.append(f'i32.const {node.value}')
        return 'int'
    
    elif isinstance(node, Float):
        mod.function.code.append(f'f64.const {node.value}')
        return 'float'
    
    elif isinstance(node, Boolean):
        mod.function.code.append(f'i32.const {int(node.value=="true")}')
        return 'bool'
    
    elif isinstance(node, Character):
        mod.function.code.append(f'i32.const {ord(eval(node.value))}')
        return 'char'

    elif isinstance(node, PrintStatement):
        valtype = generate(node.value, mod)
        if valtype == 'int':
            mod.function.code.append('call $_printi')
        elif valtype == 'float':
            mod.function.code.append('call $_printf')
        elif valtype == 'bool':
            mod.function.code.append('call $_printb')
        elif valtype == 'char':
            mod.function.code.append('call $_printc')
        return None

    elif isinstance(node, BinOp):
        ltype = generate(node.left, mod)
        rtype = generate(node.right, mod)
        if ltype == 'float':
            if node.op == '+':
                mod.function.code.append('f64.add')
                return 'float'
            elif node.op == '-':
                mod.function.code.append('f64.sub')
                return 'float'                
            elif node.op == '*':
                mod.function.code.append('f64.mul')
                return 'float'                
            elif node.op == '/':
                mod.function.code.append('f64.div')
                return 'float'                
            elif node.op == '<':
                mod.function.code.append('f64.lt')
                return 'bool'
            elif node.op == '>':
                mod.function.code.append('f64.gt')
                return 'bool'                
            elif node.op == '<=':
                mod.function.code.append('f64.le')
                return 'bool'                
            elif node.op == '>=':
                mod.function.code.append('f64.ge')
                return 'bool'                
            elif node.op == '==':
                mod.function.code.append('f64.eq')
                return 'bool'                
            elif node.op == '!=':
                mod.function.code.append('f64.ne')
                return 'bool'                
        else:
            if node.op == '+':
                mod.function.code.append('i32.add')
                return ltype
            elif node.op == '-':
                mod.function.code.append('i32.sub')
                return ltype
            elif node.op == '*':
                mod.function.code.append('i32.mul')
                return ltype
            elif node.op == '/':
                mod.function.code.append('i32.div_s')
                return ltype
            elif node.op == '<':
                mod.function.code.append('i32.lt_s')
                return 'bool'
            elif node.op == '>':
                mod.function.code.append('i32.gt_s')
                return 'bool'                
            elif node.op == '<=':
                mod.function.code.append('i32.le_s')
                return 'bool'                
            elif node.op == '>=':
                mod.function.code.append('i32.ge_s')
                return 'bool'                
            elif node.op == '==':
                mod.function.code.append('i32.eq')
                return 'bool'                
            elif node.op == '!=':
                mod.function.code.append('i32.ne')
                return 'bool'
            elif node.op == '&&':
                mod.function.code.append('i32.and')
                return 'bool'
            elif node.op == '||':
                mod.function.code.append('i32.or')
                return 'bool'

    elif isinstance(node, UnaryOp):
        pos = len(mod.function.code)
        operandtype = generate(node.operand, mod)
        if node.op == '-':
            if operandtype == 'float':
                mod.function.code.insert(pos, 'f64.const 0.0')
                mod.function.code.append('f64.sub')
            else:
                mod.function.code.insert(pos, 'i32.const 0')
                mod.function.code.append('i32.sub')
        elif node.op == '!':
            mod.function.code.append('i32.const 1')
            mod.function.code.append('i32.xor')
        return operandtype

    elif isinstance(node, Grouping):
        return generate(node.expression, mod)

    elif isinstance(node, ConstDeclaration):
        valtype = generate(node.value, mod)
        if mod.scope == 'global':
            if valtype == 'float':
                mod.module.append(f'(global ${node.name} (mut f64) (f64.const 0.0))')
            else:
                mod.module.append(f'(global ${node.name} (mut i32) (i32.const 0))')
            mod.function.code.append(f'global.set ${node.name}')
        elif mod.scope == 'local':
            if valtype == 'float':
                mod.function.locals.append(f'(local ${node.name} f64)')
            else:
                mod.function.locals.append(f'(local ${node.name} i32)')
            mod.function.code.append(f'local.set ${node.name}')
        mod.define(node.name, (mod.scope, valtype))
        return None

    elif isinstance(node, VarDeclaration):
        if node.value:
            valtype = generate(node.value, mod)
        else:
            valtype = node.type
        if mod.scope == 'global':
            if valtype == 'float':
                mod.module.append(f'(global ${node.name} (mut f64) (f64.const 0.0))')
            else:
                mod.module.append(f'(global ${node.name} (mut i32) (i32.const 0))')
            if node.value:
                mod.function.code.append(f'global.set ${node.name}')
        elif mod.scope == 'local':
            if valtype == 'float':
                mod.function.locals.append(f'(local ${node.name} f64)')
            else:
                mod.function.locals.append(f'(local ${node.name} i32)')
            if node.value:
                mod.function.code.append(f'local.set ${node.name}')
                
        mod.define(node.name, (mod.scope, valtype))
        return None

    elif isinstance(node, Assignment):
        generate_lhs(node.location, node.value, mod)
        return None
    
    elif isinstance(node, Name):
        scope, valtype = mod.lookup(node.value)
        if scope == 'global':
            mod.function.code.append(f'global.get ${node.value}')
        elif scope == 'local':
            mod.function.code.append(f'local.get ${node.value}')
        return valtype
        
    elif isinstance(node, Statements):
        result = None
        for stmt in node.statements:
            if result:
                mod.function.code.append('drop')
            result = generate(stmt, mod)
        return result

    elif isinstance(node, IfStatement):
        generate(node.test, mod)
        mod.function.code.append('if')
        with mod.new_scope():
            generate(node.consequence, mod)
        if node.alternative:
            mod.function.code.append('else')
            with mod.new_scope():
                generate(node.alternative, mod)
        mod.function.code.append('end')
        return None
    
    elif isinstance(node, WhileStatement):
        test_label = mod.new_label()
        exit_label = mod.new_label()
        mod.function.code.append(f'block ${exit_label}')
        mod.function.code.append(f'loop ${test_label}')
        generate(node.test, mod)
        mod.function.code.append(f'i32.const 1')
        mod.function.code.append(f'i32.xor')
        mod.function.code.append(f'br_if ${exit_label}')
        with mod.new_scope():
            mod.define('break', exit_label)
            mod.define('continue', test_label)
            generate(node.body, mod)
            mod.function.code.append(f'br ${test_label}')
            mod.function.code.append('end')
        mod.function.code.append('end')
        return None

    elif isinstance(node, BreakStatement):
        mod.function.code.append(f'br ${mod.lookup("break")}')
        return None

    elif isinstance(node, ContinueStatement):
        mod.function.code.append(f'br ${mod.lookup("continue")}')
        return None

    elif isinstance(node, CompoundExpression):
        with mod.new_scope():
            return generate(node.statements, mod)

    elif isinstance(node, ExpressionAsStatement):
        return generate(node.expression, mod)

    elif isinstance(node, FunctionDeclaration):
        oldfunc = mod.function
        mod.function = WasmFunction(node.name, node.parameters, node.return_type)
        mod.define(node.name, ('func', node.return_type))
        with mod.new_scope():
            mod.scope = 'local'
            for parm in node.parameters:
                mod.define(parm.name, ('local', parm.type))
            generate(node.body, mod)
        mod.module.append(str(mod.function))
        mod.function = oldfunc
        mod.scope = 'global'
        if node.name == 'main':
            mod.have_main = True
        return None

    elif isinstance(node, FunctionApplication):
        for arg in  node.arguments:
            argtype = generate(arg, mod)
        if node.func.value in {'int','bool','char'}:
            if argtype == 'float':
                mod.function.code.append('i32.trunc_s/f64')
            return node.func.value
        if node.func.value in 'float':
            if argtype in {'int','bool','char'}:
                mod.function.code.append('f64.convert_s/i32')
            return 'float'
            
        mod.function.code.append(f'call ${node.func.value}')
        decl, rettype = mod.lookup(node.func.value)
        return rettype
    
    elif isinstance(node, ReturnStatement):
        generate(node.value, mod)
        mod.function.code.append('return')
        return None
    
    else:
        raise RuntimeError(f"Can't generate {node}")

def generate_lhs(location, value, mod):
    valtype = generate(value, mod)
    if isinstance(location, Name):
        scope, valtype = mod.lookup(location.value)
        if scope == 'global':
            mod.function.code.append(f'global.set ${location.value}')
        elif scope == 'local':
            mod.function.code.append(f'local.set ${location.value}')
            
    return None
    
def main(filename):
    from compared_py_to_wasm.parses.parse import parse_file
    from compared_py_to_wasm.types.typecheck import check_program
    model = parse_file(filename)
    if check_program(model):
        mod = generate_program(model)
        with open('out.wat', 'w') as file:
            file.write(mod)
        print("Wrote out.wat")

if __name__ == '__main__':
    import sys
    main(sys.argv[1])

        
        

    

                   
