from Numbers import Number
import Op
from Settings import Settings

class Memory:

    # Functions override main calculator memory with their own variable memory.
    # Parser requires access to memory
    # Expressions requires access to memory

    base_list = {'e': Number('2.718281828459045235360287471353'),
                 'pi': Number('3.1415926535897932384626433832795'),
                 'P': Op.permutation,   # These are here so that
                 'C': Op.combination,   # they are overrideable.
    }

    top_list = {'sin': Op.sin,   # These override user vars
                'cos': Op.cos,
                'tan': Op.tan,
                'sqrt': Op.sqrt,
                'ln': Op.ln,
    }

    def __init__(self, settings, filename=None):
        self._vars = {}
        self._vars_version = 0
        self._full_version = 0
        self._full = Memory.combine()
        if filename is not None: self.load(filename, settings)
        # for testing

    def get(self, str):
        return self.update[str] if str in self.update else None
    
    def add(self, str, val):
        need_sort = True if str not in self._vars else False
        self._vars[str] = val
        if need_sort:
            self._vars = {k: self._vars[k] for k in sorted(self._vars, key=lambda x: (-len(x), x))}
        self._vars_version += 1

    def delete(self, string):
        str_list = string.replace(',', ' ').split()
        deleted = []
        for str in str_list:
            if str in self._vars: del self._vars[str]; deleted.append(str)
        if deleted: self._vars_version += 1
        return ', '.join(deleted)
    
    def save(self, filename):
        from Functions import Function, FuncComposition
        with open(filename, "w") as f:
            for var in self.own_list:
                value = self.own_list[var]
                if isinstance(value, Number):
                    f.write(f"{var} = {str(value)}\n")
                elif isinstance(value, FuncComposition):
                    f.write(f"{var} = {value.name}\n")
                elif isinstance(value, Function):
                    f.write(f"{str(value)}\n")

    def load(self, settings, filename):
        import Parser
        working_epsilon = Number(1, 10 ** settings.get('working_precision'), fcf=False)
        with open(filename) as f:
            for line in f:
                Parser.parse(line).value(mem=self, epsilon=working_epsilon, debug=False)

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

pass