from settings import Settings
from errors import ParseError
from expressions import Expression
from vars import LValue, WordToken
import op

st = Settings()
ONE_TUPLE_INDICATOR = ':'  # to be placed before the end bracket, e.g. (3:)

class Tuple(Expression):  # Tuple elements are all Expressions

    def __init__(self, inputStr=None, brackets='()', parent=None, parentOffset=0):
        super().__init__(inputStr=inputStr, brackets=brackets, parent=parent, parentOffset=parentOffset)

    @staticmethod
    def fromFirst(expr):  # begins the making of a Tuple from the first character after '('
        tup = Tuple(inputStr=expr.inputStr, brackets=expr.brackets, parent=expr.parent, parentOffset=expr.parentOffset)
        tup.tokens = [expr]
        expr.parent = tup
        return tup

    @staticmethod
    def fromExpr(expr):
        tup = expr.morphCopy(Tuple)
        if len(expr.tokens) == 0:
            tup.tokens = []
        else:
            cpy = expr.morphCopy()
            cpy.brackets = ''
            tup.tokens = [cpy]
        return tup

    def toExpr(self):
        if len(self.tokens) != 1: raise TypeError("Cannot convert Tuple to Expression because tuple does not have exactly 1 expression")
        expr = self.tokens[0]
        expr.parent = self.parent
        expr.brackets = self.brackets
        return expr

    def disp(self, fracMaxLength, decimalPlaces):
        tempTokens = [token.fastContinuedFraction(epsilon=st.finalEpsilon) if hasattr(token, 'fastContinuedFraction') else token for token in self.tokens]
        return self.brackets[:1] + ', '.join(['-' if x is None else x.disp(fracMaxLength, decimalPlaces) for x in tempTokens]) + self.brackets[1:]

    def __len__(self): return len(self.tokens)

    def __iter__(self): return iter(self.tokens)

    def __gt__(self, other):
        if not isinstance(other, Tuple): return NotImplemented
        for e1, e2 in zip(self, other):
            if e1 > e2: return True
        else:
            return len(e1) > len(e2)

    def __lt__(self, other):
        if not isinstance(other, Tuple): return NotImplemented
        for e1, e2 in zip(self, other):
            if e1 < e2: return True
        else:
            return len(e1) < len(e2)

    def __eq__(self, other):
        if not isinstance(other, Tuple): return NotImplemented
        for e1, e2 in zip(self, other):
            if e1 != e2: return False
        else:
            return len(e1) == len(e2)

    def __ne__(self, other): return not self == other
    def __ge__(self, other): return not self < other
    def __le__(self, other): return not self > other


    def __str__(self):
        return self.brackets[:1] + ', '.join([str(x) for x in self.tokens]) + (':' if len(self) == 1 else '') + self.brackets[1:]

    def value(self, mem=None):
        tup = Tuple(inputStr=self.inputStr, brackets=self.brackets, parent=self.parent, parentOffset=self.parentOffset)
        tup.tokenPos = self.tokenPos
        tup.tokens = [expr.value(mem=mem) for expr in self.tokens]
        return tup

    def __repr__(self): return f"Tuple('{str(self)}')"


class LTuple(LValue, Tuple):  # LTuple elements are all Expressions.

    def __init__(self, tupOrExpr):

        # check validity - each param Expression must be either one WordToken, or a WordToken followed by op.assignment, or a Tuple (which will be converted to LTuple)
        def checkExpr(expr):
            if isinstance(expr.tokens[0], Tuple) and not isinstance(expr.tokens[0], LTuple):
                expr.tokens[0] = LTuple(expr.tokens[0])
            elif not isinstance(expr.tokens[0], (WordToken, LValue)) or len(expr.tokens) > 1 and expr.tokens[1] != op.assignment:
                raise ParseError("Each parameter must be exactly one WordToken or LValue (with optional default expression)", expr.pos)
            elif isinstance(expr.tokens[0], WordToken):
                expr.tokens[0] = expr.tokens[0].morphCopy(LValue)

        self.__dict__.update(tupOrExpr.__dict__)
        if isinstance(tupOrExpr, Tuple):
            for token in self.tokens:
                token.parent = self
                checkExpr(token)
        else:  # if Expression, then make LTuple a parent of Expression
            tupOrExpr = tupOrExpr.morphCopy()
            tupOrExpr.parent = self
            tupOrExpr.parentOffset = 0
            tupOrExpr.brackets = ''
            checkExpr(tupOrExpr)
            self.tokens = [tupOrExpr]


    def assign(self, R, mem=None):

        def assignOneParam(param, val):  # each param of an LTuple is an Expression
            if val is None:  # then use default parameter. Check for WordToken followed by op.assignment
                if not isinstance(param, Expression) or len(param.tokens) < 3 or not isinstance(param.tokens[0], LValue) or param.tokens[1] != op.assignment:
                    raise ParseError("Parameter without default argument cannot be omitted")
                return param.value(mem)
            else:
                return op.assignmentFn(param.tokens[0], val, mem=mem)

        if mem is None: raise MemoryError('LTuple requires memory object to perform assignment')
        if len(R) > len(self): raise ParseError(f"Cannot destructure a {f"tuple of size {len(R)}" if isinstance(R, Tuple) else "value"} into an LTuple of size {len(self)}")
        if len(self) == 1 and not isinstance(R, Expression):
            return assignOneParam(self.tokens[0], R)
        else:
            for i, param in enumerate(self.tokens):
                val = R.tokens[i] if i < len(R) else None
                if isinstance(param, LTuple):
                    param.assign(val, mem=mem)
                else:
                    assignOneParam(param, val)
        return R

    def __str__(self):
        return self.brackets[:1] + ', '.join([str(x) for x in self.tokens]) + self.brackets[1:]

    def __repr__(self): return f"LTuple('{str(self)}')"