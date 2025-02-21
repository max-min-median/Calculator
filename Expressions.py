from Operators import *
import Op
from Vars import Value, Var, WordToken, LValue
from Errors import CalculatorError, ParseError
from Functions import Function


class Expression(Value):
    def __init__(self, input_string=None, brackets='', parent=None, parent_offset=0):
        self.input_string = input_string  # only the part of the string relevant to this Expression.
        self.tokens = []
        self.token_pos = []  # position of individual tokens within this Expression.
        self.parsed = None
        self.parsed_pos = None
        self.brackets = brackets  # 2-char string, '()', '[]', '{}' or an empty string.
        self.parent = parent  # parent_obj
        self.parent_offset = parent_offset  # position of this Expression relative to parent
        self.display_string = ''

    def pos_of_elem(self, i=None, tup=None):  # returns a tuple describing the position of the i-th element in the full string.
        tup_to_use = tup if tup is not None else self.parsed_pos[i] if self.parsed_pos is not None else self.token_pos[i]
        return tuple(self.offset + x for x in tup_to_use)

    @property
    def offset(self):
        return self.parent_offset + (0 if self.parent is None else self.parent.offset)

    @property
    def pos(self):
        return (self.offset, self.offset + len(self.input_string))

    def value(self, mem, epsilon, debug=False):
        dummy = Var('dummy')

        def evaluate(power=0, index=0, skip_eval=False):  # returns (Value, end_index)
            def try_operate(L, *args, **kwargs):
                try:
                    ret = skip_eval and dummy or token.function(L, *args, **kwargs)
                    debug and print(f"{str(token).strip(): ^3}:", ', '.join((str(L),) + tuple(str(a) for a in args)))
                    return ret
                except CalculatorError as e:
                    raise (type(e))(e.args[0], self.pos_of_elem(index))
                
            L = None
            while True:
                token = self.parsed[index]
                if isinstance(token, WordToken):
                    if self.parsed[index+1] == Op.assignment:
                        self.parsed[index] = token.to_LValue()
                    elif isinstance(self.parsed[index+1], Expression) and self.parsed[index+2] == Op.assignment:  # make a function
                        self.parsed[index] = token.to_LFunc()
                    else:
                        split_lst, var_lst = token.split_word_token(mem, self.parsed[index+1])
                        self.parsed[index:index+1] = var_lst
                        prev = 0
                        self.parsed_pos[index:index+1] = [(self.parsed_pos[index][0] + prev, self.parsed_pos[index][0] + (prev := prev + len(s))) for s in ([''] + split_lst)[:-1]]
                    continue
                match L, token:
                    case None, Value():
                        L = skip_eval and dummy or token.value(mem=mem, epsilon=epsilon)
                        index += 1
                        continue
                    case None, Postfix() | Infix():
                        raise ParseError(f"Unexpected operator '{token.name}'", self.pos_of_elem(index))
                    # non-Fn-Fn : Low
                    # non-Fn-Prefix : Low
                    # non-Fn-non-Fn : High
                    # Fn-Fn : High
                    case Function(), Expression():
                        token = Op.function_invocation
                    case Value(), Function() | Prefix() | Expression() if not isinstance(L, Function):  # Fn-Fn = High, nonFn-Fn = Low
                        token = Op.implicit_mult_prefix  # implicit mult of value to prefix, slightly lower precedence
                    case Value(), Value():
                        token = Op.implicit_mult
                match token:
                    case Operator() if token.power[0] <= power: return L, index - 1
                    case Prefix():
                        L, index = evaluate(power=token.power[1], index=index+1, skip_eval=skip_eval)
                        L = try_operate(L, mem=mem, epsilon=epsilon)
                    case Postfix():
                        L = try_operate(L, mem=mem, epsilon=epsilon)
                    case Infix():
                        old_index = index
                        exp, index = evaluate(power=token.power[1], index = index + 1 - (token in [Op.implicit_mult, Op.implicit_mult_prefix, Op.function_invocation]), skip_eval = skip_eval or token == Op.logical_and and L.sign == 0 or token == Op.logical_or and L.sign != 0)
                        if token == Op.assignment and not isinstance(L, LValue): raise ParseError("Invalid LValue for assignment operator '='", self.pos_of_elem(old_index))
                        elif token != Op.assignment and isinstance(exp, LValue): raise ParseError(f"Invalid operation on LValue", self.pos_of_elem(old_index))
                        else: L = try_operate(L, exp, mem=mem, epsilon=epsilon)
                    case None:
                        return L, index - 1
                index += 1

        match self.tokens[:3]:  # create new function
            case WordToken(), Expression(), Op.assignment:
                mem.add(self.tokens[0].name, fn := Function(name=self.tokens[0].name, params=self.tokens[1], expr=self))
                return fn
            
        self.parsed = self.parsed or (self.tokens + [None, None])
        self.parsed_pos = self.parsed_pos or (self.token_pos + [(9999, 9999), (9999, 9999)])
        return evaluate()[0]
            
    def __str__(self):
        from Numbers import Number
        if self.display_string == '':
            prev_token = None
            for token in self.tokens:
                if isinstance(prev_token, (Number, Var, Postfix)) and isinstance(token, (Var, Prefix)): self.display_string += '⋅' + str(token)
                else: self.display_string += str(token)
                prev_token = token
            self.display_string = self.brackets[:1] + self.display_string + self.brackets[1:]
        return self.display_string


class Tuple(Expression):

    def __init__(self, input_string=None, brackets='()', parent=None, parent_offset=0):
        super().__init__(input_string=input_string, brackets=brackets, parent=parent, parent_offset=parent_offset)

    @staticmethod
    def from_first(expr):
        tup = Tuple(input_string=expr.input_string, brackets=expr.brackets, parent=expr.parent, parent_offset=expr.parent_offset)
        tup.tokens = [expr]
        return tup

    def __str__(self):
        if self.display_string == '':
            self.display_string = self.brackets[:1] + ', '.join([x.disp() for x in self.tokens]) + self.brackets[1:]
        return self.display_string

    def value(self, mem=None, epsilon=None, debug=False):
        tup = Tuple(input_string=self.input_string, brackets=self.brackets, parent=self.parent, parent_offset=self.parent_offset)
        tup.token_pos = self.token_pos
        tup.tokens = [expr.value(mem=mem, epsilon=epsilon, debug=debug) for expr in self.tokens]
        return tup