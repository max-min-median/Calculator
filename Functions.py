from Vars import Value
from Errors import ParseError, EvaluationError

# Functions must be followed by bracketed expressions, unlike Unary_Left_Operators.
# Trig fns and sqrt are therefore treated as Unary_Left_Operators.

# ffg(7), f(g(3, 4)), (fg^2)(x), (f(fg)^2)(7)

class Function(Value):
    def __init__(self, name='<fn>', params=None, expr=None):
        from Expressions import Tuple
        from Vars import WordToken
        self.name = name
        self.function = self.invoke
        self.func_list = [self]
        if expr is not None:
            self.expression = expr
            expr.tokens = expr.tokens[3:]
            expr.input_string = expr.input_string[expr.token_pos[3][0]:]
            expr.token_pos = [(a - expr.token_pos[3][0], b - expr.token_pos[3][0]) for (a, b) in expr.token_pos[3:]]
        self.params = {}
        self.word_dict = {}  # word_dict is rebuilt when main memory changes.
        self.word_dict_ver = -1
        if params is not None:
            param_tmp_lst = params.tokens if isinstance(params, Tuple) else [params]  # for functions with 1 param, wrap the Expression in a list
            for i, x in enumerate(param_tmp_lst):
                if len(x.tokens) != 1 or not isinstance(x.tokens[0], WordToken): raise ParseError('Each parameter should be exactly one WordToken', params.pos_of_elem(i))
                self.params[x.tokens[0].name] = None

    def value(self, *args, **kwargs):
        return self
    
    def __str__(self):
        if hasattr(self, 'params') and hasattr(self, 'expression'):
            return f"{self.name}({', '.join(list(self.params))}) = {self.expression}"
        else:
            return self.name

    def invoke(self, tup_or_expr, mem=None, debug=False):
        if mem is None:  raise EvaluationError(f"No memory passed to function '{self.name}'")
        from Expressions import Tuple
        from Memory import Memory
        func_inputs = [] if tup_or_expr is None else \
                      [tup_or_expr] if not isinstance(tup_or_expr, Tuple) else \
                      tup_or_expr.tokens  # to make func_inputs a list of Expressions.
        if len(func_inputs) != len(self.params): raise EvaluationError(f"Function '{self.name}' expects {len(self.params)} parameters but received {len(func_inputs)}")
        if isinstance(mem, Memory):
            if self.word_dict_ver < mem._vars_version:
                self.word_dict = Memory.combine(mem, self.params)
                self.word_dict_ver = mem._vars_version
                self.expression.parsed = self.expression.parsed_pos = None
            this_invocation_dict = self.word_dict.copy()
        else:
            this_invocation_dict = mem.copy()
        # store inputs into own copy of word_dict
        for k, v in list(zip(self.params, func_inputs)): this_invocation_dict[k] = v
        # evaluate the expression
        return self.expression.value(mem=this_invocation_dict, debug=debug)

    def __mul__(self, other):
        if not isinstance(other, Function): raise EvaluationError('Incorrect type for function composition')
        return FuncComposition(*self.func_list, *other.func_list)

    def __pow__(self, other):
        other = int(other)
        if not other > 0: raise EvaluationError('Functional power must be a positive integer')
        return FuncComposition(*(self.func_list * int(other)))

class FuncComposition(Function):
    def __init__(self, *func_list):
        self.name = ''.join([fn.name for fn in func_list])
        self.func_list = list(func_list)
        self.function = self.invoke
    
    def invoke(self, tup_or_expr, mem=None, debug=False):
        res = tup_or_expr
        for fn in self.func_list[::-1]:
            res = fn.invoke(res, mem=mem, debug=debug)
        return res
