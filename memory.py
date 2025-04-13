from number import *
import op
from settings import Settings

st = Settings()


class Memory:

    # Functions override main calculator memory with their own variable memory.
    # Parser requires access to memory
    # Expressions requires access to memory

    baseList = {
        'e': e,
        'pi': pi,
        'i': imag_i,
        'P': op.permutation,   # These are here so that
        'C': op.combination,   # they are overrideable.
    }

    topList = {
        'abs': op.absolute,   # These override user vars
        'arg': op.argument,
        'conj': op.conjugate,
        'sin': op.sin,
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

    def __init__(self, filename=None):
        self._vars = {}
        self._varsVersion = 0
        self._fullVersion = 0
        self._full = Memory.combine()
        self.trie = None
        if filename is not None: self.load(filename)
        # for testing

    def get(self, str):
        return self.update[str] if str in self.update else None
    
    def add(self, str, val):
        if isinstance(val, Number): val = val.fastContinuedFraction(epsilon=st.epsilon)
        needSort = True if str not in self._vars else False
        self._vars[str] = val
        if self.trie is not None: self.trie.insert(str)
        if needSort:
            self._vars = {k: self._vars[k] for k in sorted(self._vars, key=lambda x: (-len(x), x))}
        self._varsVersion += 1

    def delete(self, string):
        strList = string.replace(',', ' ').split()
        deleted = []
        for s in strList:
            if s in self._vars:
                del self._vars[s]
                deleted.append(s)
                if s not in self.baseList:
                    self.trie.delete(s)
        if deleted: self._varsVersion += 1
        return deleted
    
    def save(self, filename):
        from functions import Function, FuncComposition
        with open(filename, "w") as f:
            for var in self.ownList:
                value = self.ownList[var]
                if isinstance(value, Number):
                    f.write(f"{var} = {str(value)}\n")
                elif isinstance(value, FuncComposition):
                    f.write(f"{var} = {value.name}\n")
                elif isinstance(value, Function):
                    f.write(f"{str(value)}\n")

    def load(self, filename):
        import parser
        with open(filename) as f:
            for line in f:
                parser.parse(line).value(mem=self)

    @staticmethod
    def combine(*dicts):  # combines Memory objects and/or dictionaries and produces a dict
        # print("Combining dicts...")
        combinedLst = [memOrDict.ownList if isinstance(memOrDict, Memory) else memOrDict for memOrDict in [Memory.baseList] + list(dicts) + [Memory.topList]]
        tmp = {k: d[k] for d in combinedLst for k in d}
        # Predefined constants (e.g. pi) may be overridden by user-defined variables.
        # Predefined operators (sin, cos, tan) override user-defined variables.
        tmp = {k: tmp[k] for k in sorted(tmp, key=lambda x: (-len(x), x))}
        return tmp

    @property
    def update(self):
        if self._fullVersion < self._varsVersion:
            # print(f"Memory: updating full list...")
            self._full = Memory.combine(self._vars)
            self._fullVersion = self._varsVersion
        return self._full

    @property
    def ownList(self): return self._vars