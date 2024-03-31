from Errors import *
import math
        
class Var:
    def __init__(self, name = '<var>', function = None, value = None):
        if function != None and value != None: raise VariableError('Variable cannot have both a function and value')
        self.name = name
        self.fn = function
        self.value = value
    def __str__(self):
        return str(self.name)

# Functions must be followed by bracketed expressions, unlike Unary_Left_Operators. Trig fns and sqrt are therefore treated as Unary_Left_Operators.
class Function(Var):
    def __init__(self, name = '<fn>', function = lambda x: x):
        super().__init__(name, function, None)

class Constant(Var):
    def __init__(self, name = '<const>', value = None):
        super().__init__(name, None, value)

EULER = Constant('e', 2.718)
PI = Constant('pi', 3.142)

var_regexes = {r'e\b': EULER,
               r'pi\b': PI,
}
