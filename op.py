from operators import *
from functions import Function
from errors import *
from vars import LValue
from number import *
from settings import Settings

st = Settings()

def factorialFn(n):
    if not n.isInt(): raise CalculatorError(f'Factorial operator expects an integer, not {str(n)}')
    n = int(n)
    if n in (0, 1): return one
    for i in range(2, n): n *= i
    return RealNumber(n)

def permutationFn(n, r):  # nPr
    return combinationFn(n, r, perm=True)

def combinationFn(n, r, perm=False):  # nCr
    if not n.isInt() or not r.isInt(): raise CalculatorError(f'Combination function expects integers')
    n, r = int(n), int(r)
    res = 1
    if n in (0, 1): return one
    for i in range(1, r + 1): res *= n + 1 - i; res //= i ** (not perm)
    return RealNumber(res)

def exponentiationFn(a, b):
    if isinstance(a, Function):
        if b.isInt(): return a ** b
        raise CalculatorError(f'Cannot raise a function ({str(a)}) to a fractional power {str(b)}')
    if a == zero:
        if b == zero: raise CalculatorError(f'0^0 is undefined')
        return zero
    if b.isInt() and (isinstance(a, RealNumber) or isinstance(a, ComplexNumber) and a.real.isInt() and a.im.isInt()):
        return intPower(a, int(b))
    elif isinstance(a, ComplexNumber) and isinstance(b, RealNumber):  # complex ^ real
        r = exponentiationFn(abs(a), b)
        theta = (a.arg() / pi).fastContinuedFraction() * b % two * pi
        return ComplexNumber(r * cosFn(theta), r * sinFn(theta)).fastContinuedFraction()
    # if isinstance(b, RealNumber) and b.sign == -1: return one / exponentiationFn(a, -b, *args, fcf=fcf, **kwargs)
    # a^b = e^(b ln a)
    return exp(b * lnFn(a))

def intPower(base, power):
    if not isinstance(power, int): raise CalculatorError(f'intPower() expects integral power, received {power}')
    pow = abs(power)
    result = one
    while pow > 0:
        if pow & 1: result *= base
        base = (base * base).fastContinuedFraction()
        pow >>= 1
    return (one / result if power < 0 else result).fastContinuedFraction()

def exp(x):
    if isinstance(x, ComplexNumber):  # e^(a + ib) = (e^a) e^(ib) = (e^a) cis b
        r = exp(x.real)
        return ComplexNumber(r * cosFn(x.im), r * sinFn(x.im))
    intPart = intPower(e, int(x))
    x = x.fracPart()
    sum = term = i = one
    while (abs(term) >= st.epsilon):
        term = (term * x) / i
        sum += term
        i += one
    return intPart * sum.fastContinuedFraction()

def lnFn(x):
    if x == zero: raise CalculatorError(f'ln 0 is undefined.')
    # ln(re^iθ) = ln r + iθ
    if isinstance(x, ComplexNumber): return ComplexNumber(lnFn(abs(x)), x.arg())
    if isinstance(x, RealNumber) and x < zero: return ComplexNumber(lnFn(abs(x)), pi)
    if x < one: return -lnFn(one / x)
    result = zero
    while x > ten:
        x /= ten
        result += ln10
    while x > two:
        x /= two
        result += ln2
    while True:
        x /= onePointOne
        result += ln1_1
        if x < one: break
    # ln (1 + x) = x - x^2/2 + x^3/3 - x^4/4 + x^5/5 - ...
    # ln (1 - x) = -x - x^2/2 - x^3/3 - x^4/4 - x^5/5 - ...
    xPow = dx = x = one - x
    denom = one
    while abs(dx) > st.epsilon:
        result -= dx
        xPow *= x
        denom += one
        dx = xPow / denom 
    return result.fastContinuedFraction()

