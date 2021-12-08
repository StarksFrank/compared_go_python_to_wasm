# model.py
#
# This file defines the data model for Wabbit programs.  The data
# model is a data structure that represents the contents of a program
# as objects, not text.  Sometimes this structure is known as an
# "abstract syntax tree" or AST.  However, the model is not
# necessarily a direct representation of the syntax of the language.
# So, we'll prefer to think of it as a more generic data model
# instead.
#
# To do this, you need to identify the different "elements" that make
# up a program and encode them into classes.  To do this, it may be
# useful to slightly "underthink" the problem. To illustrate, suppose
# you wanted to encode the idea of "assigning a value."  Assignment
# involves a location (the left hand side) and a value like this:
#
#         location = expression;
#
# To represent this idea, maybe you make a class with just those parts:
#
#     class Assignment:
#         def __init__(self, location, expression):
#             self.location = location
#             self.expression = expression
#
# Alternatively, maybe you elect to store the information in a tuple:
#
#    def Assignment(location, expression):
#        return ('assignment', location, expression)
#
# What are "location" and "expression"?  Does it matter? Maybe
# not. All you know is that an assignment operator definitely requires
# both of those parts.  DON'T OVERTHINK IT.  Further details will be
# filled in as the project evolves.
# 
# Work on this file in conjunction with the top-level
# "test_models.py" file.  Go look at that file and see what program
# samples are provided.  Then, figure out what those programs look
# like in terms of data structures.
#
# There is no "right" solution to this part of the project other than
# the fact that a program has to be represented as some kind of data
# structure that's not "text."   You could use classes. You could use 
# tuples. You could make a bunch of nested dictionaries like JSON. 
# The key point: it must be a data structure.
#
# Starting out, I'd advise against making this file too fancy. Just
# use basic data structures. You can add usability enhancements later.
# -----------------------------------------------------------------------------

# The following classes are used for the expression example in test_models.py.
# Feel free to modify as appropriate.  You don't even have to use classes
# if you want to go in a different direction with it.

class Node:
    id = 0
    @staticmethod
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.id = Node.id + 1
        Node.id += 1
        return self

class Integer(Node):
    '''
    Example: 42
    '''
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'Integer({self.value})'

class Float(Node):
    '''
    Example: 4.2
    '''
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'Float({self.value})'

class Boolean(Node):
    '''
    Example:  true/false
    '''
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'Boolean({self.value})'

class Character(Node):
    '''
    Example: '\n'
    '''
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'Character({self.value})'
    
class Name(Node):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'Name({self.value})'


class Assignment(Node):
    def __init__(self, location, value):
        self.location = location
        self.value = value

    def __repr__(self):
        return f'Assignment({self.location}, {self.value})'

class IfStatement(Node):
    def __init__(self, test, consequence, alternative):
        self.test = test
        self.consequence = consequence
        self.alternative = alternative

    def __repr__(self):
        return f'IfStatement({self.test}, {self.consequence}, {self.alternative})'

class WhileStatement(Node):
    def __init__(self, test, body):
        self.test = test
        self.body = body

    def __repr__(self):
        return f'WhileStatement({self.test}, {self.body})'

class BreakStatement(Node):
    def __repr__(self):
        return f'BreakStatement()'

class ContinueStatement(Node):
    def __repr__(self):
        return f'ContinueStatement()'

class FunctionDeclaration(Node):
    def __init__(self, name, parameters, return_type, body):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.body = body

    def __repr__(self):
        return f'FunctionDeclaration({self.name}, {self.parameters}, {self.return_type}, {self.body})'

class FunctionApplication(Node):
    def __init__(self, func, arguments):
        self.func = func
        self.arguments = arguments

    def __repr__(self):
        return f'FunctionApplication({self.func}, {self.arguments})'

class ReturnStatement(Node):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'ReturnStatement({self.value})'

class Parameter(Node):
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __repr__(self):
        return f'Parameter({self.name}, {self.type})'


class SourceContext:
    def __init__(self, indent='', newline='\n'):
        self.indent = indent
        self.newline = newline
    
def to_source(node, context=SourceContext()):
    if isinstance(node, Integer):
        return str(node.value)

    elif isinstance(node, Float):
        return str(node.value)

    elif isinstance(node, Boolean):
        return str(node.value)



    
