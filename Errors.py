class CalculatorError(Exception):
    def __init__(self, err_msg = 'Calculator Error!'):
        super().__init__(err_msg)
        # self.message = err_msg

class BracketMismatchError(CalculatorError):
    def __init__(self, err_msg = 'Bracket mismatch!'):
        super().__init__(err_msg)

class VariableError(CalculatorError):
    def __init__(self, err_msg = 'Variable error!'):
        super().__init__(err_msg)

class NumberError(CalculatorError):
    def __init__(self, err_msg = 'Number error!'):
        super().__init__(err_msg)

class ParseError(CalculatorError):
    def __init__(self, err_msg = 'Parse error!'):
        super().__init__(err_msg)
