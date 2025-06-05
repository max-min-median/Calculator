from vars import Value, LValue
from errors import ParseError, EvaluationError

# Functions must be followed by bracketed expressions, unlike Unary_Left_Operators.
# Trig fns and sqrt are therefore treated as Unary_Left_Operators.
# ffg(7), f(g(3, 4)), (fg^2)(x), (f(fg)^2)(7)

# LAMBDAS
# sum = x => y => z => x + y + z
# sum(3): 'y => {x = 3}; z => x + y + z'
# sum(3, 5): 'z => {x = 3; y = 5}; x + y + z'

class Function(Value):

    def __init__(self, name='<fn>', params=None, expr=None, closure=None):
        self.name = name
        self.function = self.invoke
        self.funcList = [self]
        self.expression = expr
        if closure is None: raise MemoryError("Function must be created with a closure. Pass the global memory mainMem if it is defined in global scope.")
        self.closure = closure
        if params is None: raise ParseError("Function parameter should be exactly one LTuple")
        self.params = params

    def value(self, *args, **kwargs):
        return self
    
    def __str__(self):
        if hasattr(self, 'params') and hasattr(self, 'expression'):
            return f"{self.name}{self.params} = {self.expression}"
        else:
            return self.name

    def invoke(self, argTuple):
    # TODO: rewrite. Should perform the following:
    # - assign its input tuple to the paramsTuple (which writes to its memory)
    # - perform the evaluation

        if len(argTuple) > len(self.params): raise EvaluationError(f"Function '{self.name}' expects {len(self.params)} parameters but received {len(argTuple)}")
        self.expression.parsed = self.expression.parsedPos = None
        closure = mem.copy()
        self.params.assign(argTuple, closure)
        # evaluate the expression
        return self.expression.value(mem=closure)

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

class LFunc(Function, LValue):
    def __init__(self, wordtoken, params):
        self.name = wordtoken.name
        self.params = params
    
    def __str__(self):
        return f"{self.name}{self.params}"
