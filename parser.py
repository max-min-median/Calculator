from expressions import Expression
from tuples import *
from number import RealNumber
from operators import *
from vars import LValue, WordToken, Value
import op
from errors import ParseError
import re


# Performs surface-level parsing and validation. Does not attempt to split WordTokens or evaluate expressions.

def parse(s, startPos=0, brackets='', parent=None):

    def addToken(token, m=None):  # modifies 'pos'!
        nonlocal pos
        if token is not None:
            tokens.append(token)
            posList.append(tuple(pos + x for x in m.span(1)))
            # debug and print(f'{tuple(startPos + x for x in posList[-1])}: {t}')
        if m is not None:
            pos += m.span()[1]

    def checkOpRegex():
        for regex in op.regex:
            if m := re.match(regex, ss):
                addToken(op.regex[regex], m)
                return True
        return False
    
    expr = Expression(inputStr=s, brackets=brackets, parent=parent, parentOffset=startPos)
    tokens, posList = expr.tokens, expr.tokenPos
    offsetOfParent = 0 if parent is None else parent.offset
    pos = 0
    # print(f"Parsing '{s}', brackets: {brackets}, parent: {parent}")
    while ss := s[pos:]:
        if (ch := ss[0]) == ',' or ch in ')]}' or (ch := ss[:2]) in [f'{ONE_TUPLE_INDICATOR}{ch}' for ch in ')]}']:  # last item in expression / tuple
            if expr.parent is None: raise ParseError(f"Unexpected {"comma separator ','" if ch == ',' else f"delimiter '{ch}'"} outside a tuple. Please enclose tuples in parentheses '()'.", (offsetOfParent + startPos + pos, offsetOfParent + startPos + pos + len(ch)))
            expr.inputStr = expr.inputStr[:pos]
            validate(expr)
            return expr
        elif ss[0] in '([{': # tuple or bracketed expression
            tup = Tuple(inputStr=ss[1:], brackets={'(': '()', '[': '[]', '{': '{}'}[ss[0]], parent=expr, parentOffset=pos)
            pos += 1
            tupStartPos = pos
            while True:
                exprStartPos = pos
                childExpr = parse(s[pos:], startPos=pos, brackets='', parent=tup)
                tup.tokens.append(childExpr)
                tup.tokenPos.append((exprStartPos, exprStartPos + len(childExpr.inputStr)))
                pos += len(childExpr.inputStr)
                if s[pos:pos + 1] == ',':
                    pos += 1
                elif (rb := ' ') and pos >= len(s) or (rb := s[pos]) == tup.brackets[-1] or (rb := s[pos: pos + 2]) == f'{ONE_TUPLE_INDICATOR}{tup.brackets[-1]}':
                    expr.tokenPos.append((tupStartPos, pos))
                    if len(tup) == 1 and len(tup.tokens[0].tokens) == 0:  # Tuple contains 1 empty expression; remove it.
                        tup.tokens, tup.tokenPos = [], []
                    if len(rb) != 2 and len(tup) == 1:  # convert 1-tuples to Expressions unless they end with ':)'
                        tup = tup.toExpr()
                    pos += len(rb)
                    break
            expr.tokens.append(tup)

        elif m := re.match(r'(\d+(?:\.\d*)?|\.\d+)', ss):   # Number. Cannot follow Number, spaceSeparator, or Var
            addToken(RealNumber(m.group(), fcf=True, epsilon=RealNumber(1, 10**20, fcf=False)), m)
        elif checkOpRegex():
            continue
        elif m := re.match(r'([A-Za-z](?:\w*(?:\d(?!(?:[0-9.]))|[A-Za-z_](?![A-Za-z])))?)', ss):  # Word token (might be a concatenation of vars & possible func at the end) 
            # if tokens[-1] is not None and tokens[-1] is not Op.assignment: raise ParseError(f'Cannot assign to invalid l-value (pos {startPos + pos}). Did you mean "==" instead?')
            addToken(WordToken(m.group()), m)
        else:
            raise ParseError(f"Unrecognized symbol '{ss[0]}'", (offsetOfParent + startPos + pos, offsetOfParent + startPos + pos + 1))

    validate(expr)
    return expr


