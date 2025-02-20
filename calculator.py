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
    print("Calculator v1.2.0-beta by max_min_median")
    print("(type 'help' for a quick tutorial)\n")
    main_mem = Memory()
    main_mem.load('calc.mem')
    final_epsilon = Number(1, 10 ** 25, fcf=False)
    current_ver = main_mem._vars_version
    import re
    while True:
        try:
            inp = input(prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙
            # check for commands
            if m := re.match(r'\s*help\s*', inp):
                import Help
                Help.display()
            elif m := re.match(r'\s*vars\s*', inp):
                print("User-defined Variables")
                print("──────────────────────")
                for k in main_mem._vars:
                    print(f'{k} = {main_mem._vars[k].value()}', end='\n\n')
            elif m := re.match(r'\s*del\s(.*)$', inp):
                print("Deleted: " + main_mem.delete(m.group(1)), end='\n\n')
            elif m := re.match(r'\s*frac\s(\d+)$', inp):
                main_mem.set_setting("frac_max_length", int(m.group(1)))
                print(f"frac_max_length -> {main_mem.get_setting('frac_max_length')}\n")
            elif m := re.match(r'\s*debug(?:\s+(\w+))?$', inp):
                flag = {'on':True, 'off':False}.get(m.group(1) if m.group(1) is None else m.group(1).lower())
                if flag is None: raise CalculatorError('Syntax for debug mode: debug [on | off]')
                main_mem.set_setting("debug", flag)
                print(f"debug -> {main_mem.get_setting('debug')}\n")
            elif inp.strip() == '':
                continue
            else:
                expr = parse(inp, debug=False)
                # if expr is not None: print((val := expr.value(main_mem, debug=False)), '= ' + val.dec() if isinstance(val, Number) and val.denominator != 1 else '', end="\n\n")
                if expr is not None: print(expr.value(main_mem, debug=main_mem.get_setting('debug')).disp(main_mem.frac_max_length), end="\n\n")
            if main_mem._vars_version != current_ver:
                main_mem.save("./calc.mem")
                current_ver = main_mem._vars_version
        except CalculatorError as e:
            if len(e.args) > 1: print(' ' * (len(prompt) + (span := e.args[1])[0] - 1) + '↗' + '‾' * (span[1] - span[0]))
            print(f'{repr(e).split("(")[0]}:', e.args[0], end='\n\n')
            # raise e
        except ZeroDivisionError:
            print(f'Division by zero\n')
        except RecursionError:
            print(f'RecursionError: Check for infinite recursion in functions.\n')
        except (EOFError, KeyboardInterrupt):
            break

if __name__ == '__main__':
    sys.setrecursionlimit(500000)
    main()
    sys.exit()