from Operators import Operator, Infix, Prefix, Postfix
from Functions import Function
from Errors import *
from Vars import LValue
from Numbers import Number

e = Number('2.718281828459045235360287471353')
pi = Number('3.1415926535897932384626433832795')
ln2 = Number(1554903831458736, 2243252046704767, fcf=False)
ln10 = Number(227480160645689, 98793378510888, fcf=False)

def factorial_fn(n, **kwargs):
    if not n.is_int(): raise CalculatorError(f'Factorial operator expects an integer, not {str(n)}')
    n = int(n)
    if n in (0, 1): return Number(1)
    for i in range(2, n): n *= i
    return Number(n)

def permutation_fn(n, r, **kwargs):  # nPr
    return combination_fn(n, r, perm=True, **kwargs)

def combination_fn(n, r, perm=False, **kwargs):  # nCr
    if not n.is_int() or not r.is_int(): raise CalculatorError(f'Combination function expects integers')
    n, r = int(n), int(r)
    res = 1
    if n in (0, 1): return Number(1)
    for i in range(1, r + 1): res *= n + 1 - i; res //= i ** (not perm)
    return Number(res)

def exponentiation_fn(a, b, epsilon=None, *args, fcf=False, **kwargs):
    if isinstance(a, Function):
        if b.is_int(): return a ** b
        raise CalculatorError(f'Cannot raise a function ({str(a)}) to a fractional power {str(b)}')
    # print(f'Exponentiation: {str(a)} ^ {str(b)}')
    if a.numerator == 0:
        if b.numerator == 0: raise CalculatorError(f'0^0 is undefined')
        return Number(0)
    if b.sign == -1: return Number(1) / exponentiation_fn(a, -b, *args, epsilon, fcf, **kwargs)
    if b.is_int(): return int_power(a, int(b), epsilon=epsilon, fcf=fcf)
    if a.sign == -1: raise CalculatorError(f'Cannot raise a negative number {str(a)} to a fractional power {str(b)}')
    # a^b = e^(b ln a)
    return exp(b * ln_fn(a, epsilon=epsilon), epsilon=epsilon)

def int_power(base, power, *args, epsilon=None, fcf=False, **kwargs):
    if not isinstance(power, int): raise CalculatorError(f'int_power() expects integral power, received {power}')
    pow = abs(power)
    int_part = Number(1)
    while pow > 0:
        if pow & 1: int_part *= base
        base = (base * base).fast_continued_fraction(epsilon=epsilon)
        pow >>= 1
    if power & 1 == 1 and base.sign == -1: int_part = -int_part
    return (Number(1) / int_part if power < 0 else int_part).fast_continued_fraction(epsilon=epsilon)

def exp(x, *args, epsilon=None, fcf=False, **kwargs):
    int_part = int_power(e, int(x), epsilon=epsilon)
    x = x.frac_part()
    sum = term = i = Number(1)
    while (abs(term) >= epsilon):
        term = (term * x) / i
        sum += term
        i += 1
    return int_part * sum.fast_continued_fraction(epsilon=epsilon)

# How to compute ln A?
# ====================
# y = e^x - A
# Given a guess x0, we have (x0, e^x0 - A). Gradient is e^x0.
# Eqn is y - e^x0 + A = e^x0 (x - x0)
# At y = 0, - e^x0 + A = e^x0 (x - x0)
# -1 + A/e^x0 = x - x0
# x = x0 - 1 + A/e^x0 <- Newton's Method
# https://qr.ae/pYekgm

def ln_fn(x, epsilon=None, **kwargs):
    if x <= 0: raise CalculatorError(f'ln can only apply to a positive number.')
    if x < 1: return -ln_fn(Number(1) / x, epsilon=epsilon, **kwargs)
    ln2s = ln10s = 0
    while x > 10:
        x /= 10
        ln10s += 1
    while x > 2:
        x /= 2
        ln2s += 1
    x0 = Number(0)
    delta_x = epsilon * Number(2)
    while abs(delta_x) > epsilon:
        delta_x = x / exp(x0, epsilon=epsilon) - 1
        x0 = (x0 + delta_x).fast_continued_fraction(epsilon=epsilon)
    return (ln10 * ln10s + ln2 * ln2s + x0).fast_continued_fraction(epsilon=epsilon)

def sin_fn(x, epsilon=None, **kwargs):
    if x < 0: return -sin_fn(-x, epsilon=epsilon, **kwargs)
    x = x % (pi * 2)
    if x > pi * 3 / 2: return -sin_fn(pi * 2 - x, epsilon=epsilon, **kwargs)
    elif x > pi: return -sin_fn(x - pi, epsilon=epsilon, **kwargs)
    elif x > pi / 2: return sin_fn(pi - x, epsilon=epsilon, **kwargs)
    sum = x_pow = delta_x = x
    x_sq = -x * x
    mul = Number(1)
    fac = Number(1)
    while abs(delta_x) > epsilon:
        mul += 2
        fac *= mul * (mul - 1)
        x_pow *= x_sq
        delta_x = (x_pow / fac).fast_continued_fraction(epsilon=epsilon)
        sum += delta_x
    return sum.fast_continued_fraction(epsilon=epsilon)

def cos_fn(x, epsilon=None, **kwargs):
    return sin_fn(pi / 2 - x, epsilon=epsilon, **kwargs)

def tan_fn(x, epsilon=None, **kwargs):
    return sin_fn(x, epsilon=epsilon, **kwargs) / cos_fn(x, epsilon=epsilon, **kwargs)

