from expressions import Expression
from number import RealNumber
from operators import Operator, Infix, Prefix, Postfix
from vars import WordToken, Value
import op
from errors import ParseError
import re

# Performs surface-level parsing and validation. Does not attempt to split WordTokens or evaluate expressions.
# TODO: Remove dependency / references to 'mem'.

class Lexer:

    def __init__(self, expr_string='', mem=None):
        if mem is None: from memory import Memory; mem = Memory(test=True) # raise TypeError('No memory provided to lexer!')
        self._tokens = []
        self._pos_list = []
        self._pos = 0
        self.current_string = self.expr_string = expr_string
    
    def next(self):
        if len(self._tokens) > 0: return self._tokens.pop(0), self._pos_list.pop(0)
        else: return self.prep_next_token().next()

    def peek(self):
        if len(self._tokens) > 0: return self._tokens[0], self._pos_list[0]
        else: return self.prep_next_token().peek()

    def prep_next_token(self):

        def add_token(t, m):
            print(f'{self._pos:2d}: {t}')
            self._tokens.append(t)
            self._pos_list.append(self._pos + m.span(1)[0])
            self._pos += m.span()[1]
            self.current_string = self.current_string[m.span()[1]:]
            return self

        if self.current_string == '':
            self._tokens.append(None)
            self._pos_list.append(None)
            return self
                
        if m := re.match(r'([(){}[\]])', self.current_string):
            return add_token(self.current_string[0], m)
        if m := re.match(r'(\d+(?:\.\d*)?|\.\d+)', self.current_string):  # Number. Cannot follow Number, space_separator, or Var
            return add_token(RealNumber(m.group()), m)
        for regex in Op.regex:
            if m := re.match(regex, self.current_string): return add_token(Op.regex[regex], m)
        if m := re.match(r'([A-Za-z](?:\w*(?:\d(?!(?:[0-9.]))|[A-Za-z_](?![A-Za-z])))?)', self.current_string):  # Word token (might be a concatenation of vars & possible func at the end)
            return add_token(WordToken(m.group()), m)
        raise ParseError(f"Error parsing string: '{self.current_string}'")

def parse(s, start_pos=0, brackets='', mem=None, debug=False):
    def add_token(t, m=None):
        nonlocal pos, s
        if t is not None:
            debug and print(f'{start_pos + pos:2d}: {t}')
            tokens.append(t)
            pos_list.append(start_pos + pos)
        if m is not None:
            pos += m.span()[1]
            s = s[m.span()[1]:]

    if mem is None: raise ParseError('No memory provided to parser!')
    
    # check for commands
    if m := re.match(r'\s*help\s*', s): print("Help is on the way!"); return None
    if m := re.match(r'\s*vars\s*', s):
        print("\nUser-defined Variables")
        print("======================")
        for k in mem._vars:
            print(f'{k} = {mem._vars[k].value}')
        print()
        return None

    expr = Expression(brackets=brackets, mem=mem)
    tokens, pos_list = expr.tokens, expr.token_pos
    expr.start_pos = start_pos
    expr.input_string = s
    pos = 0

    while s:
        if s[0] in '([{': # bracketed expression
            tokens.append(parse(s[1:], start_pos=start_pos+pos+1, brackets={'(': '()', '[': '[]', '{': '{}'}[s[0]], mem=mem, debug=debug))
            # if len(tokens[-1].tokens) == 0: raise ParseError(f'Empty brackets at pos {pos}')
            pos_list.append(pos)
            pos += len(tokens[-1].input_string) + 2
            s = s[len(tokens[-1].input_string) + 2:]
        elif s[0] in ')]}': # end of bracketed expression
            if brackets and s[0] in brackets:
                expr.input_string = expr.input_string[:pos]
                break
            else:
                raise ParseError(f'Unmatched right delimiter "{s[0]}" at pos {start_pos + pos}')
        elif m := re.match(r'\d+(?:\.\d*)?|\.\d+', s):   # Number. Cannot follow Number, space_separator, or Var
            add_token(RealNumber(m.group()), m)
        else:  # symbolic operator
            found_token = False
            for regex in (dict := Op.regex):
                if m := re.match(regex, s):
                    this_token = dict[regex]
                    # add the token
                    add_token(this_token, m)
                    found_token = True
                    break
            if found_token: continue            
            # Unable to parse token
            if m := re.match(r'[A-Za-z](?:\w*(?:\d(?!(?:[0-9.]))|[A-Za-z_](?![A-Za-z])))?', s):  # Word token (might be a concatenation of vars & possible func at the end)
                # if tokens[-1] is not None and tokens[-1] is not Op.assignment: raise ParseError(f'Cannot assign to invalid l-value (pos {start_pos + pos}). Did you mean "==" instead?')
                add_token(WordToken(m.group(), user_mem=mem), m)
            else:
                raise ParseError(f'Unrecognized symbol "{s[0]}" at pos {start_pos + pos}')

    # if brackets and s == '': raise BracketMismatchError(f'Unpaired left delimiter "{brackets[0]}" at pos {start_pos}')
    if not brackets and not tokens: return None

    expr.tokens, expr.token_pos = validate(tokens, pos_list, brackets=brackets)

    match tokens[:3]:
        case [WordToken(), Expression(), Op.assignment]:  # function to be assigned
            pass
    
    return expr


