# parse.py
#


from compared_py_to_wasm.models.model import *
from compared_py_to_wasm.tokens.tokenize import tokenize

# Line number tracking
_line_numbers = { }
def record_lineno(node, lineno):
    _line_numbers[node.id] = lineno
    return node

def lineno(node):
    return _line_numbers.get(node.id, '')
    
class EOF:
    type = 'EOF'
    value = 'EOF'
    lineno = 'EOF'
    
class Tokens:
    def __init__(self, gen):
        self._gen = gen
        self._lookahead = None

    def peek(self, *types):
        if self._lookahead is None:
            self._lookahead = next(self._gen, EOF)
        if self._lookahead.type in types:
            return self._lookahead
        else:
            return None

    def accept(self, *types):
        tok = self.peek(*types)
        if tok:
            self._lookahead = None
        return tok

    def expect(self, *types):
        tok = self.peek(*types)
        if not tok:
            raise SyntaxError(f'Expected {types} before {self._lookahead}')
        self._lookahead = None
        return tok
            
# Top-level function that runs everything    
def parse_source(text):
    tokens = tokenize(text)
    model = parse_program(Tokens(tokens))     # You need to implement this part
    return model

def parse_program(tokens):
    # Code this to recognize any Wabbit program and return the model
    statements = parse_statements(tokens)
    tokens.expect('EOF')
    return statements

def parse_statements(tokens):
    statements = [ ]
    while not tokens.peek('RBRACE', 'EOF'):
        statement = parse_statement(tokens)
        statements.append(statement)
    return Statements(statements)

def parse_statement(tokens):
    if tokens.peek('PRINT'):
        return parse_print_statement(tokens)
    elif tokens.peek('CONST'):
        return parse_const_declaration(tokens)
    elif tokens.peek('VAR'):
        return parse_var_declaration(tokens)
    elif tokens.peek('RETURN'):
        return parse_return_statement(tokens)
    elif tokens.peek('IF'):
        return parse_if_statement(tokens)
    elif tokens.peek('WHILE'):
        return parse_while_statement(tokens)
    elif tokens.peek('BREAK'):
        return parse_break_statement(tokens)
    elif tokens.peek('CONTINUE'):
        return parse_continue_statement(tokens)
    elif tokens.peek('FUNC'):
        return parse_function_declaration(tokens)
    else:
        return parse_assignment_statement(tokens)

def parse_const_declaration(tokens):
    lineno = tokens.expect('CONST').lineno
    name = tokens.expect('ID')
    type = tokens.accept('ID')
    tokens.expect('ASSIGN')
    value = parse_expression(tokens)
    tokens.expect('SEMI')
    return record_lineno(ConstDeclaration(name.value, type.value if type else None, value), lineno)

def parse_var_declaration(tokens):
    lineno = tokens.expect('VAR').lineno
    name = tokens.expect('ID')
    type = tokens.accept('ID')
    if tokens.accept('ASSIGN'):
        value = parse_expression(tokens)
    else:
        value = None
    tokens.expect('SEMI')
    return record_lineno(VarDeclaration(name.value, type.value if type else None, value), lineno)

def parse_assignment_statement(tokens):
    location = parse_expression(tokens)
    if tokens.accept('ASSIGN'):
        value = parse_expression(tokens)
        tokens.expect('SEMI')
        return record_lineno(Assignment(location, value), lineno(location))
    else:
        tokens.expect('SEMI')
        return record_lineno(ExpressionAsStatement(location), lineno(location))

def parse_if_statement(tokens):
    lineno = tokens.expect('IF').lineno
    test = parse_expression(tokens)
    tokens.expect('LBRACE')
    consequence = parse_statements(tokens)
    tokens.expect('RBRACE')
    if tokens.accept('ELSE'):
        tokens.expect('LBRACE')
        alternative = parse_statements(tokens)
        tokens.expect('RBRACE')
    else:
        alternative = None
    return record_lineno(IfStatement(test, consequence, alternative), lineno)

def parse_while_statement(tokens):
    lineno = tokens.expect('WHILE').lineno
    test = parse_expression(tokens)
    tokens.expect('LBRACE')
    body = parse_statements(tokens)
    tokens.expect('RBRACE')
    return record_lineno(WhileStatement(test, body), lineno)

def parse_break_statement(tokens):
    # Example of parsing a simple statement (pseudocode)
    lineno = tokens.expect('BREAK').lineno
    tokens.expect('SEMI')
    return record_lineno(BreakStatement(), lineno)

def parse_continue_statement(tokens):
    lineno = tokens.expect('CONTINUE').lineno
    tokens.expect('SEMI')
    return record_lineno(ContinueStatement(), lineno)

