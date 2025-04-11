class CalculatorError(Exception):
    def __init__(self, err_msg='Calculator Error!', *args):
        super().__init__(err_msg, *args)
        # self.message = err_msg

class VariableError(CalculatorError):
    def __init__(self, err_msg='Variable error!', *args):
        super().__init__(err_msg, *args)

class EvaluationError(CalculatorError):
    def __init__(self, err_msg='Evaluation error!', *args):
        super().__init__(err_msg, *args)

class NumberError(CalculatorError):
    def __init__(self, err_msg='Number error!', *args):
        super().__init__(err_msg, *args)

class ParseError(CalculatorError):
    def __init__(self, err_msg='Parse error!', *args):
        super().__init__(err_msg, *args)

class SettingsError(CalculatorError):
    def __init__(self, err_msg='Settings error!', *args):
        super().__init__(err_msg, *args)

pass