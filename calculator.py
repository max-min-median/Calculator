from Vars import *
from Memory import Memory
from Errors import *
from Parser import parse
from Numbers import Number
import sys


class Calculator:
    def __init__(self):
        self.mem = Memory()


def main():
    print("Calculator v0.9.0a by max_min_median")
    print("(type 'help' for a quick tutorial)")
    main_mem = Memory()
    main_mem.load('calc.mem')
    current_ver = main_mem._vars_version
    import re
    while True:
        try:
            inp = input(prompt := "∙❯ ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙
            # check for commands
            if m := re.match(r'\s*help\s*', inp):
                import Help
                Help.display()
            elif m := re.match(r'\s*vars\s*', inp):
                print("User-defined Variables")
                print("──────────────────────")
                for k in main_mem._vars:
                    print(f'{k} = {main_mem._vars[k].value()}')
                print()
            elif m := re.match(r'\s*del\s(.*)$', inp):
                print("Deleted: " + main_mem.delete(m.group(1)))
            else:
                expr = parse(inp, debug=False)
                if expr is not None: print((val := expr.value(main_mem, debug=False)), '= ' + val.dec() if isinstance(val, Number) and val.denominator != 1 else '', end="\n\n")
            
            if main_mem._vars_version != current_ver:
                main_mem.save("./calc.mem")
                current_ver = main_mem._vars_version
        except CalculatorError as e:
            if len(e.args) > 1: print(' ' * (len(prompt) + (span := e.args[1])[0] - 1) + '↗' + '‾' * (span[1] - span[0]))
            print(f'{repr(e).split("(")[0]}:', e.args[0])
            # raise e
        except RecursionError:
            print(f'RecursionError: Check for infinite recursion in functions.')
        except (EOFError, KeyboardInterrupt):
            break

if __name__ == '__main__':
    sys.setrecursionlimit(100000)
    main()
    sys.exit()