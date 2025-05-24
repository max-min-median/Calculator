from settings import Settings
from operators import *
import op
from vars import Value, Var, WordToken, LValue
from errors import CalculatorError, ParseError, EvaluationError
from functions import Function

st = Settings()
dummy = Var('dummy')


class Expression(Value):
    def __init__(self, inputStr=None, brackets='', parent=None, parentOffset=0):
        self.inputStr = inputStr  # only the part of the string relevant to this Expression.
        self.tokens = []
        self.tokenPos = []  # position of individual tokens within this Expression.
        self.parsed = None
        self.parsedPos = None
        self.brackets = brackets  # 2-char string, '()', '[]', '{}' or an empty string.
        self.parent = parent  # parent object
        self.parentOffset = parentOffset  # position of this Expression relative to parent

    def posOfElem(self, i, tup=None):  # returns a tuple describing the position of the i-th element in the full string.
        tupToUse = tup if tup is not None else self.parsedPos[i] if self.parsedPos is not None else self.tokenPos[i]
        return tuple(self.offset + x for x in tupToUse)

    @property
    def offset(self):
        return self.parentOffset + (0 if self.parent is None else self.parent.offset)

    @property
    def pos(self):
        return (self.offset, self.offset + len(self.inputStr))

    def value(self, mem, debug=False):

        def evaluate(power=0, index=0, skipEval=False):  # returns (Value, endIndex)
            def tryOperate(L, *args, **kwargs):
                try:
                    ret = dummy if skipEval else token.function(L, *args, **kwargs)
                    if debug: print(f"{str(token).strip(): ^3}:", ', '.join((str(L),) + tuple(str(a) for a in args)))
                    return ret
                except CalculatorError as e:
                    raise (type(e))(e.args[0], self.posOfElem(index))

            L = None
            while True:
                token = self.parsed[index]
                if isinstance(token, WordToken):
                    if self.parsed[index+1] == op.assignment:
                        self.parsed[index] = token.toLValue()
                    elif isinstance(self.parsed[index+1], Expression) and self.parsed[index+2] == op.assignment:  # make a function
                        self.parsed[index] = token.toLFunc()  # why does this not exist
                    else:
                        try:
                            splitList, varList = token.splitWordToken(mem, self.parsed[index+1])
                        except CalculatorError as e:
                            raise (type(e))(e.args[0], self.posOfElem(index))
                        self.parsed[index:index+1] = varList
                        prev = 0
                        self.parsedPos[index:index+1] = [(self.parsedPos[index][0] + prev, self.parsedPos[index][0] + (prev := prev + len(s))) for s in ([''] + splitList)[:-1]]
                    continue
                match L, token:
                    case None, Value():
                        L = dummy if skipEval else token.value(mem=mem)
                        index += 1
                        continue
                    # case None, Postfix() | Infix():
                    #     raise ParseError(f"Unexpected operator '{token.name}'", self.posOfElem(index))
                    # non-Fn-Fn : Low
                    # non-Fn-Prefix : Low
                    # non-Fn-non-Fn : High
                    # Fn-Fn : High
                    case Function(), Expression():
                        if not isinstance(token, Tuple):
                            tup = Tuple.fromExpr(token)
                            # tup = Tuple()
                            # tup.__dict__.update(token.__dict__)
                            # tup.tokens = [token]
                            self.parsed[index] = tup 
                        token = op.functionInvocation
                    case Value(), Function() | Prefix() if not isinstance(L, Function):  # Fn-Fn = High, nonFn-Fn = Low
                        # implicit mult of value to function / prefix, slightly lower precedence. For cases like 'sin2xsin3y'
                        # also need to handle stuff like 1/2()
                        token = op.implicitMultPrefix
                    case Value(), Value() | Expression():
                        token = op.implicitMult
                match token:
                    case Operator() if token.power[0] <= power: return L, index - 1
                    case Prefix():
                        L, index = evaluate(power=token.power[1], index=index+1, skipEval=skipEval)
                        L = tryOperate(L)
                    case Ternary():
                        if token == op.ternary_else:
                            raise ParseError("Unexpected operator ' : '", self.posOfElem(index))
                        from number import zero
                        ternaryIndex = index
                        if not skipEval: isTrue = op.eq.function(L, zero) == zero
                        trueVal, index = evaluate(power=token.power[1], index=index+1, skipEval=skipEval or not isTrue)
                        if self.parsed[index + 1] != op.ternary_else: raise ParseError("Missing else clause ':' for ternary operator", self.posOfElem(ternaryIndex))
                        falseVal, index = evaluate(power=op.ternary_else.power[1], index=index+2, skipEval=skipEval or isTrue)
                        if not skipEval: L = trueVal if isTrue else falseVal
                    case Postfix():
                        L = tryOperate(L)
                    case Infix():
                        from number import zero, one
                        if token == op.assignment and not isinstance(L, LValue): raise ParseError("Invalid LValue for assignment operator '='", self.posOfElem(index - 1))
                        oldIndex = index
                        exp, index = evaluate(power=token.power[1], index = index + 1 - (token in [op.implicitMult, op.implicitMultPrefix, op.functionInvocation]), skipEval = skipEval or token == op.logicalAND and op.eq.function(L, zero) == one or token == op.logicalOR and op.eq.function(L, zero) == zero)
                        if token != op.assignment and isinstance(exp, LValue): raise ParseError(f"Invalid operation on LValue", self.posOfElem(oldIndex))
                        L = tryOperate(L, exp, mem=mem) if token in (op.assignment, op.functionInvocation) else tryOperate(L, exp)
                    case None:
                        return L, index - 1
                index += 1

        # TODO - rewrite this part. Multiple assignment of functions should be possible, e.g. "f(x) = x^2; g(x) = 2x"
        # Line 52 is not entered because of this section, which assigns "f(x) = x + 1"
        match self.tokens[:3]:  # create new function
            case WordToken(), Expression(), op.assignment:
                name = self.tokens[0].name
                mem[name] = Function(name=self.tokens[0].name, params=self.tokens[1], expr=self)
                return mem[name]

        self.parsed = self.tokens + [None, None]
        self.parsedPos = self.tokenPos + [(9999, 9999), (9999, 9999)]
        # self.parsed = self.parsed or (self.tokens + [None, None])
        # self.parsedPos = self.parsedPos or (self.tokenPos + [(9999, 9999), (9999, 9999)])
        # if (result := evaluate()[0]) is None:
        #     raise CalculatorError("Expression is empty", self.pos)
        return evaluate()[0]


    def __str__(self):
        # from number import RealNumber
        s = ''
        for token in self.tokens:
            s += token.fromString if hasattr(token, 'fromString') else str(token)
        s = self.brackets[:1] + s + self.brackets[1:]
        return s

    def __repr__(self): return f"Expression('{str(self)}')"


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
        tup = Tuple()
        tup.__dict__.update(expr.__dict__)
        tup.tokens = [expr] if len(expr.tokens) > 0 else []
        expr.brackets = ''
        return tup

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
            elif not isinstance(expr.tokens[0], WordToken) or len(expr.tokens) > 1 and expr.tokens[1] != op.assignment:
                raise ParseError("Each parameter must be exactly one WordToken (with optional default expression)", expr.pos)
            else:
                expr.tokens[0] = expr.tokens[0].toLValue()

        self.__dict__.update(tupOrExpr.__dict__)
        if isinstance(tupOrExpr, Tuple):
            for token in self.tokens:
                token.parent = self
                checkExpr(token)
        else:  # if Expression, then make LTuple a parent of Expression
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