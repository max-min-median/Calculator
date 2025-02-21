class Value:    
    def __init__(self, name='<Value>', value=None):
        self.name = name
        self._value = value

    def __str__(self):
        return self.name

    def disp(self, *args, **kwargs):
        return str(self)

    def value(self, *args, **kwargs):
        raise NotImplementedError(f'subclass {type(self)} has no implementation of value()')

class Var(Value):
    def __init__(self, name):
        super().__init__(name=name)

    def value(self, *args, mem=None, **kwargs):
        from Errors import EvaluationError
        if mem is None: raise EvaluationError(f"No memory provided to Var object '{self.name}'")
        val = mem.get(self.name)
        if val is None: raise EvaluationError(f"Variable '{self.name}' not found in memory!")
        return val
    
class LValue(Value):  # variable ready for assignment. Has NO value
    def __init__(self, name='<l_value>', value=None):
        super().__init__(name=name, value=value)

    def value(self, *args, **kwargs):
        # return self._value if self._value is not None else self.name
        return self

    def make_var(self, value=None):
        if value is None: raise ValueError(f'No value to assign to "{self.name}"')
        return Var(name=self.name, value=value)

class WordToken:
    def __init__(self, name='<word_token>'):
        self.name = name

    def __str__(self):
        return str(self.name)
    
    def split_word_token(self, mem, next_token):
        from Operators import Prefix
        from Numbers import Number
        from Functions import Function
        from Errors import ParseError
        # returns a list of possible splits of the string.
        # 'greediest' (longer tokens are prioritized) splits come first.
        def try_split(s, num_allowed=False, only_funcs_allowed=False):
            if s == '': return [[]], [[]]
            lst, var_lst = [], []
            for i in reversed(range(len(s))):
                if (this_word := s[:i+1]) in word_dict:
                    if isinstance(word_dict[this_word], Number): this_word = Var(this_word)
                    else: this_word = word_dict[this_word]
                    if only_funcs_allowed and type(this_word) != Function: continue
                    if i == len(s) - 1 and type(this_word) == Prefix and not isinstance(next_token, Value): continue  # allow stuff like 'ksin3.0pi'
                elif num_allowed and not only_funcs_allowed and s[:i+1].isdigit() and not s[i+1:i+2].isdigit():
                    this_word = Number(s[:i+1])
                else:
                    continue
                split_rest, split_rest_vars = try_split(s[i+1:], num_allowed=(type(this_word) == Prefix), only_funcs_allowed=(type(this_word) == Function))
                lst += [[s[:i+1]] + spl for spl in split_rest]
                var_lst += [[this_word] + spl for spl in split_rest_vars]
            return lst, var_lst
        
        word_dict = mem if isinstance(mem, dict) else mem.update
        split_lst, var_lst = try_split(self.name)

        if len(split_lst) == 0: raise ParseError(f"Unable to parse '{self.name}'")
        tmp = ['∙'.join(s) for s in split_lst]
        if len(split_lst) > 1:
            print(f"Warning: Found multiple ways to parse '{self.name}': " + ", ".join(tmp) + f". (selecting '{tmp[0]}')")
        return split_lst[0], var_lst[0]

    def to_LValue(self):
        return LValue(name=self.name)

    def to_LFunc(self):
        from Functions import LFunc
        return LFunc(name=self.name)
    
    @property
    def memory(self):
        from Memory import Memory
        if self.func_mem is not None: word_dict = Memory.combine(self.user_mem, self.func_mem)
        else: word_dict = self.user_mem.full
        return word_dict

    pass

