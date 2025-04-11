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
        if self < 0: return -(-self).fast_continued_fraction(epsilon=epsilon, max_denom=max_denom)
        # print(f'Fast continued fractions called on {str(self)}')
        if epsilon is None and max_denom is None:
            raise NumberError('No epsilon supplied, unable to perform FCF')
        elif epsilon is not None and max_denom is not None:
            raise NumberError("Fast continued fractions: Received 2 keyword args! Please provide only 1 keyword arg ('epsilon' or 'max_denom')")
        epsilon = epsilon or zero
        max_denom = max_denom or float('inf')

        lower, upper, alpha = (0, 1), (1, 0), abs(self)
        gamma = (alpha * lower[1] - lower[0]) / (-alpha * upper[1] + upper[0])
        prev = lower
        while True:
            s = int(gamma)
            lower = (lower[0] + s * upper[0], lower[1] + s * upper[1])
            # print(lower, s, lower[0] / lower[1])
            if abs(self - (num := RealNumber(lower, fcf=False))) < epsilon or gamma == s: return num
            if lower[1] > max_denom: return RealNumber(prev, fcf=False)
            prev = lower
            lower, upper = upper, lower
            gamma = one / (gamma - s)

    def __add__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): raise NumberError('Expected another Number')
        num = self.sign * self.numerator * other.denominator + other.sign * self.denominator * other.numerator
        denom = self.denominator * other.denominator
        return RealNumber(num, denom, fcf=False).simplify()
        
    def __neg__(self): return RealNumber(-self.sign * self.numerator, self.denominator, fcf=False)
    def __sub__(self, other): return self + (-other)
    def __mul__(self, other): return zero if other == 0 or zero == other else self / (one / other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): raise NumberError('Expected another Number')
        if other.sign == 0: raise ZeroDivisionError('Integer division by 0')
        return RealNumber(self.sign * other.sign * self.numerator * other.denominator, self.denominator * other.numerator, fcf=False).simplify()

    def __mod__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): raise NumberError('Expected another Number')
        if other.sign == 0: raise ZeroDivisionError('Integer division by 0')
        int_pieces = self / other
        int_pieces = int_pieces.sign * int_pieces.numerator // int_pieces.denominator
        return self - other * int_pieces

    def __gt__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): raise NumberError('Expected another Number')
        return (self - other).sign == 1

    def __lt__(self, other): return -self > -other

    def __eq__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): return False
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

    def __repr__(self):
        return ('-' if self.sign == -1 else '') + str(self.numerator) + ('' if self.denominator == 1 else '/' + str(self.denominator))

    def disp(self, frac_max_length, decimal_places):
        if self.denominator == 1: return str(self)
        s = str(self)
        if len(s) <= frac_max_length: return s + ' = ' + self.dec(dp=decimal_places)
        return self.dec(dp=decimal_places)


# 'Interning' some useful constants
zero = RealNumber(0)
one = RealNumber(1)
two = RealNumber(2)
ten = RealNumber(10)
e = RealNumber('2.718281828459045235360287471353')
pi = RealNumber('3.1415926535897932384626433832795')
ln2 = RealNumber(1554903831458736, 2243252046704767, fcf=False)
ln10 = RealNumber(227480160645689, 98793378510888, fcf=False)


class ComplexNumber(Value):
    def __init__(self, real, im=zero):
        self.real = real if isinstance(real, RealNumber) else RealNumber(real)
        self.im = im if isinstance(im, RealNumber) else RealNumber(im)
    
    def is_int(self):
        return self.im == 0 and self.real.is_int()
    
    def dec(self, dp=25):
        if self.im == 0: return self.real.dec(dp)
        if self.im > 0: return f"{self.real.dec(dp)} + {self.im.dec(dp)}"
        return f"{self.real.dec(dp)} - {abs(self.im.dec(dp))}"

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
        if self < 0: return -(-self).fast_continued_fraction(epsilon=epsilon, max_denom=max_denom)
        # print(f'Fast continued fractions called on {str(self)}')
        if epsilon is None and max_denom is None:
            raise NumberError('No epsilon supplied, unable to perform FCF')
        elif epsilon is not None and max_denom is not None:
            raise NumberError("Fast continued fractions: Received 2 keyword args! Please provide only 1 keyword arg ('epsilon' or 'max_denom')")
        epsilon = epsilon or zero
        max_denom = max_denom or float('inf')

        lower, upper, alpha = (0, 1), (1, 0), abs(self)
        gamma = (alpha * lower[1] - lower[0]) / (-alpha * upper[1] + upper[0])
        prev = lower
        while True:
            s = int(gamma)
            lower = (lower[0] + s * upper[0], lower[1] + s * upper[1])
            # print(lower, s, lower[0] / lower[1])
            if abs(self - (num := RealNumber(lower, fcf=False))) < epsilon or gamma == s: return num
            if lower[1] > max_denom: return RealNumber(prev, fcf=False)
            prev = lower
            lower, upper = upper, lower
            gamma = one / (gamma - s)

    def __add__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): raise NumberError('Expected another Number')
        num = self.sign * self.numerator * other.denominator + other.sign * self.denominator * other.numerator
        denom = self.denominator * other.denominator
        return RealNumber(num, denom, fcf=False).simplify()
        
    def __neg__(self): return RealNumber(-self.sign * self.numerator, self.denominator, fcf=False)
    def __sub__(self, other): return self + (-other)
    def __mul__(self, other): return zero if other == 0 or zero == other else self / (one / other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): raise NumberError('Expected another Number')
        if other.sign == 0: raise ZeroDivisionError('Integer division by 0')
        return RealNumber(self.sign * other.sign * self.numerator * other.denominator, self.denominator * other.numerator, fcf=False).simplify()

    def __mod__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): raise NumberError('Expected another Number')
        if other.sign == 0: raise ZeroDivisionError('Integer division by 0')
        int_pieces = self / other
        int_pieces = int_pieces.sign * int_pieces.numerator // int_pieces.denominator
        return self - other * int_pieces

    def __gt__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): raise NumberError('Expected another Number')
        return (self - other).sign == 1

    def __lt__(self, other): return -self > -other

    def __eq__(self, other):
        if isinstance(other, (int, float)): other = RealNumber(other)
        if not isinstance(other, RealNumber): return False
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

    def __repr__(self):
        return ('-' if self.sign == -1 else '') + str(self.numerator) + ('' if self.denominator == 1 else '/' + str(self.denominator))

    def disp(self, frac_max_length, decimal_places):
        if self.denominator == 1: return str(self)
        s = str(self)
        if len(s) <= frac_max_length: return s + ' = ' + self.dec(dp=decimal_places)
        return self.dec(dp=decimal_places)


# test code
if __name__ == '__main__':
    print(RealNumber(125842, 9999000).dec(30))
    print(RealNumber(-8,3).dec(20))
    print(RealNumber(9,11).dec(20))
    print(RealNumber(7,13).dec(20))
    print(RealNumber(538461,999999).dec(5))
    print(RealNumber(7,13).dec(20))
    pass