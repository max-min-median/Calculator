from Vars import *
from Memory import Memory
from Errors import *
from Parser import parse
from Numbers import Number
from Settings import Settings
from pathlib import Path
import sys, re
from UI import *

# class Calculator:
#     def __init__(self):
#         self.mem = Memory()

def main():

    # ui.useWin("status").addstr("Calculator v1.4.1-beta by max_min_median\n")
    # ui.addstr("(type 'help' for a quick tutorial)\n").refresh()
    basedir = Path(__file__).resolve().parent
    settings = Settings(basedir/'calc_settings.txt')
    main_mem = Memory(basedir/'calc_mem.txt', settings)
    main_mem.trie = trie = Trie.fromCollection(main_mem.update)
    ui = UI(main_mem)
    working_epsilon = Number(1, 10 ** settings.get('working_precision'), fcf=False)
    final_epsilon = Number(1, 10 ** settings.get('final_precision'), fcf=False)
    current_ver = main_mem._vars_version

    while True:
        try:
            inp = ui.getInput(trie=trie) # (prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙
            ui.useWin("display")
            # check for commands
            if m := re.match(r'^\s*help\s*$', inp):
                import Help
                Help.display()
            elif m := re.match(r'^\s*vars\s*$', inp):
                if len(ui.text["display"]) > 0: ui.addText()
                ui.addText(("User-defined Variables", UI.LIGHTBLUE_ON_BLACK))
                ui.addText(("──────────────────────", ))
                for k in main_mem._vars:
                    ui.addText((k, UI.LIGHTBLUE_ON_BLACK), (' = ', ), (f"{main_mem._vars[k].value()}", UI.LIGHTBLUE_ON_BLACK)).redraw()
            elif m := re.match(r'\s*del\s(.*)$', inp):
                deleted = main_mem.delete(m.group(1))
                if not deleted:
                    ui.addText(('Variables not found', )).redraw()
                else:
                    ui.addText(("Deleted: ", ))
                    for var in deleted:
                        ui.addText((var, UI.LIGHTBLUE_ON_BLACK), (', ', ), startNewLine=False)
                    ui.text["display"][-1].pop()
                    ui.redraw()
            elif m := re.match(r'\s*frac(?:\s+(\d+))?$', inp):
                if m.group(1) is not None: settings.set("frac_max_length", int(m.group(1)))
                ui.addText(("frac_max_length", UI.LIGHTBLUE_ON_BLACK), (' -> ', ), (f"{settings.get('frac_max_length')}", UI.LIGHTBLUE_ON_BLACK)).redraw()
            elif m := re.match(r'\s*prec(?:ision)?(?:\s+(\d+))?$', inp):
                if m.group(1) is not None: settings.set("working_precision", int(m.group(1)))
                working_epsilon = Number(1, 10 ** settings.get('working_precision'), fcf=False)
                ui.addText(("working_precision", UI.LIGHTBLUE_ON_BLACK), (' -> ', ), (f"{settings.get('working_precision')}", UI.LIGHTBLUE_ON_BLACK)).redraw()
            elif m := re.match(r'\s*disp(?:lay)?(?:\s+(\d+))?$', inp):
                if m.group(1) is not None: settings.set("final_precision", int(m.group(1)))
                final_epsilon = Number(1, 10 ** settings.get('final_precision'), fcf=False)
                ui.addText(("final_precision", UI.LIGHTBLUE_ON_BLACK), (' -> ', ), (f"{settings.get('final_precision')}", UI.LIGHTBLUE_ON_BLACK)).redraw()
            elif m := re.match(r'\s*debug(?:\s+(\w+))?$', inp):
                flag = {'on':True, 'off':False}.get(m.group(1) if m.group(1) is None else m.group(1).lower(), None)
                if flag is not None: settings.set("debug", flag)
                else: ui.addText(("Usage: ", ), ("debug [on/off]", UI.LIGHTBLUE_ON_BLACK))
                ui.addText(("debug", UI.LIGHTBLUE_ON_BLACK), (" -> ", ), (f"{settings.get('debug')}", UI.LIGHTBLUE_ON_BLACK)).redraw()
            elif inp.strip() == '':
                continue
            elif m := re.match(r'(?:=|sto(?:re)? |->)\s*([A-Za-z]\w*)', inp):
                if (ans := main_mem.get('ans')) is None:
                    ui.addText(("Variable '", ), ("ans", UI.LIGHTBLUE_ON_BLACK), ("' does not exist or has been deleted", )).redraw()
                else:
                    main_mem.add(m.group(1), ans)
                    ui.trie.insert(m.group(1))
                    ui.addText((f'{m.group(1)}', UI.LIGHTBLUE_ON_BLACK), (' = ', ), (f'{main_mem.get(m.group(1)).value()}', UI.LIGHTBLUE_ON_BLACK)).redraw()
            else:
                expr = parse(inp, debug=False)
                if expr is None: continue
                val = expr.value(main_mem, working_epsilon, debug=settings.get('debug'))
                if isinstance(val, Number): val = val.fast_continued_fraction(epsilon=final_epsilon)
                main_mem.add('ans', val)
                ui.addText((val.disp(settings.get('frac_max_length'), settings.get('final_precision')), UI.BRIGHT_GREEN_ON_BLACK)).redraw()
            if main_mem._vars_version != current_ver:
                main_mem.save(basedir/'calc_mem.txt')
                current_ver = main_mem._vars_version
        except CalculatorError as e:
            if len(e.args) > 1: ui.addText((' ' * (len(ui.prompt) + (span := e.args[1])[0] - 1) + '↗' + '‾' * (span[1] - span[0]), UI.BRIGHT_RED_ON_BLACK))
            ui.addText((f"{repr(e).split('(')[0]}: {e.args[0]}", UI.BRIGHT_RED_ON_BLACK))
            ui.redraw()
            # raise e
        except ZeroDivisionError:
            ui.addText(("Division by zero", UI.BRIGHT_RED_ON_BLACK))
            ui.redraw()
        except RecursionError:
            ui.addText(("RecursionError: Check for infinite recursion in functions.", UI.BRIGHT_RED_ON_BLACK))
            ui.redraw()
        except (EOFError, KeyboardInterrupt):
            break
    ui.end()

if __name__ == '__main__':
    sys.setrecursionlimit(500000)
    main()