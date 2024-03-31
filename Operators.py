from Errors import *
import math

class Operator:
    
    def __init__(self, name = '<op>', function = lambda x: 'undefined op'):
        self.name = name
        self.fn = function
    
    def __str__(self):
        return self.name

class Unary_Left_Operator(Operator):
    def __init__(self, name = '<un_op_l>', function = lambda x: 'undefined un_op_left'):
        super().__init__(name, function)

class Unary_Right_Operator(Operator):
    def __init__(self, name = '<un_op_r>', function = lambda x: 'undefined un_op_right'):
        super().__init__(name, function)

class Binary_Operator(Operator):
    def __init__(self, name = '<bin_op>', function = lambda x, y: 'undefined bin_op'):
        super().__init__(name, function)

def factorial_fn(N):
    if not N.is_int(): raise CalculatorError(f'Factorial operator expects an integer, not {str(N)}')
    return 

assignment = Binary_Operator('=')
space_separator = Binary_Operator(' ')
comma_separator = Binary_Operator(', ')
permutation = Binary_Operator('P')
combination = Binary_Operator('C')
ambiguous_plus = Operator('+')
ambiguous_minus = Operator('-')
ambiguous_exclamation = Operator('!')
addition = Binary_Operator(' + ')
subtraction = Binary_Operator(' - ')
multiplication = Binary_Operator('*')
division = Binary_Operator('/')
positive = Unary_Left_Operator('+')
negative = Unary_Left_Operator('-')
sin = Unary_Left_Operator('sin ')
cos = Unary_Left_Operator('cos ')
tan = Unary_Left_Operator('tan ')
sqrt = Unary_Left_Operator('sqrt', lambda x: math.sqrt)
exponentiation = Binary_Operator('^')
factorial = Unary_Right_Operator('!', factorial_fn)

op_regexes = {r'\s*\/\s*': division,
              r'\s*\*\s*': multiplication,
              r'!': ambiguous_exclamation,  # factorial or logical NOT
              r'\^': exponentiation,
              r'\s*\+\s+': addition,
              r'\s*\-\s+': subtraction,
              r'\s*\+': ambiguous_plus,
              r'\s*\-': ambiguous_minus,
              r'\s*=\s*': assignment,
              r'\s*,\s*': comma_separator,
              r'\s*sin\s*': sin,
              r'\s*cos\s*': cos,
              r'\s*tan\s*': tan,
              r'\s*sqrt\s*': sqrt,
              r'\s+': space_separator,
              r'P': permutation,
              r'C': combination,
}

def assign(x, y):
    pass

              # '\\*': multiply,
              # '\\/': divide,
              # '\\^': power,
              # '%': modulus,
              # 'P': permutation,
              # 'C': combination
              # }
              #  'sqrt': square_root,
              #  'sin *': , 'cos *', 'tan *'] 