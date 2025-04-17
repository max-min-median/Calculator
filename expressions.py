from settings import Settings
from operators import *
import op
from vars import Value, Var, WordToken, LValue
from errors import CalculatorError, ParseError
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
        self.displayStr = ''

    def posOfElem(self, i=None, tup=None):  # returns a tuple describing the position of the i-th element in the full string.
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
                        self.parsed[index] = token.toLFunc()
                    else:
                        splitList, varList = token.splitWordToken(mem, self.parsed[index+1])
                        self.parsed[index:index+1] = varList
                        prev = 0
                        self.parsedPos[index:index+1] = [(self.parsedPos[index][0] + prev, self.parsedPos[index][0] + (prev := prev + len(s))) for s in ([''] + splitList)[:-1]]
                    continue
                match L, token:
                    case None, Value():
                        L = dummy if skipEval else token.value(mem=mem)
                        index += 1
                        continue
                    case None, Postfix() | Infix():
                        raise ParseError(f"Unexpected operator '{token.name}'", self.posOfElem(index))
                    # non-Fn-Fn : Low
                    # non-Fn-Prefix : Low
                    # non-Fn-non-Fn : High
                    # Fn-Fn : High
                    case Function(), Expression():
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
                        isTrue = op.eq.function(L, zero) == zero
                        trueVal, index = evaluate(power=token.power[1], index=index+1, skipEval=skipEval or not isTrue)
                        if self.parsed[index + 1] != op.ternary_else: raise ParseError("Missing else clause ':' for ternary operator", self.posOfElem(ternaryIndex))
                        falseVal, index = evaluate(power=op.ternary_else.power[1], index=index+2, skipEval=skipEval or isTrue)
                        L = trueVal if isTrue else falseVal
                    case Postfix():
                        L = tryOperate(L)
                    case Infix():
                        from number import zero, one
                        oldIndex = index
                        exp, index = evaluate(power=token.power[1], index = index + 1 - (token in [op.implicitMult, op.implicitMultPrefix, op.functionInvocation]), skipEval = skipEval or token == op.logicalAND and op.eq.function(L, zero) == one or token == op.logicalOR and op.eq.function(L, zero) == zero)
                        if token == op.assignment and not isinstance(L, LValue): raise ParseError("Invalid LValue for assignment operator '='", self.posOfElem(oldIndex))
                        elif token != op.assignment and isinstance(exp, LValue): raise ParseError(f"Invalid operation on LValue", self.posOfElem(oldIndex))
                        else: L = tryOperate(L, exp, mem=mem) if token in (op.assignment, op.functionInvocation) else tryOperate(L, exp)
                    case None:
                        return L, index - 1
                index += 1

        match self.tokens[:3]:  # create new function
            case WordToken(), Expression(), op.assignment:
                if isinstance(mem, dict):
                    name = self.tokens[0].name
                    mem[name] = (fn := Function(name=self.tokens[0].name, params=self.tokens[1], expr=self))
                else:
                    mem.add(self.tokens[0].name, fn := Function(name=self.tokens[0].name, params=self.tokens[1], expr=self))
                return fn
            
        self.parsed = self.parsed or (self.tokens + [None, None])
        self.parsedPos = self.parsedPos or (self.tokenPos + [(9999, 9999), (9999, 9999)])
        return evaluate()[0]
            
    def __str__(self):
        # from number import RealNumber
        if self.displayStr == '':
            # prevToken = None
            for token in self.tokens:
                # if isinstance(prevToken, (RealNumber, Var, Postfix)) and isinstance(token, (Var, Prefix)): self.displayStr += '⋅' + str(token)
                # else: self.displayStr += str(token)
                self.displayStr += token.fromString if hasattr(token, 'fromString') else str(token)
                # prevToken = token
            self.displayStr = self.brackets[:1] + self.displayStr + self.brackets[1:]
        return self.displayStr


class Tuple(Expression):

    def __init__(self, inputStr=None, brackets='()', parent=None, parentOffset=0):
        super().__init__(inputStr=inputStr, brackets=brackets, parent=parent, parentOffset=parentOffset)

    @staticmethod
    def fromFirst(expr):  # begins the making of a Tuple from the first character after '('
        tup = Tuple(inputStr=expr.inputStr, brackets=expr.brackets, parent=expr.parent, parentOffset=expr.parentOffset)
        tup.tokens = [expr]
        return tup

    def disp(self, fracMaxLength, decimalPlaces):
        tempTokens = [token.fastContinuedFraction(epsilon=st.finalEpsilon) if hasattr(token, 'fastContinuedFraction') else token for token in self.tokens]
        self.displayStr = self.brackets[:1] + ', '.join([x.disp(fracMaxLength, decimalPlaces) for x in tempTokens]) + self.brackets[1:]
        return self.displayStr

    def __str__(self):
        if self.displayStr == '':
            self.displayStr = self.brackets[:1] + ', '.join([str(x) for x in self.tokens]) + self.brackets[1:]
        return self.displayStr

    def value(self, mem=None):
        tup = Tuple(inputStr=self.inputStr, brackets=self.brackets, parent=self.parent, parentOffset=self.parentOffset)
        tup.tokenPos = self.tokenPos
        tup.tokens = [expr.value(mem=mem) for expr in self.tokens]
        return tup