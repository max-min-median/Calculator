from errors import *
from vars import Value

class RealNumber(Value):

    @staticmethod
    def gcd(a, b):
        while a != 0:
            a, b = b % a, a
        return b


    def __init__(self, *inp, fcf=True, epsilon=None, max_denom=None):
        if len(inp) == 1: inp = inp[0]
        if isinstance(inp, float): inp = str(inp)
        if isinstance(inp, int):
            self.sign = (inp > 0) - (inp < 0)
            self.numerator = inp * self.sign
            self.denominator = 1
        elif isinstance(inp, str):
            from re import match
            if m := match(r'^(-)?(\d+)(?:\.(\d*))?$', inp) or match(r'(-)?(\d*)\.(\d+)', inp):  # integer or float
                sign, integer, decimal_fraction = ['' if x is None else x for x in m.groups()]
                self.numerator = int(integer + decimal_fraction)
                self.denominator = 10 ** len(decimal_fraction)
                epsilon = epsilon or RealNumber(1, 2 * 10 ** max(len(decimal_fraction), 30), fcf=False)
                self.sign = 0 if self.numerator == 0 else -1 if sign == '-' else 1
            elif m := match(r'^(-)?(\d+)\/(\d+)$', inp):  # fraction
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
            raise NumberError("Usage: Number(int [, int] | float | str | (int, int), fcf=True, epsilon=None, max_denom=None)")

        if self.denominator != 1:
            self.simplify()
            if fcf and (epsilon is not None or max_denom is not None and self.denominator > max_denom):
                new_frac = self.fast_continued_fraction(epsilon=epsilon, max_denom=max_denom)
                self.numerator = new_frac.numerator
                self.denominator = new_frac.denominator
    
    def is_int(self):
        return self.denominator == 1

    def __int__(self): return self.numerator // self.denominator * self.sign
    def __float__(self): return self.numerator / self.denominator * self.sign
    
    def dec(self, dp=25):
        s = '-' if self.sign == -1 else ''
        s += str(self.numerator // self.denominator)
        rem = self.numerator % self.denominator
        if rem == 0: return s
        rem_lst = []
        s += '.'
        frac = ''
        while rem and len(frac) <= dp:
            if rem in rem_lst: return s + frac[:(i := rem_lst.index(rem))] + '(' + frac[i:] + ')*'  # repeated decimal representation
            rem_lst.append(rem)
            rem *= 10
            frac = frac + str(rem // self.denominator)
            rem %= self.denominator

        if len(frac) <= dp or frac[-1] in '01234': return s + frac[:dp]
        # At this point we don't have a repeated decimal representation, but rounding is required
        s = [ch for ch in s + frac[:-1]]
        for i in range(len(s))[::-1]:
            match s[i]:
                case '-': s[i] = '-1'
                case '.': continue
                case '9': s[i] = '10' if i == 0 else '0'
                case x: s[i] = str(int(x) + 1); break
        return ''.join(s[:-1] if dp == 0 else s)

    def simplify(self):
        div = RealNumber.gcd(self.numerator, self.denominator)
        self.numerator = self.numerator // div
        self.denominator = self.denominator // div
        return self

    def stern_brocot(self, epsilon=None, max_denom=float('inf')):
        if epsilon is None and max_denom == float('inf'):
            raise NumberError("Stern-Brocot tree search requires at least 1 keyword argument: 'epsilon' or 'max_denom'")
        if epsilon is None: epsilon = zero
        whole, frac = self.whole_part(), self.frac_part()
        lower, current, upper = (0, 1), (1, 2), (1, 1)
        closest_frac, smallest_diff = RealNumber(current, fcf=False), one

        while current[1] < max_denom:
            diff = frac - RealNumber(current, fcf=False)
            abs_diff = abs(diff)
            if abs_diff < smallest_diff:
                smallest_diff = abs_diff
                closest_frac = current
            if abs_diff <= epsilon: break
            if diff.sign > 0:
                lower, current = current, (current[0] + upper[0], current[1] + upper[1])
            else:
                current, upper = (lower[0] + current[0], lower[1] + current[1]), current
        return (RealNumber(closest_frac, fcf=False) + whole) * RealNumber(self.sign, 1, fcf=False)

    def fast_continued_fraction(self, epsilon=None, max_denom=None):
        if self.sign == -1: return -(-self).fast_continued_fraction(epsilon=epsilon, max_denom=max_denom)
        # print(f'Fast continued fractions called on {str(self)}')
        if epsilon is None and max_denom is None:
            raise NumberError('No epsilon supplied, unable to perform FCF')
        elif epsilon is not None and max_denom is not None:
            raise NumberError("Fast continued fractions: Received 2 keyword args! Please provide only 1 keyword arg ('epsilon' or 'max_denom')")
        if epsilon is None: epsilon = zero
        if max_denom is None: max_denom = 'inf'

        lower, upper, alpha = (zero, one), (one, zero), abs(self)
        gamma = (alpha * lower[1] - lower[0]) / (-alpha * upper[1] + upper[0])
        prev = lower
        while True:
            s = gamma - gamma % one
            lower = (lower[0] + s * upper[0], lower[1] + s * upper[1])
            # print(lower, s, lower[0] / lower[1])
            if lower[1] != zero and abs(self - (num := lower[0] / lower[1])) < epsilon or gamma == s: return num
            if max_denom != 'inf' and lower[1] > max_denom: return RealNumber(prev, fcf=False)
            prev = lower
            lower, upper = upper, lower
            gamma = one / (gamma - s)

    def __add__(self, other):
        # if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): return NotImplemented
        num = self.sign * self.numerator * other.denominator + other.sign * self.denominator * other.numerator
        denom = self.denominator * other.denominator
        return RealNumber(num, denom, fcf=False).simplify()
        
    def __neg__(self): return RealNumber(-self.sign * self.numerator, self.denominator, fcf=False)
    def __sub__(self, other): return self + (-other)

    def __mul__(self, other):
        if not isinstance(other, RealNumber): return NotImplemented
        return RealNumber(self.sign * other.sign * self.numerator * other.numerator, self.denominator * other.denominator, fcf=False).simplify()

    def __truediv__(self, other):
        # if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): return NotImplemented
        if other.sign == 0:
            raise ZeroDivisionError('Division by 0 (RealNumber)')
        return RealNumber(self.sign * other.sign * self.numerator * other.denominator, self.denominator * other.numerator, fcf=False).simplify()

    def __mod__(self, other):
        # if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): return NotImplemented
        if other.sign == 0: raise ZeroDivisionError('Cannot modulo by 0')
        int_pieces = self / other
        int_pieces = RealNumber(int_pieces.sign * int_pieces.numerator // int_pieces.denominator)
        return self - other * int_pieces

    def __gt__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): raise NumberError('Expected another Number')
        return (self - other).sign == 1

    def __lt__(self, other): return -self > -other


    def __eq__(self, other):
        # if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): return NotImplemented
        return (self - other).sign == 0

    def __ne__(self, other): return not self == other
    def __ge__(self, other): return not self < other
    def __le__(self, other): return not self > other
    def __abs__(self): return RealNumber(self.numerator, self.denominator, fcf=False)

    def frac_part(self): return RealNumber(self.numerator % self.denominator * self.sign, self.denominator, fcf=False)
    
    def value(self, *args, **kwargs):
        return self

    def __str__(self):
        return ('-' if self.sign == -1 else '') + str(self.numerator) + ('' if self.denominator == 1 else '/' + str(self.denominator))

    def __repr__(self): return str(self)

    def disp(self, frac_max_length, decimal_places):
        if self.denominator == 1: return str(self)
        s = str(self)
        if len(s) <= frac_max_length: return s + ' = ' + self.dec(dp=decimal_places)
        return self.dec(dp=decimal_places)


# 'Interning' some useful constants
zero = RealNumber(0)
one = RealNumber(1)
two = RealNumber(2)
three = RealNumber(3)
ten = RealNumber(10)
e = RealNumber('2.718281828459045235360287471353')
pi = RealNumber('3.1415926535897932384626433832795')
ln2 = RealNumber(1554903831458736, 2243252046704767, fcf=False)
ln10 = RealNumber(227480160645689, 98793378510888, fcf=False)
half = RealNumber(1, 2, fcf=False)


class ComplexNumber(Value):  # Must be non-real valued, i.e. must have an imaginary part.

    def __new__(cls, real, im=zero):
        if im == zero: return real
        return super().__new__(cls)

    def __init__(self, real, im):
        self.real = real
        self.im = im
    
    def dec(self, dp=25):
        if self.real.sign == 0:
            return f"{'-' if self.im.sign == -1 else ''}{self.im.dec(dp) if abs(self.im) != one else ''}i"
        else:
            return f"{self.real.dec(dp)}{' + ' if self.im.sign == 1 else ' - '}{abs(self.im).dec(dp) if abs(self.im) != one else ''}i"

    def simplify(self):
        self.real.simplify()
        self.im.simplify()
        return self

    def fast_continued_fraction(self, epsilon=None, max_denom=None):
        return ComplexNumber(self.real.fast_continued_fraction(epsilon=epsilon, max_denom=max_denom), self.im.fast_continued_fraction(epsilon=epsilon, max_denom=max_denom))

    def conj(self): return ComplexNumber(self.real, -self.im)
    
    def reciprocal(self): return self.conj() / (self.real * self.real + self.im * self.im)

    def __add__(self, other):
        if isinstance(other, RealNumber): return ComplexNumber(self.real + other, self.im)
        return ComplexNumber(self.real + other.real, self.im + other.im)

    def __radd__(self, other):
        if isinstance(other, RealNumber): return self + ComplexNumber(other, zero)
        return NotImplemented

    def __neg__(self): return ComplexNumber(-self.real, -self.im)
    def __sub__(self, other): return self + (-other)

    def __mul__(self, other):
        if other == zero: return zero
        if isinstance(other, RealNumber): return ComplexNumber(self.real * other, self.im * other)
        return ComplexNumber(self.real * other.real - self.im * other.im, self.real * other.im + self.im * other.real)

    def __rmul__(self, other):
        if isinstance(other, RealNumber): return self * other
        return NotImplemented

    def __truediv__(self, other):
        if other == zero: raise ZeroDivisionError('Division by 0 (ComplexNumber)')
        if isinstance(other, RealNumber): return ComplexNumber(self.real / other, self.im / other)
        if not isinstance(other, ComplexNumber): return NotImplemented
        return self * other.reciprocal()

    def __rtruediv__(self, other):
        if isinstance(other, RealNumber): return self.reciprocal() * other
        return NotImplemented

    def abs(self, epsilon=None):
        from op import exponentiation_fn
        return exponentiation_fn(self.real * self.real + self.denominator * self.denominator, half, epsilon=epsilon, fcf=True)

    def __gt__(self, other):
        raise TypeError('Complex value has no total ordering')

    def __lt__(self, other): return -self > -other

    def __eq__(self, other):
        if isinstance(other, (int, float, RealNumber)): return False
        return self.real == other.real and self.im == other.im

    def __ne__(self, other): return not self == other
    def __ge__(self, other): return not self < other
    def __le__(self, other): return not self > other

    def value(self, *args, **kwargs):
        return self

    def __str__(self):
        if self.real.sign == 0:
            return f"{'-' if self.im.sign == -1 else ''}{str(self.im) if abs(self.im) != one else ''}{' ' if self.im.denominator != 1 else ''}i"
        else:
            return f"{str(self.real)}{' + ' if self.im.sign == 1 else ' - '}{str(abs(self.im)) if abs(self.im) != one else ''}{' ' if self.im.denominator != 1 else ''}i"

    def __repr__(self): return str(self)

    def disp(self, frac_max_length, decimal_places):
        if self.real.denominator == 1 and self.im.denominator == 1: return str(self)
        if len(str(self.real)) <= frac_max_length and len(str(self.im)) <= frac_max_length:
            return str(self) + ' = ' + self.dec(dp=decimal_places)
        return self.dec(dp=decimal_places)

imag_i = ComplexNumber(zero, one)

# test code
if __name__ == '__main__':
    a = RealNumber(2, 5)
    b = RealNumber(1, 4)
    assert a + b == RealNumber(13, 20)
    assert a / b == RealNumber(8, 5)
    assert a * b == RealNumber(1, 10)
    assert a - b == RealNumber(3, 20)
    c = ComplexNumber(RealNumber(5), RealNumber(2))
    d = ComplexNumber(RealNumber(3), RealNumber(-1))
    pass