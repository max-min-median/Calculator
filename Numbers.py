from Errors import *
import math

class Number:
    def __init__(self, *inp, st_br=True):
        if len(inp) == 1: inp = inp[0]
        if isinstance(inp, float): inp = str(inp)
        if isinstance(inp, int):
            self.sign = (inp > 0) - (inp < 0)
            self.numerator = inp * self.sign
            self.denominator = 1
        elif isinstance(inp, str):
            from re import match
            if m := match(r'(-)?(\d+)(?:\.(\d*))?', inp) or match(r'(-)?(\d*)\.(\d+)', inp):
                sign, integer, decimal_fraction = ['' if x is None else x for x in m.groups()]
                self.numerator = int(integer + decimal_fraction)
                self.denominator = 10 ** len(decimal_fraction)
                self.sign = 0 if self.numerator == 0 else -1 if sign == '-' else 1
            elif m := match(r'(-)?(\d+)\/(\d+)', inp):
                sign, num, denom = m.groups()
                self.numerator = int(num)
                self.denominator = int(denom)
                if self.denominator == 0: raise ZeroDivisionError('Denominator cannot be 0')
                self.sign = 0 if self.numerator == 0 else -1 if sign == '-' else 1
            else:
                raise NumberError('Cannot parse string. Try "-43.642" or "243" or "-6/71" etc')
            # handle negative numbers
        elif isinstance(inp, tuple) and len(inp) == 2 and isinstance(inp[0], int) and isinstance(inp[1], int):
            self.sign = 0 if inp[0] == 0 else -1 if (inp[0] < 0) + (inp[1] < 0) == 1 else 1
            self.numerator, self.denominator = abs(inp[0]), abs(inp[1])
        else:
            raise NumberError("Usage: Number(int) | Number(str) | Number(int, int) | Number((int, int))")
        self.simplify()
        if st_br and self.denominator > 10000 and self.denominator / self.numerator < 500:
            sb = self.stern_brocot(epsilon=Number(1,10**12))
            self.numerator = sb.numerator
            self.denominator = sb.denominator
    
    def is_int(self):
        return self.denominator == 1
    
    def simplify(self):
        div = math.gcd(self.numerator, self.denominator)
        self.numerator = int(self.numerator / div)
        self.denominator = int(self.denominator / div)

    def stern_brocot(self, epsilon=None, max_denom=math.inf):
        if epsilon is None and max_denom == math.inf:
            raise NumberError("Stern-Brocot tree search requires at least 1 keyword argument: 'epsilon' or 'max_denom'")
        if epsilon is None: epsilon = Number(0, 1, st_br=False)
        whole, frac = self.whole_part(), self.frac_part()
        lower, current, upper = (0, 1), (1, 2), (1, 1)
        closest_frac, smallest_diff = Number(current, st_br=False), Number(1, 1, st_br=False)

        while current[1] < max_denom:
            diff = frac - Number(current, st_br=False)
            abs_diff = abs(diff)
            if abs_diff < smallest_diff:
                smallest_diff = abs_diff
                closest_frac = current
            if abs_diff <= epsilon: break
            if diff.sign > 0:
                lower, current = current, (current[0] + upper[0], current[1] + upper[1])
            else:
                current, upper = (lower[0] + current[0], lower[1] + current[1]), current
        return (Number(closest_frac, st_br=False) + whole) * Number(self.sign, 1, st_br=False)

    def __add__(self, other):
        if not isinstance(other, Number): raise TypeError('Expected another Number')
        num = self.sign * self.numerator * other.denominator + other.sign * self.denominator * other.numerator
        denom = self.denominator * other.denominator
        return Number(num, denom, st_br=False)
        
    def __neg__(self):
        return Number(-self.numerator, self.denominator, st_br=False)

    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, other):
        return self / (Number(1, 1, st_br=False) / other)

    def __truediv__(self, other):
        if not isinstance(other, Number): raise TypeError('Expected another Number')
        return Number(self.sign * other.sign * self.numerator * other.denominator, self.denominator * other.numerator, st_br=False)

    def __gt__(self, other):
        if not isinstance(other, Number): raise TypeError('Expected another Number')
        return (diff := self - other).sign == 1 and diff.numerator > 0

    def __lt__(self, other):
        return other > self

    def __eq__(self, other):
        if not isinstance(other, Number): raise TypeError('Expected another Number')
        return (self - other).numerator == 0

    def __ne__(self, other):
        return not self == other

    def __ge__(self, other):
        return not self < other
    
    def __le__(self, other):
        return not self > other
    
    def __abs__(self):
        return Number(self.numerator, self.denominator, st_br=False)
    
    def whole_part(self):
        return Number(self.numerator // self.denominator, 1, st_br=False)

    def frac_part(self):
        return Number(self.numerator % self.denominator, self.denominator, st_br=False)

    def __str__(self):
        return ('-' if self.sign == -1 else '') + str(self.numerator) + ('' if self.denominator == 1 else '/' + str(self.denominator))

"""
a = Number('0.75') # 3/4
b = Number('0.4') # 2/5
c = Number((1, 3)) # 1/3
pi = Number('3.1415926535897932384626')
e = Number('2.7182818284590452353602874713526624')
print(str(e))
print(str(e.stern_brocot(max_denom = 5000)))
print(str(pi))
print(pi.stern_brocot(max_denom = 5000))
"""

pass