def validate(tokens, pos_list, brackets=''):
    # Validation checks
    i = 1
    lst, pos_lst = [None] + tokens + [None], [None] + pos_list + [None]
    while i < len(lst) - 1:
        # Transform / remove some types of tokens
        match lst[i-1:i+2]:
            # Remove space separators that come at the start or end
            case [_any_, Op.space_separator, None] | [None, Op.space_separator, _any_]:
                lst[i:i+1] = []; pos_lst[i:i+1] = []; i -= 2
            # Bin cannot follow Bin / UL / None
            case [Infix() | Prefix() | None, Infix(), _any_]: raise ParseError(f"Invalid operand for {str(lst[i])} (pos {pos_lst[i]})")
            # Bin cannot precede Bin / UR / None
            case [_any_, Infix(), Infix() | Postfix() | None]: raise ParseError(f"Invalid operand for {str(lst[i])} (pos {pos_lst[i]})")
            # L to R: Convert +/- to positive/negative if they come after Bin / UL
            case [None | Infix() | Prefix(), Op.ambiguous_plus | Op.ambiguous_minus, _any_]:
                lst[i] = Op.positive if lst[i] == Op.ambiguous_plus else Op.negative
                i -= 2
            # L to R: If not, convert +/- to addition/subtraction
            case [_other_types_, Op.ambiguous_plus | Op.ambiguous_minus, _also_other_types_]:
                lst[i] = Op.addition if lst[i] == Op.ambiguous_plus else Op.subtraction
                i -= 2
            # Numbers cannot follow space separators or evaluables
            case [_any_, Value() | Op.space_separator, RealNumber()]: raise ParseError(f'Number {str(lst[i+1])} cannot follow space separator or an evaluable expression (pos {pos_lst[i+1]})')
            # UR has to follow an evaluable
            case [_operand_, Postfix(), _any_] if not isinstance(_operand_, (Value, WordToken)): raise ParseError(f"Invalid operand for {str(lst[i])} (pos {pos_lst[i]})")
            # UL cannot precede Bin or UR
            case [_any_, Prefix(), Infix() | Postfix()]: raise ParseError(f"Invalid operand for {str(lst[i])} (pos {pos_lst[i]})")
            case _: pass
        i += 1
    return lst[1:-1], pos_lst[1:-1]

if __name__ == '__main__':
    from memory import Memory
    mem = Memory()
    exp1 = parse('25 - cos +3pi + (5 sqrt(4)) - 4abc + sqr', debug=True, mem=mem)
    print(str(exp1))
    parse('5P2 + (5)', mem=mem)
    parse('10C3', mem=mem)
    parse('cos(32x+0.5) + sin(6pi/3) - f(3,4) + g', mem=mem)
    exp2 = parse('--5--4++-+3-90', debug=True, mem=mem)
    print(str(exp2))
    parse('k f(5)', mem=mem) # k*f(5)
    parse('300ab^2 c', mem=mem) # 300a*b^2*c
    exp3 = parse('300ab^2c', mem=mem) # 300a*b^(2*c)
    print(str(exp3))
    parse('1/2 x', mem=mem) # 1/2*x
    parse('2/3x', mem=mem) # 2/(3*x)
    exp7 = parse('7!/5!3!', mem=mem) # 7!/(5!*3!)
    print(str(exp7))
    parse('2.3pi', mem=mem, debug=True)
    parse('k', mem=mem)
    parse('25 - cos +3pi + (5 sqrt(4)) - 4abc + sqr', mem=mem)
    exp4 = parse('   2^k  x + 3^abc + 2/3 x -   3x/5', mem=mem)
    print(str(exp4))
    exp5 = parse('2[3 + 4{5 + 6(7/4)}]', mem=mem)
    print(str(exp5))
    exp6 = parse('a = bc = def = 73', mem=mem)
    print(str(exp6))
    exp8 = parse('5!', debug=True, mem=mem)
    exp9 = parse('fracpix2(3ab^2-4sqrsqrt5)', mem=mem)
    exp10 = parse('f(g) = 35x + 2y', mem=mem)
    exp11 = parse('fracpix2 = 35x + 2y', mem=mem)
    exp12 = parse('testfunc(x, y) = x + 5y - 23 cos h', debug=True, mem=mem)
    exp13 = parse('ab = fracsin3.2(b=3)/b - 23 cos h', debug=True, mem=mem)
    exp14 = parse('(b=2) + sinb23(x+5) cos h', debug=True, mem=mem)
    # (b=2) + <WT>(exp)<cos><WT>
    exp14 = parse('a + (b=2)^fracsin 2b', debug=True, mem=mem)
    # (b=2) + <WT>(exp)<cos><WT>
    # print(str(exp8))
    # print(exp11.value)
    # result = exp8.value
    # result2 = exp7.value
    pass