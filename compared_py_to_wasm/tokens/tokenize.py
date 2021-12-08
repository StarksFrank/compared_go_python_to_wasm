# tokenizer.py
# -------------------------------

# Class that represents a token
class Token:
    def __init__(self, type, value, lineno):
        self.type = type
        self.value = value
        self.lineno = lineno

    def __repr__(self):
        return f'Token({self.type!r}, {self.value!r}, {self.lineno})'

# High level function that takes input source text and turns it into
# tokens.  This might be a natural place to use some kind of generator
# function or iterator.

_literals = {
    '+': 'PLUS',
    '-': 'MINUS',
    '*': 'TIMES',
    '/': 'DIVIDE',
    '<': 'LT',
    '<=' : 'LE',
    '>': 'GT',
    '>=': 'GE',
    '=': 'ASSIGN',
    '==': 'EQ',
    '!=' : 'NE',
    '&&': 'LAND',
    '||': 'LOR',
    '!': 'LNOT',
    ';': 'SEMI',
    '(': 'LPAREN',
    ')': 'RPAREN',
    '{': 'LBRACE',
    '}': 'RBRACE',
    ',': 'COMMA',
    }

_keywords = { 'print', 'if', 'else', 'var', 'const', 'func', 'while', 'break', 'continue', 'return', 'true', 'false' }
    
def tokenize(text):
    n = 0
    lineno = 1
    size = len(text)
    while n < size:
        if text[n] in ' \t':
            n += 1
            continue
        elif text[n] == '\n':
            n += 1
            lineno += 1
            continue
        elif text[n:n+2] == '/*':
            end = text.find('*/', n)
            if end < 0:
                error(lineno, "Unterminated comment")
                return
            else:
                lineno += text[n:end].count('\n')
                n = end + 2
                continue
        elif text[n:n+2] == '//':
            end = text.find('\n', n)
            if end < 0:
                return
            lineno += 1
            n = end + 1
            continue
        elif text[n].isdigit():
            start = n
            while n < size and text[n].isdigit():
                n += 1
            if n < size and text[n] == '.':
                n += 1
                while n < size and text[n].isdigit():
                    n += 1
                yield Token('FLOAT', text[start:n], lineno)
            else:
                yield Token('INTEGER', text[start:n], lineno)
            continue

        elif text[n] == '.':
            start = n
            n += 1
            while n < size and text[n].isdigit():
                n += 1
            if n != start + 1:
                yield Token('FLOAT', text[start:n], lineno)
            else:
                yield Token('DOT', '.', lineno)
            continue

        elif text[n].isalpha() or text[n] == '_':
            start = n
            while n < size and (text[n].isalnum() or text[n] == '_'):
                n += 1
            toktype = text[start:n]
            if toktype in _keywords:
                yield Token(toktype.upper(), toktype, lineno)
            else:
                yield Token('ID', toktype, lineno)
            continue

        elif text[n] == "'":
            start = n
            n += 1
            while n < size and text[n] != "'":
                if text[n] == '\\':
                    n += 1
                n += 1
            if n >= size:
                error(lineno, "Unterminated character constant")
            yield Token('CHAR', text[start:n+1], lineno)
            n += 1
            continue
        
        elif text[n:n+2] in _literals:
            yield Token(_literals[text[n:n+2]], text[n:n+2], lineno)
            n += 2
            continue
        elif text[n] in _literals:
            yield Token(_literals[text[n]], text[n], lineno)
            n += 1
            continue

        else:
            error(lineno, f'Illegal character {text[n]!r}')
            n += 1

# Main program to test on input files
def main(filename):
    with open(filename) as file:
        text = file.read()

    for tok in tokenize(text):
        print(tok)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 -m wabbit.tokenize filename")
    main(sys.argv[1])

    
            
        

            
    
