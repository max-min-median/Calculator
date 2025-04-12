from expressions import Expression, Tuple
from number import RealNumber
from operators import Infix, Prefix, Postfix
from vars import LValue, WordToken, Value
import op
from errors import ParseError
import re

# Performs surface-level parsing and validation. Does not attempt to split WordTokens or evaluate expressions.

def parse(s, startPos=0, brackets='', parent=None):
    def addToken(t, m=None):
        nonlocal pos
        if t is not None:
            tokens.append(t)
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
    pos = 0

    while ss := s[pos:]:
        if ss[0] in ',':  # tuple
            if not brackets and not isinstance(expr.parent, Tuple): raise ParseError(f"Unexpected comma separator ',' outside a tuple. Please enclose tuples in parentheses '()'.", (startPos + pos, startPos + pos + 1))
            if not isinstance(expr.parent, Tuple):
                tup = Tuple.fromFirst(expr)
                tup.tokenPos.append((0, pos))
                expr = tup.tokens[0]
                expr.brackets = ''
                expr.inputStr = expr.inputStr[:pos]
                validate(expr)
                endTuple = False
                pos += 1
                # start a new Expression
                while not endTuple:
                    if s[pos:] == '': break
                    tup.tokens.append(expr := parse(s[pos:], startPos=pos, brackets='', parent=tup))
                    tup.tokenPos.append((pos, pos + (l := len(expr.inputStr)) - 1))
                    validate(expr)
                    if expr.inputStr[-1] == ')':
                        endTuple = True
                    if expr.inputStr[-1] in ',)': expr.inputStr = expr.inputStr[:-1]
                    pos += len(expr.inputStr) + 1
                tup.inputStr = tup.inputStr[:pos-1]
                return tup
            else:
                expr.inputStr = expr.inputStr[:pos+1]
                validate(expr)
                return expr
        elif ss[0] in '([{': # bracketed expression
            tokens.append(parse(ss[1:], startPos=pos+1, brackets={'(': '()', '[': '[]', '{': '{}'}[ss[0]], parent=expr))
            posList.append((pos + 1, pos + 1 + (l := len(tokens[-1].inputStr))))
            pos += l + 2
        elif ss[0] in ')]}': # end of bracketed expression
            if ss[0] not in brackets and not isinstance(expr.parent, Tuple): raise ParseError(f"Unmatched right delimiter '{ss[0]}'", (startPos + pos, startPos + pos + 1))
            expr.inputStr = expr.inputStr[:pos + isinstance(expr.parent, Tuple)]  # If within a Tuple, leave the closing bracket in the string to be processed later.
            validate(expr)
            return expr
        elif m := re.match(r'(\d+(?:\.\d*)?|\.\d+)', ss):   # Number. Cannot follow Number, spaceSeparator, or Var
            addToken(RealNumber(m.group(), fcf=True, epsilon=RealNumber(1, 10**20, fcf=False)), m)
        elif checkOpRegex():
            continue
        elif m := re.match(r'([A-Za-z](?:\w*(?:\d(?!(?:[0-9.]))|[A-Za-z_](?![A-Za-z])))?)', ss):  # Word token (might be a concatenation of vars & possible func at the end) 
            # if tokens[-1] is not None and tokens[-1] is not Op.assignment: raise ParseError(f'Cannot assign to invalid l-value (pos {startPos + pos}). Did you mean "==" instead?')
            addToken(WordToken(m.group()), m)
        else:
            raise ParseError(f'Unrecognized symbol "{ss[0]}"', (startPos + pos, startPos + pos + 1))

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
            # Bin cannot follow Bin / UL / None
            case [Infix() | Prefix() | None, Infix(), _any_]: raise ParseError(f"Invalid operand for '{str(lst[i])}'", expr.posOfElem(i-1))
            # Bin cannot precede Bin / UR / None
            case [_any_, Infix(), Infix() | Postfix() | None]: raise ParseError(f"Invalid operand for '{str(lst[i])}'", expr.posOfElem(i-1))
            # L to R: Convert +/- to positive/negative if they come after Bin / UL
            case [None | Infix() | Prefix(), op.ambiguousPlus | op.ambiguousMinus, _any_]:
                lst[i] = op.positive if lst[i] == op.ambiguousPlus else op.negative
                i -= 2
            # L to R: If not, convert +/- to addition/subtraction
            case [_other_types_, op.ambiguousPlus | op.ambiguousMinus, _also_other_types_]:
                lst[i] = op.addition if lst[i] == op.ambiguousPlus else op.subtraction
                i -= 2
            # Numbers cannot follow space separators or evaluables
            case [_any_, Value() | op.spaceSeparator, RealNumber()]: raise ParseError(f'Number {str(lst[i+1])} cannot follow space separator or an evaluable expression', expr.posOfElem(i))
            # UR has to follow an evaluable or other UR
            case [_operand_, Postfix(), _any_] if not isinstance(_operand_, (Value, WordToken, Postfix)): raise ParseError(f"Invalid operand for {str(lst[i])}", expr.posOfElem(i-1))
            # UL cannot precede Bin, UR or None
            case [_any_, Prefix(), Infix() | Postfix() | None]: raise ParseError(f"Invalid operand for {str(lst[i])}", expr.posOfElem(i-1))
            case [Infix() | Prefix() | Value(), LValue(), _any_] if lst[i-1] != op.assignment: raise ParseError(f"RValue cannot be the target of an assignment ", expr.posOfElem(i))
            case _: pass
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
        # exp0 = parse('3 + 5, 2 - 3')
        exp1 = parse('5+(3+5,1,2-3)-9')
        exp2 = parse('5  +  (   3 +   5, 1,,2 - 3  ) - 9')
        exp3 = parse('5 + ( 3 + 5 , (1, 5, 7) , (((2 , 7), 0), 2, 5)) - 9')
        exp3 = parse('{5, 3, 2[2, 4')
        print(str(exp3))
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
