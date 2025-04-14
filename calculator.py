from settings import Settings
from vars import *
from memory import Memory
from errors import *
from parser import parse
from number import *
from pathlib import Path
import sys, re
from UI import *

# class Calculator:
#     def __init__(self):
#         self.mem = Memory()

# TODO:
# - allow functions to have 0 params
# - scrollable display window

def main():

    basedir = Path(__file__).resolve().parent
    memPath = basedir/'mem.txt'
    settingsPath = basedir/'settings.txt'
    st = Settings(settingsPath)
    mainMem = Memory(memPath)
    mainMem.trie = trie = Trie.fromCollection(mainMem.update)
    ui = UI(mainMem)
    currVersion = mainMem._varsVersion

    while True:
        try:
            inp = ui.getInput(trie=trie) # (prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙
            # check for commands
            if m := re.match(r'^\s*help\s*$', inp):
                import help
                help.display()
            elif m := re.match(r'^\s*vars\s*$', inp):
                if len(ui.text["display"]) > 0: ui.addText("display")
                ui.addText("display", ("User-defined Variables", UI.LIGHTBLUE_ON_BLACK))
                ui.addText("display", ("──────────────────────", ))
                for k in mainMem._vars:
                    ui.addText("display", (k, UI.LIGHTBLUE_ON_BLACK), (' = ', ), (f"{mainMem._vars[k].value()}", UI.LIGHTBLUE_ON_BLACK))
            elif m := re.match(r'\s*del\s(.*)$', inp):
                deleted = mainMem.delete(m.group(1))
                if not deleted:
                    ui.addText("display", ('Variable(s) not found!', UI.LIGHTBLUE_ON_BLACK))
                else:
                    ui.addText("display", ("Deleted: ", ))
                    for var in deleted:
                        ui.addText("display", (var, UI.LIGHTBLUE_ON_BLACK), (', ', ), startNewLine=False)
                    ui.text["display"][-1].pop()
            elif m := re.match(r'\s*frac(?:\s+(\d+))?$', inp):
                if m.group(1) is not None: st.set("frac_max_length", int(m.group(1)))
                ui.addText("display", ("frac_max_length", UI.LIGHTBLUE_ON_BLACK), (' -> ', ), (f"{st.get('frac_max_length')}", UI.LIGHTBLUE_ON_BLACK))
            elif m := re.match(r'\s*prec(?:ision)?(?:\s+(\d+))?$', inp):
                if m.group(1) is not None: st.set("working_precision", int(m.group(1)))
                ui.addText("display", ("working_precision", UI.LIGHTBLUE_ON_BLACK), (' -> ', ), (f"{st.get('working_precision')}", UI.LIGHTBLUE_ON_BLACK))
            elif m := re.match(r'\s*disp(?:lay)?(?:\s+(\d+))?$', inp):
                if m.group(1) is not None: st.set("final_precision", int(m.group(1)))
                ui.addText("display", ("final_precision", UI.LIGHTBLUE_ON_BLACK), (' -> ', ), (f"{st.get('final_precision')}", UI.LIGHTBLUE_ON_BLACK))
            elif m := re.match(r'\s*debug(?:\s+(\w+))?$', inp):
                flag = {'on':True, 'off':False}.get(m.group(1) if m.group(1) is None else m.group(1).lower(), None)
                if flag is not None: st.set("debug", flag)
                else: ui.addText("display", ("Usage: ", ), ("debug [on/off]", UI.LIGHTBLUE_ON_BLACK))
                ui.addText("display", ("debug", UI.LIGHTBLUE_ON_BLACK), (" -> ", ), (f"{st.get('debug')}", UI.LIGHTBLUE_ON_BLACK))
            elif inp.strip() == '':
                continue
            elif m := re.match(r'(?:=|sto(?:re)? |->)\s*([A-Za-z]\w*)', inp):
                if (ans := mainMem.get('ans')) is None:
                    ui.addText("display", ("Variable '", ), ("ans", UI.LIGHTBLUE_ON_BLACK), ("' does not exist or has been deleted", ))
                else:
                    mainMem.add(m.group(1), ans)
                    ui.trie.insert(m.group(1))
                    ui.addText("display", (f'{m.group(1)}', UI.LIGHTBLUE_ON_BLACK), (' = ', ), (f'{mainMem.get(m.group(1)).value()}', UI.LIGHTBLUE_ON_BLACK))
            else:
                expr = parse(inp)
                if expr is None: continue
                val = expr.value(mainMem)
                if isinstance(val, Number): val = val.fastContinuedFraction(epsilon=st.finalEpsilon)
                mainMem.add('ans', val)
                ui.addText("display", (val.disp(st.get('frac_max_length'), st.get('final_precision')), UI.BRIGHT_GREEN_ON_BLACK))
            if mainMem._varsVersion != currVersion:
                mainMem.save(memPath)
                currVersion = mainMem._varsVersion
        except CalculatorError as e:
            if len(e.args) > 1: ui.addText("display", (' ' * (len(ui.prompt) + (span := e.args[1])[0] - 1) + '↗' + '‾' * (span[1] - span[0]), UI.BRIGHT_RED_ON_BLACK))
            ui.addText("display", (f"{repr(e).split('(')[0]}: {e.args[0]}", UI.BRIGHT_RED_ON_BLACK))
            # raise e
        except ZeroDivisionError as e:
            ui.addText("display", (repr(e), UI.BRIGHT_RED_ON_BLACK))
        except RecursionError:
            ui.addText("display", ("RecursionError: Check for infinite recursion in functions.", UI.BRIGHT_RED_ON_BLACK))
        except (EOFError, KeyboardInterrupt):
            break
        ui.redraw("display")

    ui.end()

if __name__ == '__main__':
    sys.setrecursionlimit(500000)
    main()