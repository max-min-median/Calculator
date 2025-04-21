import curses
import os
import platform
import subprocess
from trie import Trie
from functions import Function
from operators import Operator

system = platform.system()
calcSplash = "MaxCalc v2.3.0-beta by max_min_median"

try:
    raise ImportError
    import keyboard
    keyboard.is_pressed(29)  # start up `keyboard` listener
except ImportError:
    keyboard = type('DummyKeyboard', (), {'is_pressed': lambda self, *args: None})()

# - history
# - copy from display

class UI:

    _instance = None

    keymap = {
        "Windows":
        {
            443: {"key": curses.KEY_LEFT, "modifiers": {"ctrl"}},
            444: {"key": curses.KEY_RIGHT, "modifiers": {"ctrl"}},
            480: {"key": curses.KEY_UP, "modifiers": {"ctrl"}},
            481: {"key": curses.KEY_DOWN, "modifiers": {"ctrl"}},
            391: {"key": curses.KEY_LEFT, "modifiers": {"shift"}},
            400: {"key": curses.KEY_RIGHT, "modifiers": {"shift"}},
            547: {"key": curses.KEY_UP, "modifiers": {"shift"}},
            548: {"key": curses.KEY_DOWN, "modifiers": {"shift"}},
            449: {"key": curses.KEY_HOME, "modifiers": {}},
            388: {"key": curses.KEY_HOME, "modifiers": {"shift"}},
            449: {"key": curses.KEY_HOME, "modifiers": {}},
            388: {"key": curses.KEY_HOME, "modifiers": {"shift"}},
            455: {"key": curses.KEY_END, "modifiers": {}},
            384: {"key": curses.KEY_END, "modifiers": {"shift"}},
           1001: {"key": curses.KEY_LEFT, "modifiers": {"ctrl", "shift"}},
        },
    
        "Linux":
        {
            554: {"key": curses.KEY_LEFT, "modifiers": {"ctrl"}},
            569: {"key": curses.KEY_RIGHT, "modifiers": {"ctrl"}},
            393: {"key": curses.KEY_LEFT, "modifiers": {"shift"}},
            402: {"key": curses.KEY_RIGHT, "modifiers": {"shift"}},
            555: {"key": curses.KEY_LEFT, "modifiers": {"ctrl", "shift"}},
            570: {"key": curses.KEY_RIGHT, "modifiers": {"ctrl", "shift"}},
        }
    }

    pairIdx = None
    @staticmethod
    def makeColorPair(fg, bg):
        UI.pairIdx += 1
        curses.init_pair(UI.pairIdx, fg, bg)
        return curses.color_pair(UI.pairIdx)

    @staticmethod
    def isWordChar(char):
        ascii = ord(char)
        return 65 <= ascii <= 90 or 97 <= ascii <= 122 or char in "_'"  # or 48 <= ascii <= 57

    @staticmethod
    def getInstance():
        return UI._instance


    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self, settings):
        
        if hasattr(self, 'initialized'): return
        else: self.initialized = True

        self.st = settings
        # Initialize curses
        self.stdscr = curses.initscr()
        curses.update_lines_cols()
        curses.raw()
        curses.noecho()
        self.stdscr.keypad(1)
        try: curses.start_color()
        except: pass
        curses.use_default_colors()

        if UI.pairIdx is None:
            UI.pairIdx = 0
            UI.YELLOW_ON_BLACK = UI.makeColorPair(226, -1)
            UI.GREY_ON_BLACK = UI.makeColorPair(241, -1)
            UI.GREEN_ON_BLACK = UI.makeColorPair(10, -1)
            UI.LIGHTBLUE_ON_BLACK = UI.makeColorPair(69, -1)
            UI.BRIGHT_PURPLE_ON_BLACK = UI.makeColorPair(201, -1)
            UI.DARK_PURPLE_ON_BLACK = UI.makeColorPair(129, -1)
            UI.BRIGHT_ORANGE_ON_BLACK = UI.makeColorPair(202, -1)
            UI.DIM_ORANGE_ON_BLACK = UI.makeColorPair(208, -1)
            UI.BRIGHT_GREEN_ON_BLACK = UI.makeColorPair(46, -1)
            UI.BRIGHT_RED_ON_BLACK = UI.makeColorPair(196, -1)
            UI.WHITE_ON_BLUE = UI.makeColorPair(-1, 21)
            UI.YELLOW_ON_BLUE = UI.makeColorPair(226, 21)
            UI.GREY_ON_BLUE = UI.makeColorPair(241, 21)
            # (prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙

        self.quickExponents = True
        # self.mem = memory
        self.statusDuration = 0
        # (prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙
        self.prompt = (("♦", UI.BRIGHT_ORANGE_ON_BLACK), (">", UI.DIM_ORANGE_ON_BLACK), (" "))
        self.text = {"display": [], "status": [[]], "input": []}
        self.inputHistory = []
        self.selectionAnchor = None
        self.pos = 0
        self.setupWindows(firstRun=True)


    def copyToClipboard(self, s):
        if system == "Windows": subprocess.run("clip", input=s.encode("utf-8"), check=True)
        elif system == "Darwin": subprocess.run("pbcopy", input=s.encode("utf-8"), check=True)
        elif system == "Linux": 
            if subprocess.run(["which", "xclip"], capture_output=True).returncode == 0:
                subprocess.run(["xclip", "-selection", "clipboard"], input=s.encode("utf-8"), check=True)
            elif subprocess.run(["which", "xsel"], capture_output=True).returncode == 0:
                subprocess.run(["xsel", "--clipboard"], input=s.encode("utf-8"), check=True)
            else:
                self.text["status"] = [[("No clipboard utility found. Install xclip or xsel."[:self.stdscr.getmaxyx()[1] - 3], UI.BRIGHT_RED_ON_BLACK)]]
                self.statusDuration = 1
                self.redraw("status", limitWidth=True)
                self.subwins["status"].refresh()


    def setupWindows(self, firstRun=False) -> dict[str, curses.window]:
        os.system("cls" if os.name == "nt" else "clear")
        curses.raw()
        self.stdscr.erase()
        self.ht, self.wd = self.stdscr.getmaxyx()
        self.subwins = {}
        if self.ht < 17 or self.wd < 44:
            if self.ht > 3 and self.wd > 15:
                self.stdscr.addstr(self.ht // 2, self.wd // 2 - 6, "Too small :(")
                self.stdscr.refresh()
            return False
        self.stdscr.addstr(0, (self.wd - len(calcSplash)) // 2, calcSplash, UI.LIGHTBLUE_ON_BLACK)
        self.stdscr.subwin(self.ht * 3 // 4, self.wd, 1, 0).box()  # rows, cols, startrow, startcol
        self.subwins["display"] = self.stdscr.subwin(self.ht * 3 // 4 - 2, self.wd - 2, 2, 1)
        self.subwins["display"].leaveok(True)
        self.subwins["display"].scrollok(True)
        # self.stdscr.subwin(ht // 3, wd, ht // 3, 0).box()
        self.subwins["status"] = self.stdscr.subwin(1, self.wd - 1, self.ht * 3 // 4 + 1, 1)
        self.subwins["status"].leaveok(True)
        self.subwins["status"].scrollok(True)
        if firstRun:
            self.addText("status", ("Hello :) Type 'help' for a quick guide!", UI.GREEN_ON_BLACK))
        self.redraw("status", limitWidth=True)
        self.stdscr.subwin(self.ht - self.ht * 3 // 4 - 2, self.wd, self.ht * 3 // 4 + 2, 0).box()
        self.subwins["input"] = self.stdscr.subwin(self.ht - self.ht * 3 // 4 - 4, self.wd - 2, self.ht * 3 // 4 + 3, 1)
        self.subwins["input"].leaveok(True)
        self.subwins["input"].scrollok(True)
        return self.subwins


    def getWordAtPos(self, text, pos):  # returns (currWord, wordL, wordR)
        if not (pos > 0 and UI.isWordChar(text[pos - 1])) and not (pos < len(text) and UI.isWordChar(text[pos])):
            return None, len(text), 0
        else:
            wordL = wordR = pos
            while wordL > 0 and UI.isWordChar(text[wordL - 1]): wordL -= 1
            while wordR < len(text) and UI.isWordChar(text[wordR]): wordR += 1
            return ''.join(text[wordL:wordR]), wordL, wordR


    def getInput(self, trie: Trie=None):
        if trie is not None: self.trie = trie
        text = []
        keys = []
        nearestWords = []
        self.pos = 0
        historyIndex = 0
        self.currWord = self.prevWord = None
        self.wordL, self.wordR = len(text), 0
        tabbed = False
        self.drawInput(text)

        while True:
            if keys == []:
                key = self.stdscr.getch()
                self.stdscr.nodelay(True)
                while (k := self.stdscr.getch()) != -1: keys.append(k)
                keys.reverse()
                self.stdscr.nodelay(False)
            else:
                key = keys.pop()

            if (keyCombo := UI.keymap[system].get(key, None)): key = keyCombo["key"]
            shiftPressed = keyCombo is not None and "shift" in keyCombo["modifiers"] or keyboard.is_pressed(42) or keyboard.is_pressed(54)
            ctrlPressed = keyCombo is not None and "ctrl" in keyCombo["modifiers"] or keyboard.is_pressed(29)

            if key == 55 and (shiftPressed or keyboard.is_pressed(71)): key = curses.KEY_HOME
            elif key == 49 and (shiftPressed or keyboard.is_pressed(79)): key = curses.KEY_END

            # Handle window resizing
            if key == curses.KEY_RESIZE:
                if not self.setupWindows():
                    while key := self.getch():
                        if key in (17, 27, 433): raise KeyboardInterrupt("Esc")
                        curses.update_lines_cols()
                        if self.setupWindows():
                            break
                self.redraw("display")
                self.redraw("input")
                continue

            if self.statusDuration > 0:
                self.statusDuration -= 1
                if self.statusDuration == 0: self.redraw("status", limitWidth=True)

            # Resolve tabbed state if the current key is not a tab or resize
            if tabbed is not False and key not in (9, 351, curses.KEY_RESIZE):
                text[self.wordL:self.wordR] = [*self.currWord + nearestWords[tabbed][len(self.currWord):]]
                self.pos = self.wordL + len(nearestWords[tabbed])
                tabbed = False

            # Register history as current input if a key is pressed which is not KEY_UP or KEY_DOWN.
            if historyIndex != 0 and key not in (curses.KEY_UP, curses.KEY_DOWN):
                if key in (curses.KEY_ENTER, 10, 13, 459):
                    self.inputHistory.pop(historyIndex)
                historyIndex = 0

            if key == 21:  # Ctrl-U = Ctrl-A then Backspace
                curses.ungetch(curses.KEY_BACKSPACE)
                curses.ungetch(1)  # Ctrl-A
                continue
            elif key == 24:  # Ctrl-X = Ctrl-C then Backspace
                if self.selectionAnchor is not None:
                    curses.ungetch(curses.KEY_BACKSPACE)
                    curses.ungetch(3)  # Ctrl-C
                continue

            if key == 1:  # Ctrl-A
                self.selectionAnchor = 0
                self.pos = len(text)
            elif key in (curses.KEY_BACKSPACE, 8, 127, curses.KEY_DC) and self.selectionAnchor is not None:
                selectL, selectR = sorted([self.selectionAnchor, self.pos])
                text[selectL:selectR] = []
                self.pos = selectL
                self.selectionAnchor = None
            elif key == 127:
                curses.ungetch(curses.KEY_BACKSPACE)
                curses.ungetch(1001)
                continue
            elif key in (curses.KEY_BACKSPACE, 8) and self.pos > 0:
                self.pos -= 1
                text[self.pos:self.pos+1] = []
            elif key == curses.KEY_DC and self.pos < len(text):
                text[self.pos:self.pos+1] = []
            elif key in (curses.KEY_UP, curses.KEY_DOWN):
                if key == curses.KEY_UP:
                    if -historyIndex == len(self.inputHistory): continue
                    if historyIndex == 0:
                        currentText = text
                    historyIndex -= 1
                    text = [*self.inputHistory[historyIndex]]
                    self.pos = len(text)
                else:  # curses.KEY_DOWN
                    if historyIndex == 0: continue
                    historyIndex += 1
                    if historyIndex == 0:
                        text = currentText
                    else:
                        text = [*self.inputHistory[historyIndex]]
                    self.pos = len(text)
            elif key in (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP, curses.KEY_DOWN, curses.KEY_HOME, curses.KEY_END):
                if shiftPressed:
                    if self.selectionAnchor is None: self.selectionAnchor = self.pos
                else:
                    self.selectionAnchor = None
                if key == curses.KEY_LEFT:
                    self.pos -= 1
                    if ctrlPressed:
                        while self.pos > 0 and (not UI.isWordChar(text[self.pos]) or UI.isWordChar(text[self.pos-1])): self.pos -= 1
                elif key == curses.KEY_RIGHT:
                    self.pos += 1
                    if ctrlPressed:
                        while self.pos < len(text) and (not UI.isWordChar(text[self.pos-1]) or self.pos < len(text) and UI.isWordChar(text[self.pos])): self.pos += 1
                elif key == curses.KEY_HOME: self.pos = 0
                elif key == curses.KEY_END: self.pos = len(text)
                self.pos = min(len(text), max(self.pos, 0))
                if self.selectionAnchor == self.pos: self.selectionAnchor = None
            elif key in (9, 351):  # TAB
                self.selectionAnchor = None
                if not nearestWords: continue
                if tabbed is False: tabbed = ((nearestWords[0] == self.currWord) if key == 9 else -1) % len(nearestWords)
                else: tabbed = (tabbed + (1 if key == 9 else -1)) % len(nearestWords)
            elif 32 <= key <= 126:  # usual alphanumeric + symbols
                # quickExponents
                typed = [*(('^' if 48 <= key <= 57 and self.quickExponents and self.pos > 0 and (text[self.pos - 1] in ')]}' or self.wordR == self.pos and not isinstance(self.mem.get(self.currWord), (Operator))) else '') + chr(key))]
                
                if self.selectionAnchor is not None:
                    selectL, selectR = sorted([self.selectionAnchor, self.pos])
                    text[selectL:selectR] = typed
                    self.pos = selectL + len(typed)
                    self.selectionAnchor = None
                else:
                    text[self.pos:self.pos] = typed
                    self.pos += len(typed)
            elif key in (curses.KEY_ENTER, 10, 13, 459):  # Enter
                result = ''.join(text).strip()
                if result:
                    self.subwins["status"].erase()
                    self.subwins["status"].refresh()
                    if len(self.text["display"]) > 0: self.addText("display")
                    self.addText("display", *self.prompt, (result, ))
                    self.inputHistory.append(result)
                    return result
                # ignore empty input
                text = []
                self.pos = 0
            elif key == 3:
                if self.selectionAnchor is not None:
                    selectL, selectR = sorted([self.selectionAnchor, self.pos])
                    self.copyToClipboard(''.join(text[selectL:selectR]))
            elif key in (17, 27, 433):
                raise KeyboardInterrupt("Esc")
            
            self.currWord, self.wordL, self.wordR = self.getWordAtPos(text, self.pos)
            if self.prevWord != self.currWord:
                self.text["status"] = [[]]
                self.prevWord = self.currWord
                if self.currWord:
                    nearestWords = self.trie.nearestAutocomplete(self.currWord)
                    tabbed = False
                    # update text of status/autocomplete bar
                    spaces = ''
                    for word in nearestWords:
                        self.addText("status", (spaces, ), (word[:len(self.currWord)], UI.GREEN_ON_BLACK), (word[len(self.currWord):], UI.GREY_ON_BLACK), startNewLine=False)
                        spaces = '   '
                else:
                    nearestWords = []
                if self.statusDuration == 0: self.redraw("status", limitWidth=True)

            if keys: continue

            self.drawInput(text, tabbed, nearestWords)


    def drawInput(self, text, tabbed=False, nearestWords=[]):
        # redraws the input window and relocates the cursor
        if not self.subwins: return

        selectL, selectR = sorted([self.selectionAnchor, self.pos]) if self.selectionAnchor is not None else (len(text), 0)
        self.text["input"].clear()
        self.addText("input", *self.prompt)

        # 1. print left part
        self.addText("input", (''.join(text[:min(self.wordL, selectL)]), ), startNewLine=False)
        # 2. print from left end of selection to left end of autocomplete
        self.addText("input", (''.join(text[selectL:min(self.wordL, selectR)]), UI.WHITE_ON_BLUE), startNewLine=False)
        # 3. print from left end of autocomplete to left end of selection
        self.addText("input", (''.join(text[self.wordL:min(selectL, self.wordR)]), UI.YELLOW_ON_BLACK), startNewLine=False)
        # 4. print overlap of selection and autocomplete
        self.addText("input", (''.join(text[max(selectL, self.wordL):min(selectR, self.wordR)]), UI.YELLOW_ON_BLUE), startNewLine=False)
        # 5. print from right end of selection to right end of autocomplete
        self.addText("input", (''.join(text[max(selectL, selectR):self.wordR]), UI.YELLOW_ON_BLACK), startNewLine=False)

        if nearestWords:
            if tabbed is False: self.addText("input", (nearestWords[0][len(self.currWord):], UI.GREY_ON_BLUE if selectL <= self.wordR < selectR else UI.GREY_ON_BLACK), startNewLine=False)
            else: self.addText("input", (nearestWords[tabbed][len(self.currWord):], UI.YELLOW_ON_BLACK), startNewLine=False)

        # 6. print from right end of autocomplete to right end of selection
        self.addText("input", (''.join(text[max(self.wordR, self.wordL):selectR]), UI.WHITE_ON_BLUE), startNewLine=False)
        # 7. print right part
        self.addText("input", (''.join(text[max(self.wordR, selectR, min(self.wordL, selectL)):]), ), startNewLine=False)

        # self.useWin("display").addstr(f"{self.stdscr.getmaxyx()} Key: {key} Str: {''.join(text)}\n").refresh()
        curses.curs_set(0)
        self.subwins["input"].move(*divmod(len(self.prompt) + (self.pos if tabbed is False else self.wordL + len(nearestWords[tabbed])), self.wd - 2))
        self.subwins["input"].cursyncup()
        self.redraw("input")
        curses.curs_set(1)
        curses.doupdate()


    def addText(self, windowName, *strAndAttrTuples, startNewLine=True):
        if startNewLine:
            self.text[windowName].append([])
        self.text[windowName][-1] += strAndAttrTuples
        return self


    def redraw(self, windowName, limitWidth=False):  # does not call doupdate
        window = self.subwins[windowName]
        window.erase()
        firstLine = True
        for line in self.text[windowName]:
            if not firstLine: window.addstr('\n')
            firstLine = False
            if limitWidth:
                charsLeft = self.wd - 2
                for item in line:  # either 1- or 2-tuple
                    if charsLeft == 0: break
                    lst = [*item]
                    charsLeft -= (lenToAdd := min(charsLeft, len(item[0])))
                    lst[0] = lst[0][:lenToAdd]
                    window.addstr(*lst)
            else:
                for item in line:
                    window.addstr(*item)
                    
        window.noutrefresh()


    def end(self):
        # Set everything back to normal
        self.stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()


if __name__ == "__main__":
    # import tracemalloc
    # tracemalloc.start()
    # print("Loading dictionary...")
    # trie = Trie.fromTextFile('google-10000-english.txt')
    # mem_size, _mem_peak = tracemalloc.get_traced_memory()
    # print(f"Memory used: {mem_size=} bytes")
    # print(f"Trie stats:")
    # print(f"{trie.numWords() = }\n{trie.numChars() = }\n{trie.numNodes() = }")
    # print("Press any key...")
    ui = UI()
    # curses.raw()
    # ui.trie = trie
    while True:
        k = ui.stdscr.getch()
        ui.stdscr.addstr(f'key {str(k)} typed.\n')
        ui.stdscr.refresh()