from vars import Value
from errors import ParseError, EvaluationError

# Functions must be followed by bracketed expressions, unlike Unary_Left_Operators.
# Trig fns and sqrt are therefore treated as Unary_Left_Operators.
# ffg(7), f(g(3, 4)), (fg^2)(x), (f(fg)^2)(7)


class Function(Value):
    def __init__(self, name='<fn>', params=None, expr=None):
        from expressions import Tuple
        from vars import WordToken
        self.name = name
        self.function = self.invoke
        self.funcList = [self]
        if expr is not None:
            self.expression = expr
            expr.tokens = expr.tokens[3:]
            expr.inputStr = expr.inputStr[expr.tokenPos[3][0]:]
            expr.tokenPos = [(a - expr.tokenPos[3][0], b - expr.tokenPos[3][0]) for (a, b) in expr.tokenPos[3:]]
        self.params = {}
        self.wordDict = {}  # wordDict is rebuilt when main memory changes.
        self.wordDictVer = -1
        if params is not None:
            paramTmpLst = params.tokens if isinstance(params, Tuple) else [params]  # for functions with 1 param, wrap the Expression in a list
            for i, x in enumerate(paramTmpLst):
                if len(x.tokens) != 1 or not isinstance(x.tokens[0], WordToken): raise ParseError('Each parameter should be exactly one WordToken', params.posOfElem(i))
                self.params[x.tokens[0].name] = None

    def value(self, *args, **kwargs):
        return self
    
    def __str__(self):
        if hasattr(self, 'params') and hasattr(self, 'expression'):
            return f"{self.name}({', '.join(list(self.params))}) = {self.expression}"
        else:
            return self.name

    def invoke(self, tupOrExpr, mem=None):
        if mem is None:  raise EvaluationError(f"No memory passed to function '{self.name}'")
        from expressions import Tuple
        from memory import Memory
        funcInputs = [] if tupOrExpr is None else \
                      [tupOrExpr] if not isinstance(tupOrExpr, Tuple) else \
                      tupOrExpr.tokens  # to make funcInputs a list of Expressions.
        if len(funcInputs) != len(self.params): raise EvaluationError(f"Function '{self.name}' expects {len(self.params)} parameters but received {len(funcInputs)}")
        if isinstance(mem, Memory):
            if self.wordDictVer < mem._varsVersion:
                self.wordDict = Memory.combine(mem, self.params)
                self.wordDictVer = mem._varsVersion
                self.expression.parsed = self.expression.parsedPos = None
            thisInvocationDict = self.wordDict.copy()
        else:
            thisInvocationDict = mem.copy()
        # store inputs into own copy of wordDict
        for k, v in list(zip(self.params, funcInputs)): thisInvocationDict[k] = v
        # evaluate the expression
        return self.expression.value(mem=thisInvocationDict)

    def __mul__(self, other):
        if not isinstance(other, Function): raise EvaluationError('Incorrect type for function composition')
        return FuncComposition(*self.funcList, *other.funcList)

    def __pow__(self, other):
        other = int(other)
        if not other > 0: raise EvaluationError('Functional power must be a positive integer')
        return FuncComposition(*(self.funcList * int(other)))

class FuncComposition(Function):
    def __init__(self, *funcList):
        self.name = ''.join([fn.name for fn in funcList])
        self.funcList = list(funcList)
        self.function = self.invoke

    def invoke(self, tupOrExpr, mem=None):
        res = tupOrExpr
        for fn in self.funcList[::-1]:
            res = fn.invoke(res, mem=mem)
        return res