def sinFn(x):
    if isinstance(x, ComplexNumber):
        eiz = exp(imag_i * x)
        return (eiz - (one / eiz)) / two / imag_i
    if x < zero: return -sinFn(-x)
    x = x % (pi * two)
    if x > pi * three / two: return -sinFn(pi * two - x)
    elif x > pi: return -sinFn(x - pi)
    elif x > pi / two: return sinFn(pi - x)
    sum = xPow = dx = x
    xSq = -x * x
    mul = fac = one
    while abs(dx) > st.epsilon:
        mul += two
        fac *= mul * (mul - one)
        xPow *= xSq
        dx = (xPow / fac).fastContinuedFraction()
        sum += dx
    return sum.fastContinuedFraction()

def cosFn(x):
    return sinFn(pi / two - x)

def tanFn(x):
    return sinFn(x) / cosFn(x)

def secFn(x):
    return one / cosFn(x)

def cscFn(x):
    return one / sinFn(x)

def cotFn(x):
    return one / tanFn(x)

def sinhFn(x):
    return ((ex := exp(x)) - one / ex) / two

def coshFn(x):
    return ((ex := exp(x)) + one / ex) / two

def tanhFn(x):
    return ((e2x := exp(two * x)) - one) / (e2x + one)

def arcsinFn(x):
    # https://en.wikipedia.org/wiki/List_of_mathematical_series
    if x.sign == -1: return -arcsinFn(-x)
    if x > one: raise CalculatorError('arcsin only accepts values from -1 to 1 inclusive')
    if x * x > -x * x + one: return pi / two - arcsinFn(exponentiationFn(-x * x + one, half))
    sum = term = x
    xsqr = x * x
    k = zero
    while abs(term) > st.epsilon:
        k += one
        term *= xsqr * (k * two) * (k * two - one) / four / k / k
        term = term.fastContinuedFraction()
        sum += term / (k * two + one)
    return sum.fastContinuedFraction()

def arccosFn(x):
    if x.sign == -1: return pi - arccosFn(-x)
    if x > one: raise CalculatorError('arccos only accepts values from -1 to 1 inclusive')
    return pi / two - arcsinFn(x)

def arctanFn(x):
    if x.sign == -1: return -arctanFn(-x)
    if x > one: return pi / two - arctanFn(one / x)
    # https://en.wikipedia.org/wiki/Arctangent_series
    sum = term = x / (x * x + one)
    factor = term * x
    num = two
    while abs(term) > st.epsilon:
        term *= factor
        term *= num
        term /= num + one
        term = term.fastContinuedFraction()
        sum += term
        sum = sum.fastContinuedFraction()
        num += two
    return sum

def absFn(x): return abs(x)
def conjFn(x): return x.conj()
def argFn(x): return x.arg()

def assignmentFn(L, R, mem=None):
    if mem is None: raise MemoryError('No Memory object passed to assignment operator')
    if not isinstance(L, LValue): raise TypeError('Can only assign to LValue')
    if isinstance(mem, dict):
        mem[L.name] = R
    else:
        mem.add(L.name, R)
    return R

