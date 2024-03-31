from Operators import *
from Vars import *
from Numbers import *

class Expression:
    def __init__(self, input_string='', debug=False):
        self.input_string = input_string
        self.lst = Expression.parse(input_string, start_pos=0, closing_bracket=False, debug=debug)[0]
        self.display_string = Expression.to_string(self.lst, self.input_string)

    @staticmethod
    def parse(s, start_pos=0, closing_bracket=False, debug=False):
        import re
        pos = start_pos
        tokens = []
        prev_token = None
        while s:
            if s[0] in '([{':
                bracketed_expression, new_pos, s = Expression.parse(s[1:], pos + 1, ')]}'['([{'.index(s[0])], debug)
                tokens.append((prev_token := bracketed_expression, pos))
                pos = new_pos
            elif s[0] in ')]}':
                if s[0] == closing_bracket:
                    closing_bracket = False
                    pos += 1
                    s = s[1:]
                    break
                else:
                    raise BracketMismatchError(f'Unmatched right delimiter "{s[0]}" at pos {pos}')
            elif m := re.match(r'\d+(?:\.\d*)?|\.\d+', s):   # Number. Cannot follow Number, space_separator or list
                if isinstance(prev_token, (Number, list)) or prev_token == space_separator: raise ParseError(f'Number {m.group()} cannot follow space separator, bracketed expression, or another Number (pos {pos})')
                debug and print(f'Number: {m.group()}', pos)
                tokens.append((prev_token := Number(m.group()), pos))
                pos += m.span()[1]
                s = s[m.span()[1]:]
            else:
                for regex in (dict := {**op_regexes, **var_regexes}):
                    if m := re.match(regex, s):
                        this_token = dict[regex]
                        # Validation checks
                        if this_token in [ambiguous_plus, ambiguous_minus]:
                            if isinstance(prev_token, Operator) or prev_token is None: this_token = {ambiguous_plus: positive, ambiguous_minus: negative}[this_token]
                            else: this_token = {ambiguous_plus: addition, ambiguous_minus: subtraction}[this_token]
                        elif this_token == space_separator and (not tokens or s.lstrip() == '' or s.lstrip()[0] == closing_bracket):  # if space separator is first or last item in expression, ignore it.
                            this_token = None
                        elif isinstance(this_token, Unary_Right_Operator) and not isinstance(prev_token, (Number, list)):
                            raise ParseError(f'Right-unary operator {this_token.name} must follow a Number or bracketed expression (pos {pos})')
                        elif isinstance(this_token, Binary_Operator) and isinstance(prev_token, (Binary_Operator, Unary_Left_Operator)):
                            raise ParseError(f'Binary operator {this_token.name} cannot follow a binary or left-unary operator (pos {pos})') 
                        
                        if this_token is not None:
                            debug and print(f'"{m.group()}"', this_token, pos)
                            tokens.append((prev_token := this_token, pos))
                        pos += m.span()[1]
                        s = s[m.span()[1]:]
                        break
                else:  # should be alphabetic at this point
                    if s[0].isalpha():
                        while s and s[0].isalpha():
                            debug and print(f'Letter: "{s[0]}" at pos {pos}')
                            tokens.append((s[0], pos))
                            s = s[1:]
                            pos += 1
                            prev_token = 'letter'
                    else:
                        raise ParseError(f'Unrecognized symbol "{s[0]}" at pos {pos}')
        if closing_bracket: raise BracketMismatchError(f'Unpaired left bracket at pos {start_pos - 1}')
        if len(tokens) == 0: raise ParseError(f'Empty brackets at pos {start_pos - 1}')
        return tokens, pos, s
    
    def evaluate(self, bracket=False):
        """
        Order of Operations
        -------------------
        Parentheses
        functions
        implicit mult and power: R to L
        unaries R to L
        binaries L to R - multiple layers of Order of Operations
        """
        def eval(lst):  # returns a Number or ParamList (not implemented)
            lst = lst[:]  # copy the list
            for i, (token, _) in enumerate(lst):
                if isinstance(token, list): lst[i] = eval(token)
            for i, (token, _) in lst:
                if isinstance(token, Unary_Right_Operator):
                    lst[i-1:i+1] = token
            

        return eval(self.lstcopy)

    @property
    def lstcopy(self):
        return self.lst[:]

    def __str__(self):
        if not self.display_string: self.display_string = Expression.to_string(self.lst, self.input_string)
        return self.display_string
    
    @staticmethod
    def to_string(lst, input_string):
        s = ''
        for token in lst:
            if isinstance(token[0], list):
                left_bracket, right_bracket = input_string[token[1]], ')]}'['([{'.index(input_string[token[1]])]
                s += left_bracket + Expression.to_string(token[0], input_string) + right_bracket
            else:
                s += str(token[0])
        return s


# testing
# test = []
exp1 = Expression('e +  sin  (  34 )   - 5 +  sqrt   (2) ', debug = True)
Expression('e +  sin  (  34 )   - 5 +  sqrt(2) + sqr ')
Expression('25 - cos +3pi + (5 sqrt(4)) - 4abc + sqr')
Expression('5P2')
Expression('10C3')
Expression('cos(32x+0.5) + sin(6pi/3) - f(3,4) + g')
Expression('--5--4++-+3-90', debug = True)
Expression('k f(5)') # k*f(5)
Expression('300ab^2 c') # 300a*b^2*c
Expression('300ab^2c') # 300a*b^(2*c)
Expression('1/2 x') # 1/2*x
Expression('2/3x') # 2/(3*x)
Expression('7!/5!3!', debug = True) # 7!/(5!*3!)
Expression('2.3')
Expression('k')
Expression('25 - cos +3pi + (5 sqrt(4)) - 4abc + sqr')
exp2 = Expression('   2^k  x + 3^abc + 2/3 x -   3x/5', debug = True)
pass

# result = [Expression.parse(t, debug = True)[0] for t in test]
pass