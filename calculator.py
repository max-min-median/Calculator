from Expressions import *
from Vars import *
from Operators import *
from Errors import *

"""
Sample parsables:
=================
5P2, 10C3
cos(32x+0.5), sin(6pi/3), f(3,4), g
--5--4++-+3-7
k f(5) --> k*f(5)
300ab^2 c --> 300a*b^2*c
300ab^2c --> 300a*b^(2*c)
1/2 x --> 1/2*x
2/3x --> 2/(3*x)
7!/5!3! --> 7!/(5!*3!)
"""

def main():
    print("Calculator v0.1a by max_min_median")
    vars = {}
    tokens = []
    while True:
        try:
            inp = input("> ")
            a = Expression.parse(inp, debug = True)[0]
            print(a)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()