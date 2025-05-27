from vars import Value
from errors import ParseError, EvaluationError

# Functions must be followed by bracketed expressions, unlike Unary_Left_Operators.
# Trig fns and sqrt are therefore treated as Unary_Left_Operators.
# ffg(7), f(g(3, 4)), (fg^2)(x), (f(fg)^2)(7)


class Function(Value):

    def __init__(self, name='<fn>', params=None, expr=None):
        from tuples import Tuple
        from vars import WordToken
        self.name = name
        self.function = self.invoke
        self.funcList = [self]
        if expr is not None:
            self.expression = (cpy := expr.morphCopy())
            cpy.brackets = ''
            cpy.tokens = cpy.tokens[3:]
            cpy.inputStr = cpy.inputStr[cpy.tokenPos[3][0]:]
            cpy.tokenPos = [(a - cpy.tokenPos[3][0], b - cpy.tokenPos[3][0]) for (a, b) in cpy.tokenPos[3:]]
        if params is None: raise ParseError("Function parameter should be exactly one LTuple")
        self.params = params
        self.wordDict = {}  # wordDict is rebuilt when main memory changes.
        self.wordDictVer = -1

    def value(self, *args, **kwargs):
        return self
    
    def __str__(self):
        if hasattr(self, 'params') and hasattr(self, 'expression'):
            return f"{self.name}{self.params} = {self.expression}"
        else:
            return self.name

    def invoke(self, argTuple, mem=None):
    # TODO: rewrite. Should perform the following:
    # - assign its input tuple to the paramsTuple (which writes to its memory)
    # - perform the evaluation

        if mem is None:  raise EvaluationError(f"No memory passed to function '{self.name}'")
        from tuples import Tuple
        from memory import Memory

        if len(argTuple) > len(self.params): raise EvaluationError(f"Function '{self.name}' expects {len(self.params)} parameters but received {len(argTuple)}")
        if isinstance(mem, Memory):
            if self.wordDictVer < mem._varsVersion:
                self.wordDict = mem.update
                self.wordDictVer = mem._varsVersion
                self.expression.parsed = self.expression.parsedPos = None
            thisInvocationDict = self.wordDict.copy()
        else:
            thisInvocationDict = mem.copy()
        # store inputs into own copy of wordDict
        self.params.assign(argTuple, thisInvocationDict)
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
