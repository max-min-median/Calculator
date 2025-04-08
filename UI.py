import curses
import keyboard
import os
import subprocess
from Trie import Trie
from Functions import Function
from Operators import Operator


class UI:

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
    def copyToClipboard(s):
        subprocess.run("clip", input=s.encode("utf-8"), check=True)


    def __init__(self, memory=None):

        # Initialize curses
        os.system("cls" if os.name == "nt" else "clear")
        self.stdscr = curses.initscr()
        curses.update_lines_cols()
        self.cursesInit()
        keyboard.is_pressed(29)  # start up `keyboard` listener

        if UI.pairIdx is None:
            UI.pairIdx = 0
            UI.YELLOW_ON_BLACK = UI.makeColorPair(226, 0)
            UI.GREY_ON_BLACK = UI.makeColorPair(241, 0)
            UI.GREEN_ON_BLACK = UI.makeColorPair(10, 0)
            UI.LIGHTBLUE_ON_BLACK = UI.makeColorPair(69, 0)
            UI.BRIGHT_PURPLE_ON_BLACK = UI.makeColorPair(201, 0)
            UI.DARK_PURPLE_ON_BLACK = UI.makeColorPair(129, 0)
            UI.BRIGHT_ORANGE_ON_BLACK = UI.makeColorPair(202, 0)
            UI.DIM_ORANGE_ON_BLACK = UI.makeColorPair(208, 0)
            UI.BRIGHT_GREEN_ON_BLACK = UI.makeColorPair(46, 0)
            UI.BRIGHT_RED_ON_BLACK = UI.makeColorPair(196, 0)
            UI.WHITE_ON_BLUE = UI.makeColorPair(7, 21)
            UI.YELLOW_ON_BLUE = UI.makeColorPair(226, 21)
            UI.GREY_ON_BLUE = UI.makeColorPair(241, 21)
            # (prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙

        self.quickExponents = True
        self.mem = memory
        self.prompt = (("♦", UI.BRIGHT_ORANGE_ON_BLACK), (">", UI.DIM_ORANGE_ON_BLACK), (" "))
        self.text = {"display": [], "status": [], "input": []}
        self.selectionAnchor = None
        self.setupWindows()


    def cursesInit(self):
        # Turn off echoing of keys, and enter cbreak mode, where no buffering is performed on keyboard input
        curses.raw()
        curses.noecho()
        # cbreak()
        # nonl()

        # In keypad mode, escape sequences for special keys (like the cursor keys) will be interpreted and
        # a special value like curses.KEY_LEFT will be returned
        self.stdscr.keypad(1)

        # Start color, too.  Harmless if the terminal doesn't have color; user can test with has_color() later on.
        # The try/catch works around a minor bit of over-conscientiousness in the curses module --
        # the error return from C start_color() is ignorable.
        try: curses.start_color()
        except: pass


    def setupWindows(self) -> dict[str, curses.window]:
        self.stdscr.erase()
        ht, wd = self.stdscr.getmaxyx()
        self.stdscr.addstr(0, (wd - len(s := "Calculator v2.0.0-beta by max_min_median")) // 2, s, UI.LIGHTBLUE_ON_BLACK)
        self.subwins = {}
        self.stdscr.subwin(ht * 3 // 4, wd, 1, 0).box()  # rows, cols, startrow, startcol
        self.subwins["display"] = self.stdscr.subwin(ht * 3 // 4 - 2, wd - 2, 2, 1)
        self.subwins["display"].leaveok(True)
        self.subwins["display"].scrollok(True)
        # self.stdscr.subwin(ht // 3, wd, ht // 3, 0).box()
        self.subwins["status"] = self.stdscr.subwin(1, wd - 2, ht * 3 // 4 + 1, 1)
        self.subwins["status"].leaveok(True)
        self.subwins["status"].scrollok(True)
        self.useWin("status").addText(("Hello :) Type 'help' for a quick guide!", UI.GREEN_ON_BLACK)).redraw()
        self.stdscr.subwin(ht - ht * 3 // 4 - 2, wd, ht * 3 // 4 + 2, 0).box()
        self.subwins["input"] = self.stdscr.subwin(ht - ht * 3 // 4 - 4, wd - 2, ht * 3 // 4 + 3, 1)
        self.subwins["input"].leaveok(True)
        self.subwins["input"].scrollok(True)
        return self.subwins


    def useWin(self, win):
        self.currWin = win
        return self


    def erase(self):
        self.subwins[self.currWin].erase()
        return self
    

    def cursyncup(self):
        self.subwins[self.currWin].cursyncup()
        return self


    def move(self, *args):
        self.subwins[self.currWin].move(*args)
        return self


    def getch(self):
        return self.stdscr.getch()


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
        # ht, wd = self.subwins["input"].getmaxyx()
        text = []
        nearestWords = []
        pos = 0
        wd = self.subwins["input"].getmaxyx()[1]
        prevWord = None
        tabbed = False
        # self.useWin("input").cursyncup().refresh()

        while True:

            # print(f"Selection: ({self.selectionAnchor}, {pos})\n")
            # detect word on cursor position
            currWord, wordL, wordR = self.getWordAtPos(text, pos)
            if currWord is None: nearestWords = []

            self.text["status"] = [[]]
            self.text["input"] = []

            # print input
            selectL, selectR = sorted([self.selectionAnchor, pos]) if self.selectionAnchor is not None else (len(text), 0)
            self.useWin("input").addText(*self.prompt)
            if currWord is None and self.selectionAnchor is None:
                self.addText((''.join(text), ), startNewLine=False)
                prevWord = currWord
            else:
                # 1. print left part
                self.addText((''.join(text[:min(wordL, selectL)]), ), startNewLine=False)
                # 2. print from left end of selection to left end of autocomplete
                self.addText((''.join(text[selectL:min(wordL, selectR)]), UI.WHITE_ON_BLUE), startNewLine=False)
                # 3. print from left end of autocomplete to left end of selection
                self.addText((''.join(text[wordL:min(selectL, wordR)]), UI.YELLOW_ON_BLACK), startNewLine=False)
                # 4. print overlap of selection and autocomplete
                self.addText((''.join(text[max(selectL, wordL):min(selectR, wordR)]), UI.YELLOW_ON_BLUE), startNewLine=False)
                # 5. print from right end of selection to right end of autocomplete
                self.addText((''.join(text[max(selectL, selectR):wordR]), UI.YELLOW_ON_BLACK), startNewLine=False)

                # autocomplete
                if currWord:
                    if prevWord != currWord:
                        nearestWords = self.trie.nearestAutocomplete(currWord)
                        prevWord = currWord
                        tabbed = False
                    
                    # print status/autocomplete bar
                    self.useWin("status")
                    spaces = ''
                    while len('   '.join(nearestWords)) >= wd:
                        nearestWords.pop()
                    for word in nearestWords:
                        self.addText((spaces, ), (word[:len(currWord)], UI.GREEN_ON_BLACK), (word[len(currWord):], UI.GREY_ON_BLACK), startNewLine=False)
                        spaces = '   '
                    
                    self.useWin("input")
                    if nearestWords:
                        casefunc = str.upper if currWord.isupper() else lambda x: x
                        if tabbed is False: self.addText((casefunc(nearestWords[0][len(currWord):]), UI.GREY_ON_BLUE if selectL <= wordR < selectR else UI.GREY_ON_BLACK), startNewLine=False)
                        else: self.addText((casefunc(nearestWords[tabbed][len(currWord):]), UI.YELLOW_ON_BLACK), startNewLine=False)
                else:
                    prevWord = currWord

                # 6. print from right end of autocomplete to right end of selection
                self.addText((''.join(text[max(wordR, wordL):selectR]), UI.WHITE_ON_BLUE), startNewLine=False)
                # 7. print right part
                self.addText((''.join(text[max(wordR, selectR):]), ), startNewLine=False)


            # self.useWin("display").addstr(f"{self.stdscr.getmaxyx()} Key: {key} Str: {''.join(text)}\n").refresh()
            curses.curs_set(0)
            self.useWin("input").move(*divmod(len(self.prompt) + (pos if tabbed is False else wordL + len(nearestWords[tabbed])), wd)).cursyncup().redraw()
            self.useWin("status").redraw()
            self.useWin("input").redraw()
            curses.curs_set(1)
            curses.doupdate()

            key = self.getch()
            shiftPressed = keyboard.is_pressed(42) or keyboard.is_pressed(54)

            if key == curses.KEY_RESIZE:
                self.subwins = self.setupWindows()
                wd = self.subwins["input"].getmaxyx()[1]
                self.useWin("display").redraw()
                continue

            if key == 1:  # Ctrl-A
                self.selectionAnchor = 0
                pos = len(text)
                continue

            if tabbed is not False and key not in (9, 351, curses.KEY_RESIZE):
                text[wordL:wordR] = [*currWord + casefunc(nearestWords[tabbed][len(currWord):])]
                pos = wordL + len(nearestWords[tabbed])
                tabbed = False

            if key == 55 and (shiftPressed or keyboard.is_pressed(71)): key = curses.KEY_HOME
            elif key == 49 and (shiftPressed or keyboard.is_pressed(79)): key = curses.KEY_END

            if key in (curses.KEY_BACKSPACE, 8, 127, curses.KEY_DC, 24) and self.selectionAnchor is not None:
                selectL, selectR = sorted([self.selectionAnchor, pos])
                if key == 24: UI.copyToClipboard(''.join(text[selectL:selectR]))
                text[selectL:selectR] = []
                pos = selectL
                self.selectionAnchor = None
            elif key in (curses.KEY_BACKSPACE, 8, 127) and pos > 0:
                pos -= 1
                text[pos:pos+1] = []
            elif key == curses.KEY_DC and pos < len(text):
                text[pos:pos+1] = []
            elif key in (curses.KEY_LEFT, 391, 443, curses.KEY_RIGHT, 400, 444, curses.KEY_UP, 547, 480, curses.KEY_DOWN, 548, 481, curses.KEY_HOME, 449, 388, curses.KEY_END, 455, 384):
                if shiftPressed:   # key in (391, 400, 547, 548): # shift pressed
                    if self.selectionAnchor is None: self.selectionAnchor = pos
                else:
                    self.selectionAnchor = None
                if key in (curses.KEY_LEFT, 391, 443):
                    pos -= 1
                    if keyboard.is_pressed(29):
                        while pos > 0 and (not UI.isWordChar(text[pos]) or UI.isWordChar(text[pos-1])): pos -= 1
                elif key in (curses.KEY_RIGHT, 400, 444):
                    pos += 1
                    if keyboard.is_pressed(29):
                        while pos < len(text) and (not UI.isWordChar(text[pos-1]) or pos < len(text) and UI.isWordChar(text[pos])): pos += 1
                elif key in (curses.KEY_UP, 547, 480): pos -= wd
                elif key in (curses.KEY_DOWN, 548, 481): pos += wd
                elif key in (curses.KEY_HOME, 449, 388): pos = 0
                elif key in (curses.KEY_END, 455, 384): pos = len(text)
                pos = min(len(text), max(pos, 0))
                if self.selectionAnchor == pos: self.selectionAnchor = None
            elif key in (9, 351):  # TAB
                self.selectionAnchor = None
                if not nearestWords: continue
                if tabbed is False: tabbed = ((nearestWords[0] == currWord) if key == 9 else -1) % len(nearestWords)
                else: tabbed = (tabbed + (1 if key == 9 else -1)) % len(nearestWords)
            elif 32 <= key <= 126:  # usual alphanumeric + symbols
                # quickExponents
                typed = [*(('^' if 48 <= key <= 57 and self.quickExponents and pos > 0 and (text[pos - 1] in ')]}' or wordR == pos and not isinstance(self.mem.get(currWord), (Function, Operator))) else '') + chr(key))]
                
                if self.selectionAnchor is not None:
                    selectL, selectR = sorted([self.selectionAnchor, pos])
                    text[selectL:selectR] = typed
                    pos = selectL + len(typed)
                    self.selectionAnchor = None
                else:
                    text[pos:pos] = typed
                    pos += len(typed)
            elif key in (curses.KEY_ENTER, 10, 13, 459):  # Enter
                result = ''.join(text).strip()
                if result:
                    self.useWin("display")
                    if len(self.text["display"]) > 0: self.addText()
                    self.addText(*self.prompt, (result, ))
                    return result
                # ignore empty input
                text = []
                pos = 0
            elif key == 3:
                if self.selectionAnchor is not None:
                    selectL, selectR = sorted([self.selectionAnchor, pos])
                    UI.copyToClipboard(''.join(text[selectL:selectR]))
            elif key == 27:
                raise KeyboardInterrupt("Ctrl-C")


    def addText(self, *strAndAttrTuples, startNewLine=True):
        if startNewLine:
            self.text[self.currWin].append([])
        self.text[self.currWin][-1] += strAndAttrTuples
        return self


    def redraw(self, window=None):
        if window is not None: self.useWin(window)
        self.erase()
        firstLine = True
        for line in self.text[self.currWin]:
            if not firstLine: self.subwins[self.currWin].addstr('\n')
            firstLine = False
            for item in line:
                self.subwins[self.currWin].addstr(*item)
        self.subwins[self.currWin].noutrefresh()


    def addPrompt(self):
        # (prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙
        for charAndAttrs in self.prompt:
            self.subwins[self.currWin].addstr(*charAndAttrs)
        return self

    # def end(self):
    #     # Set everything back to normal
    #     self.stdscr.keypad(0)
    #     echo()
    #     nocbreak()
    #     endwin()


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
        k = ui.getch()
        ui.stdscr.addstr(f'key {str(k)} typed.\n')
        ui.stdscr.refresh()