def parse_print_statement(tokens):
    lineno = tokens.expect('PRINT').lineno
    value = parse_expression(tokens)
    tokens.expect('SEMI')
    return record_lineno(PrintStatement(value), lineno)

def parse_function_declaration(tokens):
    lineno = tokens.expect('FUNC').lineno
    nametok = tokens.expect('ID')
    tokens.expect('LPAREN')
    parameters = []
    while not tokens.peek('RPAREN'):
        pname = tokens.expect('ID')
        ptype = tokens.expect('ID')
        parm = record_lineno(Parameter(pname.value, ptype.value), pname.lineno)
        parameters.append(parm)
        if not tokens.peek('RPAREN'):
            tokens.expect('COMMA')
    tokens.expect('RPAREN')
    rettype = tokens.expect('ID')
    tokens.expect('LBRACE')
    body = parse_statements(tokens)
    tokens.expect('RBRACE')
    return record_lineno(FunctionDeclaration(nametok.value, parameters, rettype.value, body), lineno)
    
def parse_return_statement(tokens):
    lineno = tokens.expect('RETURN').lineno
    value = parse_expression(tokens)
    tokens.expect('SEMI')
    return record_lineno(ReturnStatement(value), lineno)

def parse_expression(tokens):
    return parse_orterm(tokens)

def parse_orterm(tokens):
    left = parse_andterm(tokens)
    while (tok := tokens.accept('LOR')):
        right = parse_andterm(tokens)
        left = record_lineno(BinOp(tok.value, left, right), tok.lineno)
    return left

def parse_andterm(tokens):
    left = parse_relterm(tokens)
    while (tok := tokens.accept('LAND')):
        right = parse_relterm(tokens)
        left = record_lineno(BinOp(tok.value, left, right), tok.lineno)
    return left

def parse_relterm(tokens):
    left = parse_addterm(tokens)
    if (tok := tokens.accept('LT','LE','GT','GE','EQ','NE')):
        right = parse_addterm(tokens)
        left = record_lineno(BinOp(tok.value, left, right), tok.lineno)
    return left

def parse_addterm(tokens):
    left = parse_multerm(tokens)
    while (tok := tokens.accept('PLUS','MINUS')):
        right = parse_multerm(tokens)
        left = record_lineno(BinOp(tok.value, left, right), tok.lineno)
    return left
    
def parse_multerm(tokens):
    left = parse_factor(tokens)
    while (tok := tokens.accept('TIMES','DIVIDE')):
        right = parse_factor(tokens)
        left = record_lineno(BinOp(tok.value, left, right), tok.lineno)
    return left
    
def parse_factor(tokens):
    tok = tokens.accept('INTEGER')
    if tok:
        return record_lineno(Integer(tok.value), tok.lineno)
    tok = tokens.accept('FLOAT')
    if tok:
        return record_lineno(Float(tok.value), tok.lineno)
    tok = tokens.accept('TRUE', 'FALSE')
    if tok:
        return record_lineno(Boolean(tok.value), tok.lineno)
    tok = tokens.accept('CHAR')
    if tok:
        return record_lineno(Character(tok.value), tok.lineno)
    if tokens.accept('LPAREN'):
        value = parse_expression(tokens)
        tokens.expect('RPAREN')
        return record_lineno(Grouping(value), lineno(value))
    if tokens.accept('LBRACE'):
        value = parse_statements(tokens)
        tokens.accept('RBRACE')
        return record_lineno(CompoundExpression(value), lineno(value))
    tok = tokens.accept('PLUS','MINUS','LNOT')
    if tok:
        value = parse_factor(tokens)
        return record_lineno(UnaryOp(tok.value, value), tok.lineno)
    if tokens.peek('ID'):
        loc = parse_location(tokens)
        if tokens.accept('LPAREN'):
            args = parse_arguments(tokens)
            tokens.expect('RPAREN')
            return record_lineno(FunctionApplication(loc, args), lineno(loc))
        else:
            return loc
        
    raise SyntaxError("Syntax Error in parse_factor")

def parse_arguments(tokens):
    arguments = []
    while not tokens.peek('RPAREN'):
        expr = parse_expression(tokens)
        if not tokens.peek('RPAREN'):
            tokens.expect('COMMA')
        arguments.append(expr)
    return arguments

def parse_location(tokens):
    name = tokens.expect('ID')
    return record_lineno(Name(name.value), name.lineno)

# Example of a main program
def parse_file(filename):
    with open(filename) as file:
        text = file.read()
    return parse_source(text)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 -m wabbit.parse filename')
    model = parse_file(sys.argv[1])
    print(model)


