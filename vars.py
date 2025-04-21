class Value:    
    def __init__(self, name='<Value>', value=None):
        self.name = name
        self._value = value

    def __str__(self):
        return self.name

    def __repr__(self): return str(self)

    def __len__(self): return 1

    def disp(self, fracMaxLength, finalPrecision):
        return str(self)

    def value(self, *args, **kwargs):
        raise NotImplementedError(f'subclass {type(self)} has no implementation of value()')


class Var(Value):
    def __init__(self, name):
        super().__init__(name=name)

    def value(self, *args, mem=None, **kwargs):
        from errors import EvaluationError
        if mem is None: raise EvaluationError(f"No memory provided to Var object '{self.name}'")
        val = mem.get(self.name)
        if val is None: raise EvaluationError(f"Variable '{self.name}' not found in memory!")
        return val


class LValue(Value):  # variable ready for assignment. Has NO value
    def __init__(self, name='<lValue>', value=None):
        super().__init__(name=name, value=value)

    def value(self, *args, **kwargs):
        # return self._value if self._value is not None else self.name
        return self

    def makeVar(self, value=None):
        if value is None: raise ValueError(f'No value to assign to "{self.name}"')
        return Var(name=self.name, value=value)


class WordToken:
    def __init__(self, name='<wordToken>'):
        self.name = name

    def __str__(self):
        return str(self.name)
    
    def splitWordToken(self, mem, nextToken):
        from operators import Prefix
        from number import Number, RealNumber
        from functions import Function
        from errors import ParseError
        # returns a list of possible splits of the string.
        # 'greediest' (longer tokens are prioritized) splits come first.
        def trySplit(s, numAllowed=False, onlyFuncsAllowed=False):
            if s == '': return [[]], [[]]
            lst, varList = [], []
            for i in reversed(range(len(s))):
                if (thisWord := s[:i+1]) in wordDict:
                    if isinstance(wordDict[thisWord], Number): thisWord = Var(thisWord)
                    else: thisWord = wordDict[thisWord]
                    if onlyFuncsAllowed and type(thisWord) != Function: continue
                    if i == len(s) - 1 and type(thisWord) == Prefix and not isinstance(nextToken, Value): continue  # allow stuff like 'ksin3.0pi'
                elif numAllowed and not onlyFuncsAllowed and s[:i+1].isdigit() and not s[i+1:i+2].isdigit():
                    thisWord = RealNumber(s[:i+1])
                else:
                    continue
                splitRest, splitRestVars = trySplit(s[i+1:], numAllowed=(type(thisWord) == Prefix), onlyFuncsAllowed=(type(thisWord) == Function))
                lst += [[s[:i+1]] + spl for spl in splitRest]
                varList += [[thisWord] + spl for spl in splitRestVars]
            return lst, varList
        
        wordDict = mem if isinstance(mem, dict) else mem.update
        splitList, varList = trySplit(self.name)

        if len(splitList) == 0: raise ParseError(f"Unable to parse '{self.name}'")
        # tmp = ['∙'.join(s) for s in splitList]
        if len(splitList) > 1:
            from UI import UI
            UI().addText("display", ("Warning: ", UI.YELLOW_ON_BLACK), (f"Found {len(splitList)} ways to parse ", ), (self.name, UI.BRIGHT_PURPLE_ON_BLACK), ('.', ))
            tmp = [item for substr in splitList[0] for item in ((substr, UI.BRIGHT_PURPLE_ON_BLACK), ("∙", ))][:-1]
            UI().addText("display", (" (Using ", ), *tmp, (")", ), startNewLine=False)
            # ': " + ", ".join(tmp) + f". (selecting '{tmp[0]}')")
        return splitList[0], varList[0]

    def toLValue(self):
        return LValue(name=self.name)

    def toLFunc(self):
        from functions import LFunc
        return LFunc(name=self.name)
    
    @property
    def memory(self):
        from memory import Memory
        if self.funcMem is not None: wordDict = Memory.combine(self.userMem, self.funcMem)
        else: wordDict = self.userMem.full
        return wordDict