assignment = Infix(' = ', assignmentFn)
spaceSeparator = Infix(' ', lambda x, y: x * y)
semicolonSeparator = Infix('; ', lambda x, y: y)
ternary_if = Ternary(' ? ', lambda cond, trueVal, falseVal: trueVal if cond else falseVal)
ternary_else = Ternary(' : ')
permutation = Infix('P', permutationFn)
combination = Infix('C', combinationFn)
ambiguousPlus = Operator('+?')
ambiguousMinus = Operator('-?')
addition = Infix(' + ', lambda x, y: x + y)
subtraction = Infix(' - ', lambda x, y: x - y)
multiplication = Infix(' * ', lambda x, y: x * y)
implicitMult = Infix('', lambda x, y: x * y)
implicitMultPrefix = Infix(' ', lambda x, y: x * y)
fracDiv = Infix('/', lambda x, y: x / y)
division = Infix(' / ', lambda x, y: x / y)
intDiv = Infix(' // ', lambda x, y: x // y)
modulo = Infix(' % ', lambda x, y: x % y)
positive = Prefix('+', lambda x: x)
negative = Prefix('-', lambda x: -x)
lt = Infix(' < ', lambda x, y: one if x < y else zero)
ltEq = Infix(' <= ', lambda x, y: one if x <= y else zero)
gt = Infix(' > ', lambda x, y: one if x > y else zero)
gtEq = Infix(' >= ', lambda x, y: one if x >= y else zero)
eq = Infix(' == ', lambda x, y: one if x == y else zero)
neq = Infix(' != ', lambda x, y: one if x != y else zero)
logicalAND = Infix(' && ', lambda x, y: x if x.sign == 0 else y)
logicalOR = Infix(' || ', lambda x, y: x if x.sign != 0 else y)
functionInvocation = Infix('<invoke>', lambda x, y, mem=None: x.invoke(y, mem=mem))
functionComposition = Infix('', lambda x, y: x.invoke(y))
sin = Prefix('sin', sinFn)
cos = Prefix('cos', cosFn)
tan = Prefix('tan', tanFn)
sec = Prefix('sec', secFn)
csc = Prefix('csc', cscFn)
cot = Prefix('cot', cotFn)
sinh = Prefix('sinh', sinhFn)
cosh = Prefix('cosh', coshFn)
tanh = Prefix('tanh', tanhFn)
arcsin = Prefix('asin', arcsinFn)
arccos = Prefix('acos', arccosFn)
arctan = Prefix('atan', arctanFn)
ln = Prefix('ln', lnFn)
lg = Prefix('lg', lambda x: lnFn(x) / ln10)
weakSin = Prefix('sin ', sinFn)
weakCos = Prefix('cos ', cosFn)
weakTan = Prefix('tan ', tanFn)
weakSec = Prefix('sec ', secFn)
weakCsc = Prefix('csc ', cscFn)
weakCot = Prefix('cot ', cotFn)
weakSinh = Prefix('sinh ', sinhFn)
weakCosh = Prefix('cosh ', coshFn)
weakTanh = Prefix('tanh ', tanhFn)
weakArcsin = Prefix('asin ', arcsinFn)
weakArccos = Prefix('acos ', arccosFn)
weakArctan = Prefix('atan ', arctanFn)
weakLn = Prefix('ln ', lnFn)
weakLg = Prefix('lg ', lambda x: lnFn(x) / ln10)
weakSqrt = Prefix('sqrt ', lambda x: exponentiationFn(x, half))
sqrt = Prefix('sqrt', lambda x: exponentiationFn(x, half))
absolute = PrefixFunction('abs', absFn)
argument = PrefixFunction('arg', argFn)
conjugate = PrefixFunction('conj', conjFn)
exponentiation = Infix('^', exponentiationFn)
factorial = Postfix('!', factorialFn)

regex = {
    r'\s*(\/\/)\s*': intDiv,
    r'\s+(\/)\s+': division,
    r'(?<!\s)(\/)(?!\s)': fracDiv,
    r'\s*(\*)\s*': multiplication,
    r'\s*(%)\s*': modulo,
    r'(!)': factorial,
    r'\s*(\^)\s*': exponentiation,
    r'\s*(\+)\s+': addition,
    r'\s*(\-)\s+': subtraction,
    r'\s*(>=)\s*': gtEq,
    r'\s*(<=)\s*': ltEq,
    r'\s*(==)\s*': eq,
    r'\s*(!=)\s*': neq,
    r'\s*(>)\s*': gt,
    r'\s*(<)\s*': lt,
    r'\s*(\?)\s*': ternary_if,
    r'\s*(:)\s*': ternary_else,
    r'\s*(\+)': ambiguousPlus,
    r'\s*(\-)': ambiguousMinus,
    r'\s*(&&)\s*': logicalAND,
    r'\s*(\|\|)\s*': logicalOR,
    r'\s*(=)\s*': assignment,
    r'(sinh)\s+': weakSinh,
    r'(cosh)\s+': weakCosh,
    r'(tanh)\s+': weakTanh,
    r'(sinh)(?![A-Za-z_])': sinh,
    r'(cosh)(?![A-Za-z_])': cosh,
    r'(tanh)(?![A-Za-z_])': tanh,
    r'(sin)\s+': weakSin,
    r'(cos)\s+': weakCos,
    r'(tan)\s+': weakTan,
    r'(sec)\s+': weakSec,
    r'(csc|cosec)\s+': weakCsc,
    r'(cot)\s+': weakCot,
    r'(arcsin|asin)\s+': weakArcsin,
    r'(arccos|acos)\s+': weakArccos,
    r'(arctan|atan)\s+': weakArctan,
    r'(sqrt)\s+': weakSqrt,
    r'(ln)\s+': weakLn,
    r'(lg)\s+': weakLg,
    r'(abs)(?![A-Za-z_])': absolute,
    r'(arg)(?![A-Za-z_])': argument,
    r'(conj)(?![A-Za-z_])': conjugate,
    r'(sin)(?![A-Za-z_])': sin,
    r'(cos)(?![A-Za-z_])': cos,
    r'(tan)(?![A-Za-z_])': tan,
    r'(sec)(?![A-Za-z_])': sec,
    r'(csc|cosec)(?![A-Za-z_])': csc,
    r'(cot)(?![A-Za-z_])': cot,
    r'(arcsin|asin)(?![A-Za-z_])': arcsin,
    r'(arccos|acos)(?![A-Za-z_])': arccos,
    r'(arctan|atan)(?![A-Za-z_])': arctan,
    r'(sqrt)(?![A-Za-z_])': sqrt,
    r'(ln)(?![A-Za-z_])': ln,
    r'(lg)(?![A-Za-z_])': lg,
    r'(\s)\s*': spaceSeparator,
    r'\s*(;)\s*': semicolonSeparator,
    r'(P)': permutation,
    r'(C)': combination,
}

power = {
    # functionInvocation: (10.1, 99),  (why did I choose such a low precedence for this)
    functionInvocation: (13, 99),
    factorial: (12, 12.1),
    implicitMult: (11, 11),
    exponentiation: (11.1, 10.9),
    sqrt: (11.1, 10.9),
    sin: (11.1, 10.9),
    cos: (11.1, 10.9),
    tan: (11.1, 10.9),
    sec: (11.1, 10.9),
    csc: (11.1, 10.9),
    cot: (11.1, 10.9),
    absolute: (11.1, 10.9),
    argument: (11.1, 10.9),
    conjugate: (11.1, 10.9),
    sinh: (11.1, 10.9),
    cosh: (11.1, 10.9),
    tanh: (11.1, 10.9),
    arcsin: (11.1, 10.9),
    arccos: (11.1, 10.9),
    arctan: (11.1, 10.9),
    ln: (11.1, 10.9),
    lg: (11.1, 10.9),
    negative: (11.1, 10.9),
    positive: (11.1, 10.9),
    implicitMultPrefix: (10, 10),
    fracDiv: (9.5, 9.5),
    weakSqrt: (11.1, 8.9),
    weakSin: (11.1, 8.9),
    weakCos: (11.1, 8.9),
    weakTan: (11.1, 8.9),
    weakSec: (11.1, 8.9),
    weakCsc: (11.1, 8.9),
    weakCot: (11.1, 8.9),
    weakSinh: (11.1, 8.9),
    weakCosh: (11.1, 8.9),
    weakTanh: (11.1, 8.9),
    weakArcsin: (11.1, 8.9),
    weakArccos: (11.1, 8.9),
    weakArctan: (11.1, 8.9),
    weakLn: (11.1, 8.9),
    weakLg: (11.1, 8.9),
    permutation: (9, 9),
    combination: (9, 9),
    intDiv: (8, 8),
    division: (8, 8),
    multiplication: (8, 8),
    modulo: (8, 8),
    spaceSeparator: (8, 8),
    subtraction: (7, 7),
    addition: (7, 7),
    gtEq: (6, 6),
    gt: (6, 6),
    ltEq: (6, 6),
    lt: (6, 6),
    eq: (5, 5),
    neq: (5, 5),
    logicalAND: (4, 4),
    logicalOR: (3, 3),
    assignment: (2, 1.9),
    ternary_if: (2, 0.5),
    ternary_else: (-1, 0.5),
    semicolonSeparator: (1, 1.1),
    # comma_separator: (1, 1),
    None: (0, 0),
}


# a ? b ? c : d : e
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