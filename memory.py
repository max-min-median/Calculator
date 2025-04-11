from number import *
import op
from settings import Settings

class Memory:

    # Functions override main calculator memory with their own variable memory.
    # Parser requires access to memory
    # Expressions requires access to memory

    base_list = {'e': e,
                 'pi': pi,
                 'i': imag_i,
                 'P': op.permutation,   # These are here so that
                 'C': op.combination,   # they are overrideable.
    }

    top_list = {'sin': op.sin,   # These override user vars
                'cosec': op.csc,
                'csc': op.csc,
                'cos': op.cos,
                'sec': op.sec,
                'tan': op.tan,
                'cot': op.cot,
                'sinh': op.sinh,
                'cosh': op.cosh,
                'tanh': op.tanh,
                'asin': op.arcsin,
                'arcsin': op.arcsin,
                'acos': op.arccos,
                'arccos': op.arccos,
                'atan': op.arctan,
                'arctan': op.arctan,
                'sqrt': op.sqrt,
                'ln': op.ln,
                'lg': op.lg,
    }

    def __init__(self, settings, filename=None):
        self._vars = {}
        self._vars_version = 0
        self._full_version = 0
        self._full = Memory.combine()
        self.trie = None
        if filename is not None: self.load(filename, settings)
        # for testing

    def get(self, str):
        return self.update[str] if str in self.update else None
    
    def add(self, str, val):
        need_sort = True if str not in self._vars else False
        self._vars[str] = val
        if self.trie is not None: self.trie.insert(str)
        if need_sort:
            self._vars = {k: self._vars[k] for k in sorted(self._vars, key=lambda x: (-len(x), x))}
        self._vars_version += 1

    def delete(self, string):
        str_list = string.replace(',', ' ').split()
        deleted = []
        for s in str_list:
            if s in self._vars:
                del self._vars[s]
                deleted.append(s)
                if s not in self.base_list:
                    self.trie.delete(s)
        if deleted: self._vars_version += 1
        return deleted
    
    def save(self, filename):
        from functions import Function, FuncComposition
        with open(filename, "w") as f:
            for var in self.own_list:
                value = self.own_list[var]
                if isinstance(value, RealNumber):
                    f.write(f"{var} = {str(value)}\n")
                elif isinstance(value, FuncComposition):
                    f.write(f"{var} = {value.name}\n")
                elif isinstance(value, Function):
                    f.write(f"{str(value)}\n")

    def load(self, settings, filename):
        import parser
        working_epsilon = RealNumber(1, 10 ** settings.get('working_precision'), fcf=False)
        with open(filename) as f:
            for line in f:
                parser.parse(line).value(mem=self, epsilon=working_epsilon, debug=False)

    @staticmethod
    def combine(*dicts):  # combines Memory objects and/or dictionaries and produces a dict
        # print("Combining dicts...")
        combined_lst = [mem_or_dict.own_list if isinstance(mem_or_dict, Memory) else mem_or_dict for mem_or_dict in [Memory.base_list] + list(dicts) + [Memory.top_list]]
        tmp = {k: d[k] for d in combined_lst for k in d}
        # Predefined constants (e.g. pi) may be overridden by user-defined variables.
        # Predefined operators (sin, cos, tan) override user-defined variables.
        tmp = {k: tmp[k] for k in sorted(tmp, key=lambda x: (-len(x), x))}
        return tmp

    @property
    def update(self):
        if self._full_version < self._vars_version:
            # print(f"Memory: updating full list...")
            self._full = Memory.combine(self._vars)
            self._full_version = self._vars_version
        return self._full

    @property
    def own_list(self): return self._vars