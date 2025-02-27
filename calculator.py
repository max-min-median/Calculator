from Vars import *
from Memory import Memory
from Errors import *
from Parser import parse
from Numbers import Number
from Settings import Settings
from pathlib import Path
import sys, re

# class Calculator:
#     def __init__(self):
#         self.mem = Memory()

def main():
    print("Calculator v1.4.0-beta by max_min_median")
    print("(type 'help' for a quick tutorial)\n")
    basedir = Path(__file__).resolve().parent
    settings = Settings(basedir/'calc_settings.txt')
    main_mem = Memory(basedir/'calc_mem.txt', settings)
    working_epsilon = Number(1, 10 ** settings.get('working_precision'), fcf=False)
    final_epsilon = Number(1, 10 ** settings.get('final_precision'), fcf=False)
    current_ver = main_mem._vars_version

    while True:
        try:
            inp = input(prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙
            # check for commands
            if m := re.match(r'\s*help\s*', inp):
                import Help
                Help.display()
            elif m := re.match(r'\s*vars\s*', inp):
                print("\nUser-defined Variables")
                print("──────────────────────")
                for k in main_mem._vars:
                    print(f'{k} = {main_mem._vars[k].value()}')
                print()
            elif m := re.match(r'\s*del\s(.*)$', inp):
                print("Deleted: " + main_mem.delete(m.group(1)), end='\n\n')
            elif m := re.match(r'\s*frac\s(\d+)$', inp):
                settings.set("frac_max_length", int(m.group(1)))
                print(f"frac_max_length -> {settings.get('frac_max_length')}\n")
            elif m := re.match(r'\s*prec(?:ision)?\s(\d+)$', inp):
                settings.set("working_precision", int(m.group(1)))
                working_epsilon = Number(1, 10 ** settings.get('working_precision'), fcf=False)
                print(f"working_precision -> {settings.get('working_precision')}\n")
            elif m := re.match(r'\s*disp\s(\d+)$', inp):
                settings.set("final_precision", int(m.group(1)))
                final_epsilon = Number(1, 10 ** settings.get('final_precision'), fcf=False)
                print(f"final_precision -> {settings.get('final_precision')}\n")
            elif m := re.match(r'\s*debug(?:\s+(\w+))?$', inp):
                flag = {'on':True, 'off':False}.get(m.group(1) if m.group(1) is None else m.group(1).lower())
                if flag is None: raise CalculatorError('Syntax for debug mode: debug [on | off]')
                settings.set("debug", flag)
                print(f"debug -> {settings.get('debug')}\n")
            elif inp.strip() == '':
                continue
            elif m := re.match(r'(?:=|sto(?:re)? |->)\s*([A-Za-z]\w*)', inp):
                main_mem.add(m.group(1), main_mem.get('ans'))
                print(f'{m.group(1)} = {main_mem.get(m.group(1)).value()}\n')
            else:
                expr = parse(inp, debug=False)
                if expr is None: continue
                val = expr.value(main_mem, working_epsilon, debug=settings.get('debug'))
                if isinstance(val, Number): val = val.fast_continued_fraction(epsilon=final_epsilon)
                main_mem.add('ans', val)
                print(val.disp(settings.get('frac_max_length'), settings.get('final_precision')), end="\n\n")
            if main_mem._vars_version != current_ver:
                main_mem.save("calc_mem.txt")
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