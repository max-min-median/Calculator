from number import *
from functions import Function, FuncComposition
import op
from settings import Settings

st = Settings()


class Memory:

    # Base class intended for use by Functions.

    globalMem = None

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
        'Im': op.imPart,
        'Re': op.realPart,
        'sgn': op.signum,
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
        self.vars = {}

    def get(self, str):
        seq = [Memory.topList, self.vars if self is not Memory.globalMem else {}, Memory.globalMem.vars, Memory.baseList]
        for dct in seq:
            if str in dct: return dct[str]

    def add(self, str, val):
        if isinstance(val, Number): val = val.fastContinuedFraction(epsilon=st.epsilon)
        self.vars[str] = val

    def delete(self, key):  # Functions should never have stuff in their memory deleted
        raise NotImplementedError
    
    def copy(self):
        cpy = Memory()
        cpy.__dict__.update(self.__dict__)
        cpy.vars = self.vars.copy()
        return cpy
    
    def __iter__(self): yield from self.vars

    # def __getitem__(self, key): return self.get(key)
    # def __setitem__(self, key, value): self.add(key, value)
    # def __delitem__(self, key): self.delete(key)
    
    # @staticmethod
    # def combine(*dicts):  # combines Memory objects and/or dictionaries and produces a dict
    #     # print("Combining dicts...")
    #     combinedLst = [memOrDict.ownList if isinstance(memOrDict, Memory) else memOrDict for memOrDict in [Memory.baseList] + list(dicts) + [Memory.topList]]
    #     tmp = {k: d[k] for d in combinedLst for k in d}
    #     # Predefined constants (e.g. pi) may be overridden by user-defined variables.
    #     # Predefined operators (sin, cos, tan) override user-defined variables.
    #     tmp = {k: tmp[k] for k in sorted(tmp, key=lambda x: (-len(x), x))}
    #     return tmp

    # @property
    # def update(self):
    #     if self._fullVersion < self.varsVersion:
    #         # print(f"Memory: updating full list...")
    #         self._full = Memory.combine(self.vars)
    #         self._fullVersion = self.varsVersion
    #     return self._full

    # @property
    # def ownList(self): return self.vars

class GlobalMemory(Memory):

    def __init__(self, filename=None):
        self.vars = {}
        self.trie = None
        self.changed = False
        if filename is not None: self.load(filename)

    def add(self, str, val):
        if str == 'ans':
            # if 'ans' in self.vars: self.vars.pop('ans')
            self.vars['ans'] = val
        else:
            if isinstance(val, Number): val = val.fastContinuedFraction(epsilon=st.epsilon)
            needSort = str not in self.vars
            self.vars[str] = val
            if self.trie is not None: self.trie.insert(str)
            if needSort:
                self.vars = {k: self.vars[k] for k in sorted(self.vars, key=lambda x: -isinstance(self.vars[x], Function))}
        self.changed = True

    def delete(self, string):
        strList = string.replace(',', ' ').split()
        deleted = []
        for s in strList:
            if s in self.vars:
                del self.vars[s]
                deleted.append(s)
                if s not in self.baseList:
                    self.trie.delete(s)
        if deleted: self.changed = True
        return deleted

    def copy(self):
        return Memory()  # global returns a blank Memory object when copy is called

    def save(self, filename):
        if filename is None:  # not global memory
            raise MemoryError("Cannot save/load function memory")
        if not self.changed: return
        with open(filename, "w") as f:
            for var, value in self.vars.items():
                if isinstance(value, Number):
                    f.write(f"{var} = {value.fromString if hasattr(value, 'fromString') else str(value)}\n")
                elif isinstance(value, FuncComposition):
                    f.write(f"{var} = {value.name}\n")
                elif isinstance(value, Function):
                    if var != value.name: f.write(f"{var} = ")
                    f.write(f"{str(value)}\n")
        self.changed = False

    def load(self, filename):
        if filename is None:  # not global memory
            raise MemoryError("Cannot save/load function memory")
        import parser
        with open(filename) as f:
            for line in f:
                parser.parse(line).value(mem=self)
        self.changed = False