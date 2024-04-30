from Operators import Operator, Infix, Prefix, Postfix
from Functions import Function
from Errors import *
from Vars import LValue
from Numbers import Number

def factorial_fn(n, **kwargs):
    from Numbers import Number
    if not n.is_int(): raise CalculatorError(f'Factorial operator expects an integer, not {str(n)}')
    n = int(n)
    if n in (0, 1): return Number(1)
    for i in range(2, n): n *= i
    return Number(n)

def permutation_fn(n, r, **kwargs):  # nPr
    return combination_fn(n, r, perm=True, **kwargs)

def combination_fn(n, r, perm=False, **kwargs):  # nCr
    from Numbers import Number
    if not n.is_int() or not r.is_int(): raise CalculatorError(f'Combination function expects integers')
    n, r = int(n), int(r)
    res = 1
    if n in (0, 1): return Number(1)
    for i in range(1, r + 1): res *= n + 1 - i; res //= i ** (not perm)
    return Number(res)

# How to compute ln A?
# ====================
# y = e^x - A
# Given a guess x0, we have (x0, e^x0 - A). Gradient is e^x0.
# Eqn is y - e^x0 + A = e^x0 (x - x0)
# At y = 0, - e^x0 + A = e^x0 (x - x0)
# -1 + A/e^x0 = x - x0
# x = x0 - 1 + A/e^x0 <- Newton's Method

def exponentiation_fn(a, b, *args, epsilon=None, fcf=False, **kwargs):
    if isinstance(a, Function): return a ** b
    from Numbers import Number
    if epsilon is None: epsilon = Number(1, 10**20, fcf=False)
    # print(f'Exponentiation: {str(a)} ^ {str(b)}')
    if b.sign == -1: a = Number(1) / a; b = -b
    A = Number((a.sign * a.numerator) ** b.numerator, a.denominator ** b.numerator, fcf=False)  # A = a^(b.numerator)
    if b.is_int(): return A
    if a.sign == -1: raise CalculatorError(f'Cannot raise a negative number {str(a)} to a fractional power {str(b)}')
    # need to power A to 1/b.denominator
    # Newton's method:
    # x(k+1) = (n/(n-1)) x(k) + (A/n) /  (x(k))^(n-1)
    bd = Number(b.denominator, fcf=False)
    coeff1 = (bd - 1) / bd
    coeff2 = A / bd
    
    x = Number(float(a.dec(10)) ** float(b.dec(10)))  # initial estimate
    while True:
        x_new = (coeff1 * x + coeff2 / exponentiation_fn(x, bd - 1, epsilon=epsilon)).fast_continued_fraction(epsilon=epsilon)
        if abs(x_new - x) < epsilon: break
        x = x_new
    return x_new

def assignment_fn(L, R, mem=None):
    if mem is None: raise MemoryError('No Memory object passed to assignment operator')
    if not isinstance(L, LValue): raise TypeError('Can only assign to LValue')
    mem.add(L.name, R)
    return R

assignment = Infix(' = ', assignment_fn)
space_separator = Infix(' ', lambda x, y, *args, **kwargs: x * y)
semicolon_separator = Infix('; ', lambda x, y, *args, **kwargs: y)
permutation = Infix('P', permutation_fn)
combination = Infix('C', combination_fn)
ambiguous_plus = Operator('+?')
ambiguous_minus = Operator('-?')
addition = Infix(' + ', lambda x, y, *args, **kwargs: x + y)
subtraction = Infix(' - ', lambda x, y, *args, **kwargs: x - y)
multiplication = Infix(' * ', lambda x, y, *args, **kwargs: x * y)
implicit_mult = Infix('∙', lambda x, y, *args, **kwargs: x * y)
implicit_mult_prefix = Infix('∙', lambda x, y, *args, **kwargs: x * y)
division = Infix(' / ', lambda x, y, *args, **kwargs: x / y)
modulo = Infix(' % ', lambda x, y, *args, **kwargs: x % y)
positive = Prefix('+', lambda x: x)
negative = Prefix('-', lambda x: -x)
lt = Infix(' < ', lambda x, y, *args, **kwargs: Number(1) if x < y else Number(0))
lt_eq = Infix(' <= ', lambda x, y, *args, **kwargs: Number(1) if x <= y else Number(0))
gt = Infix(' > ', lambda x, y, *args, **kwargs: Number(1) if x > y else Number(0))
gt_eq = Infix(' >= ', lambda x, y, *args, **kwargs: Number(1) if x >= y else Number(0))
eq = Infix(' == ', lambda x, y, *args, **kwargs: Number(1) if x == y else Number(0))
neq = Infix(' != ', lambda x, y, *args, **kwargs: Number(1) if x != y else Number(0))
logical_and = Infix(' && ', lambda x, y, *args, **kwargs: x if x.sign == 0 else y)
logical_or = Infix(' || ', lambda x, y, *args, **kwargs: x if x.sign != 0 else y)
function_invocation = Infix('<invoke>', lambda x, y, *args, **kwargs: x.invoke(y, *args, **kwargs))
function_composition = Infix('', lambda x, y, *args, **kwargs: x.invoke(y, *args, **kwargs))

