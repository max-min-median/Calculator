def display():
    print()
    print("This calculator was made to perform quick algebraic calculations. Its main feature is flexible and 'loose' parsing of algebraic expressions, much like how one would write them out.")
    print("Commands: 'var' : display variables")
    print("          'del <v1> <v2> ...' : delete variables")
    print("          'prec N' : set working precision to 10^(-N), i.e. N decimal places")
    print("          'disp N' : set final display precision to N decimal places")
    print("          'frac N' : set length limit for fractions to be displayed")
    print()
    print("Some features / things to try")
    print("─────────────────────────────")
    print("Multiple bracket types are supported, and brackets are auto-closed")
    print("∙> 2{3-4[5+65(3!")
    print()
    print("Semicolons separate expressions and evaluate to the rightmost expression")
    print("∙> x = 2; 2x + 1/x  [result: 9/2]")
    print()
    print("Whitespace has an effect on precedence. Some examples:")
    print("∙> a = 2/3x; b = 2/3 x         ['a' evaluates as 2/(3x), 'b' evaluates as (2x)/3]")
    print("∙> a = sin pi/2; b = sinpi/2   ['a' evaluates as sin (pi/2), 'b' evaluates as (sin pi)/2]")
    print("∙> 4x^3/5  [evaluates as (4x^3)/5]")
    print("∙> a = 1/2/3/4; b = 1/2 / 3/4; c = 1 / 2/3 / 4   [Give these a try!]")
    print()
    print("You can store and use your own variables:")
    print("∙> a = b = c = 9  [assignments can be chained]")
    print("∙> (a = 3)a(b = 5)bb  [not sure why you would ever do this, but it's 1125]")
    print("∙> a^bc^d  [evaluates as a^(b*(c^d)), unless there is a variable 'bc', in which case it would be a^(bc^d)]")
    print("∙> pi = 3.14; r = 3  [pi and e are (re)defineable. Use 'del' to reset]")
    print("∙> pir^2  [evaluated as pi∙r^2, unless a variable 'pir' also exists, in which case it would be (pir)^2]")
    print("∙> a = b = c = ab = bc = ac = abc = 1; abc  [multiple possible parses will trigger a warning]")
    print()
    print("You can define your own functions. Use 'var' to see some preset functions.")
    print("∙> square(x) = x^2")
    print("∙> quad(a, b, c) = ((-b - sqrt(b^2 - 4ac))/2a, (-b + sqrt(b^2 - 4ac))/2a)  [quadratic solver]")
    print("∙> hero(a, b, c) = sqrt((a + b + c)(a + b - c)(b + c - a)(c + a - b)/16)  [Hero's formula for area of triangles]")
    print("∙> abs(x) = (x > 0) && x || -x  [There's no inbuilt modulus due to it being difficult/ambiguous to parse")
    print("                                 Easy to make your own though! :D ]")
    print("∙> g(x) = x > 3 && x^2 || x <= 3 && 2x  [domains can be declared using booleans and logical and/or]")
    print("∙> h = gff  [composite functions are supported]")
    print("∙> h = f^2g^3  [declares h(x) = ffggg(x)]")
    print("∙> dot(x1, y1, z1, x2, y2, z2) = x1x2 + y1y2 + z1z2  [multiple parameters are supported]")
    print("∙> cross(a, b, c, d, e, f) = (bf-ce, cd-af, ae-bd)  [tuples are supported]")
    print("∙> sigma(f, l, u) = l <= u && f(l) + sigma(f, l+1, u) || f(l)  [recursive functions are supported]")
    print("∙> collatz(n) = (n > 1) && 1 + (n % 2 && collatz(3n + 1) || collatz(n/2))  [Collatz number-of-steps-to-reach-1]")
    print()
    print("List of currently supported math operators/functions:")
    print("─────────────────────────────────────────────────────")
    print("Arithmetic: -, +, *, /, %, ^, sqrt")
    print("Combinatorics: P, C, !")
    print("Trigonometric: sin, cos, tan, a[rc]sin, a[rc]cos, a[rc]tan")
    print("Logarithmic: ln, lg")
    print("Logical: &&, ||")
    print("Equality: ==, !=")
    print("Relational: <, <=, >, >=")