def arcsin_fn(x, epsilon=None, **kwargs):
    # https://en.wikipedia.org/wiki/List_of_mathematical_series
    if x < 0: return -arcsin_fn(-x, epsilon=epsilon, **kwargs)
    if x > 1: raise CalculatorError('arcsin only accepts values from -1 to 1 inclusive')
    if x * x > -x * x + 1: return pi / 2 - arcsin_fn(exponentiation_fn(-x * x + 1, Number(1, 2, fcf=False), epsilon=epsilon), epsilon=epsilon, **kwargs)
    sum = term = x
    xsqr = x * x
    four = Number(4)
    k = Number(0)
    while abs(term) > epsilon:
        k += 1
        term *= xsqr * (k * 2) * (k * 2 - 1) / four / k / k
        term = term.fast_continued_fraction(epsilon=epsilon)
        sum += term / (k * 2 + 1)
        sum = sum.fast_continued_fraction(epsilon=epsilon)
    return sum

def arccos_fn(x, epsilon=None, **kwargs):
    if x < 0: return pi - arccos_fn(-x, epsilon=epsilon, **kwargs)
    if x > 1: raise CalculatorError('arccos only accepts values from -1 to 1 inclusive')
    return pi / 2 - arcsin_fn(x, epsilon=epsilon, **kwargs)

def arctan_fn(x, epsilon=None, **kwargs):
    if x < 0: return -arctan_fn(-x, epsilon=epsilon, **kwargs)
    if x > 1: return pi / 2 - arctan_fn(Number(1) / x, epsilon=epsilon, **kwargs)
    # https://en.wikipedia.org/wiki/Arctangent_series
    sum = term = x / (x * x + 1)
    factor = term * x
    num = Number(2)
    two = Number(2)
    while abs(term) > epsilon:
        term *= factor
        term *= num
        term /= num + 1
        term = term.fast_continued_fraction(epsilon=epsilon)
        sum += term
        sum = sum.fast_continued_fraction(epsilon=epsilon)
        num += two
    return sum

def assignment_fn(L, R, mem=None, **kwargs):
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
frac_div = Infix('/', lambda x, y, *args, **kwargs: x / y)
division = Infix(' / ', lambda x, y, *args, **kwargs: x / y)
modulo = Infix(' % ', lambda x, y, *args, **kwargs: x % y)
positive = Prefix('+', lambda x, *args, **kwargs: x)
negative = Prefix('-', lambda x, *args, **kwargs: -x)
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
sin = Prefix('sin', sin_fn)
cos = Prefix('cos', cos_fn)
tan = Prefix('tan', tan_fn)
arcsin = Prefix('asin', arcsin_fn)
arccos = Prefix('acos', arccos_fn)
arctan = Prefix('atan', arctan_fn)
ln = Prefix('ln ', ln_fn)
weak_sin = Prefix('sin ', sin_fn)
weak_cos = Prefix('cos ', cos_fn)
weak_tan = Prefix('tan ', tan_fn)
weak_arcsin = Prefix('asin ', arcsin_fn)
weak_arccos = Prefix('acos ', arccos_fn)
weak_arctan = Prefix('atan ', arctan_fn)
weak_ln = Prefix('ln ', ln_fn)
weak_sqrt = Prefix('sqrt ', lambda x, *args, epsilon=None, **kwargs: exponentiation_fn(x, Number(1, 2, fcf=False), epsilon=epsilon))
sqrt = Prefix('sqrt', lambda x, *args, epsilon=None, **kwargs: exponentiation_fn(x, Number(1, 2, fcf=False), epsilon=epsilon))
exponentiation = Infix('^', exponentiation_fn)
factorial = Postfix('!', factorial_fn)

regex = {r'(?<!\s)(\/)(?!\s)': frac_div,
         r'\s+(\/)\s+': division,
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
        #  r'\s*(sin)(?:\s+|(?![A-Za-z_]))': sin,
        #  r'\s*(cos)(?:\s+|(?![A-Za-z_]))': cos,
        #  r'\s*(tan)(?:\s+|(?![A-Za-z_]))': tan,
        #  r'\s*(sqrt)(?:\s+|(?![A-Za-z_]))': sqrt,
        #  r'\s*(ln)(?:\s+|(?![A-Za-z_]))': ln,
         r'(sin)\s+': weak_sin,
         r'(cos)\s+': weak_cos,
         r'(tan)\s+': weak_tan,
         r'(arcsin|asin)\s+': weak_arcsin,
         r'(arccos|acos)\s+': weak_arccos,
         r'(arctan|atan)\s+': weak_arctan,
         r'(sqrt)\s+': weak_sqrt,
         r'(ln)\s+': weak_ln,
         r'(sin)(?![A-Za-z_])': sin,
         r'(cos)(?![A-Za-z_])': cos,
         r'(tan)(?![A-Za-z_])': tan,
         r'(arcsin|asin)(?![A-Za-z_])': arcsin,
         r'(arccos|acos)(?![A-Za-z_])': arccos,
         r'(arctan|atan)(?![A-Za-z_])': arctan,
         r'(sqrt)(?![A-Za-z_])': sqrt,
         r'(ln)(?![A-Za-z_])': ln,
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
         sin: (11.1, 10.9),
         cos: (11.1, 10.9),
         tan: (11.1, 10.9),
         arcsin: (11.1, 10.9),
         arccos: (11.1, 10.9),
         arctan: (11.1, 10.9),
         ln: (11.1, 10.9),
         negative: (11.1, 10.9),
         positive: (11.1, 10.9),
         implicit_mult_prefix: (10, 10),
         frac_div: (10.1, 9.9),
         weak_sqrt: (11.1, 8.9),
         weak_sin: (11.1, 8.9),
         weak_cos: (11.1, 8.9),
         weak_tan: (11.1, 8.9),
         weak_arcsin: (11.1, 8.9),
         weak_arccos: (11.1, 8.9),
         weak_arctan: (11.1, 8.9),
         weak_ln: (11.1, 8.9),
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