def validate(expr):
    # Validation checks
    i = 1
    # Remove space separators that come at the start or end
    if len(expr.tokens) > 0 and expr.tokens[0] == op.spaceSeparator: expr.tokens.pop(0); expr.tokenPos.pop(0)
    if len(expr.tokens) > 0 and expr.tokens[-1] == op.spaceSeparator: expr.tokens.pop(); expr.tokenPos.pop()
    lst, posList = [None] + expr.tokens + [None], [None] + expr.tokenPos + [None]
    while i < len(lst) - 1:
        # Transform / remove some types of tokens
        match lst[i-1:i+2]:
            case [_any_, PrefixFunction(), None]: raise ParseError(f"Missing inputs for function '{str(lst[i])}'", expr.posOfElem(i-1))
            case [_any_, PrefixFunction(), _notExpression_] if not isinstance(_notExpression_, Expression):
                if _notExpression_ is None: raise ParseError(f"'{str(lst[i])}' must be followed by bracketed expression.", expr.posOfElem(i))
                else: raise ParseError(f"'{str(lst[i])}' must be followed by bracketed expression.", expr.posOfElem(i))
            # Bin cannot follow Bin / UL / None
            case [Infix() | Prefix() | None, Infix(), _any_]: raise ParseError(f"Unexpected operator '{str(lst[i])}'", expr.posOfElem(i-1))
            # Bin cannot precede Bin / UR / None
            case [_any_, Infix(), Infix() | Postfix()]: raise ParseError(f"Invalid operand for '{str(lst[i])}'", expr.posOfElem(i))
            case [_any_, Infix() | Prefix(), None]: raise ParseError(f"Missing operand for '{str(lst[i])}'", expr.posOfElem(i-1))
            # L to R: Convert +/- to positive/negative if they come after Bin / UL
            case [None | Infix() | Prefix(), op.ambiguousPlus | op.ambiguousMinus, _any_]:
                lst[i] = op.positive if lst[i] == op.ambiguousPlus else op.negative
                continue
            # L to R: If not, convert +/- to addition/subtraction
            case [_other_types_, op.ambiguousPlus | op.ambiguousMinus, _also_other_types_]:
                lst[i] = op.addition if lst[i] == op.ambiguousPlus else op.subtraction
                continue
            # Numbers cannot follow space separators or evaluables
            case [_any_, Value() | op.spaceSeparator, RealNumber()]: raise ParseError(f"Number '{str(lst[i+1])}' cannot follow space separator or an evaluable expression", expr.posOfElem(i))
            # UR has to follow an evaluable or other UR
            case [_operand_, Postfix(), _any_] if not isinstance(_operand_, (Value, WordToken, Postfix)): raise ParseError(f"Unexpected operator '{str(lst[i])}'", expr.posOfElem(i-1))
            # UL cannot precede Bin, UR or None
            # case [Infix() | Prefix() | Value(), LValue(), _any_] if lst[i-1] != op.assignment: raise ParseError(f"RValue cannot be the target of an assignment", expr.posOfElem(i))
            case [_any_, Expression(), op.assignment]:
                lst[i] = LTuple(lst[i])
                if isinstance(lst[i - 1], WordToken):  # combine lst[i - 1] and lst[i] into an LFunc
                    from functions import LFunc
                    lst[i - 1: i + 1] = [LFunc(lst[i - 1], lst[i])]
                    posList[i - 1: i + 1] = [(posList[i - 1][0], posList[i][1] + 1)]
                    continue
        i += 1
    expr.tokens, expr.tokenPos = lst[1:-1], posList[1:-1]

# test code
if __name__ == '__main__':
    from memory import Memory
    mem = Memory()

    def testFunc():
        exp1 = parse('f(xab, xac) = 2 + 3')
        exp2 = parse('f(foobar) = 2 + 3')
        exp3 = parse('gf(barf) = 2 + 3')
        print(exp1.value(mem=mem))
        print(exp2.value(mem=mem))
        print(exp3.value(mem=mem))
        pass

    def testTuple():
        # exp0 = parse('(3, 4) + (1, 2)')
        # exp1 = parse('5+(3+5,1,2-3)-9')
        exp01 = parse('(1, 2, 3)')
        exp5 = parse('(a,(b,c),(d=3,f)) = (1,(2,3),(,5))')
        exp0 = parse('(1 + 2)')
        exp2 = parse('5  +  (   3 +   5, 1,,2 - 3  ) - 9')
        exp3 = parse('5 + ( 3 + 5 , (1, 5, 7) , (((2 , 7), 0), 2, 5)) - 9')
        exp4 = parse('{5, 3, 2[2, 4')
        exp6 = parse('nC2')
        print(str(exp6))
        pass
    
    def test1():
        exp0 = parse('3 + 3')
        print(exp0.value(mem))
        exp1 = parse('25 - cos +3pi + (5 sqrt(4)) - 4abc + sqr')
        print(str(exp1))
        parse('5P2 + (5)')
        parse('10C3')
        parse('cos(32x+0.5) + sin(6pi/3) - f(3) + g')
        exp2 = parse('--5--4++-+3-90')
        print(str(exp2))
        parse('k f(5)') # k*f(5)
        parse('300ab^2 c') # 300a*b^2*c
        exp3 = parse('300ab^2c') # 300a*b^(2*c)
        print(str(exp3))
        parse('1/2 x') # 1/2*x
        parse('2/3x') # 2/(3*x)
        exp7 = parse('7!/5!3!') # 7!/(5!*3!)
        print(str(exp7))
        parse('2.3pi')
        parse('k')
        parse('25 - cos +3pi + (5 sqrt(4)) - 4abc + sqr')
        exp4 = parse('   2^k  x + 3^abc + 2/3 x -   3x/5')
        print(str(exp4))
        exp5 = parse('2[3 + 4{5 + 6(7/4)}]')
        print(str(exp5))
        exp6 = parse('a = bc = def = 73')
        print(str(exp6))
        exp8 = parse('5!')
        exp9 = parse('fracpix2(3ab^2-4sqrsqrt5)')
        exp10 = parse('f(g) = 35x + 2y')
        exp11 = parse('fracpix2 = 35x + 2y')
        exp12 = parse('testfunc(xy) = x + 5y - 23 cos h')
        exp13 = parse('ab = fracsin3.2(b=3)/b - 23 cos h')
        exp14 = parse('(b=2) + sinb23(x+5) cos h')
        # (b=2) + <WT>(exp)<cos><WT>
        exp14 = parse('a + (b=2)^fracsin 2b')
        # (b=2) + <WT>(exp)<cos><WT>
        # print(str(exp8))
        # print(exp11.value)
        # result = exp8.value
        # result2 = exp7.value
        pass

    testFunc()