sin = Prefix('sin ')
cos = Prefix('cos ')
tan = Prefix('tan ')
sqrt = Prefix('sqrt', lambda x: exponentiation_fn(x, Number(1, 2, fcf=False)))
exponentiation = Infix('^', exponentiation_fn)
factorial = Postfix('!', factorial_fn)

regex = {r'\s*(\/)\s*': division,
         r'\s*(\*)\s*': multiplication,
         r'\s*(%)\s*': modulo,
         r'(!)': factorial,
         r'\s*(\^)\s*': exponentiation,
         r'\s*(\+)\s+': addition,
         r'\s*(\-)\s+': subtraction,
         r'\s*(>=)\s*': gt_eq,
         r'\s*(<=)\s*': lt_eq,
         r'\s*(==)\s*': eq,
         r'\s*(!=)\s*': neq,
         r'\s*(>)\s*': gt,
         r'\s*(<)\s*': lt,
         r'\s*(\+)': ambiguous_plus,
         r'\s*(\-)': ambiguous_minus,
         r'\s*(&&)\s*': logical_and,
         r'\s*(\|\|)\s*': logical_or,
         r'\s*(=)\s*': assignment,
         # r'\s*(,)\s*': comma_separator,
         r'\s*(sin)(?:\s+|(?![A-Za-z_]))': sin,
         r'\s*(cos)(?:\s+|(?![A-Za-z_]))': cos,
         r'\s*(tan)(?:\s+|(?![A-Za-z_]))': tan,
         r'\s*(sqrt)(?:\s+|(?![A-Za-z_]))': sqrt,
         r'(\s)\s*': space_separator,
         r'\s*(;)\s*': semicolon_separator,
         r'(P)': permutation,
         r'(C)': combination,
}

"""
order = (((space_separator, multiplication, division, modulo), 1),
         ((addition, subtraction), 1),
         ((lt_eq, lt, gt, gt_eq), 1),
         ((eq, neq), 1),
         ((logical_and, ), 1),
         ((logical_or, ), 1),
         ((assignment, ), -1),
)
"""

power = {
         function_invocation: (10.1, 99),
         factorial: (12, 12.1),
         implicit_mult: (11, 11),
         exponentiation: (11.1, 10.9),
         sqrt: (11.1, 10.9),
         negative: (11.1, 10.9),
         positive: (11.1, 10.9),
         implicit_mult_prefix: (10, 10),
         # frac_div: (9, 9),
         permutation: (9, 9),
         combination: (9, 9),
         division: (8, 8),
         multiplication: (8, 8),
         modulo: (8, 8),
         space_separator: (8, 8),
         subtraction: (7, 7),
         addition: (7, 7),
         gt_eq: (6, 6),
         gt: (6, 6),
         lt_eq: (6, 6),
         lt: (6, 6),
         eq: (5, 5),
         neq: (5, 5),
         logical_and: (4, 4),
         logical_or: (3, 3),
         assignment: (2, 1.9),
         semicolon_separator: (1, 1.1),
         # comma_separator: (1, 1),
         None: (0, 0),
}

# a + (b=3) + 4^b(c=b+1)a!sinb + 7c
# 4  (b=4) yz^ab cos 7 b sin 3 + 8

# Postfix (UR) 10
# 9- Implicit Mult -8
# 9- Exponentiation -8
# 7- Prefix (UL) -7
# 6- Division / Multiplication -6
# 5- Addition / Subtraction -5
# 4-AND-4
# 3-OR-3
# 2-Assignment-2
# 1-Comma-1
pass