# __Calculator__
This calculator started as an idea for a final project for [CS50's Python course](https://cs50.harvard.edu/python/2022/) which I felt would be difficult enough to test my own limits as well as be an actual functional tool that I would use for my day job (math tutor).
As such, the main feature of this calculator is its flexible parsing of algebraic expressions that one would key in much like how one would write them out.

## How to use
Clone the repository and run the main file

`python Calculator.py`


print("Commands: 'var' to display variables. 'del <v1> <v2> ...' to delete variables.")
    print("Here are some things to try:")
    print("∙> 2{3-4[5+65(3!   (Multiple bracket types are supported, and brackets are auto-closed)")
    print("∙> x = 2; 2x + 1/x  [result: 9/2] (semicolons separate expressions and evaluate to the rightmost expression)")
    print("∙> a = 2/3x; b = 2/3 x  ('a' evaluates as 2/(3x), 'b' evaluates as 2x/3)")
    print("∙> a^bc^d  (evaluates as a^(b*(c^d))")
    print("∙> a = b = c = 9  (assignments can be chained)")
    print("∙> f(x) = x^2  (a simple square function)")
    print("∙> g(x) = x > 3 && x^2 || x <= 3 && 2x  (domains can be declared using booleans and logical and/or)")
    print("∙> h = gff  (composite functions are supported)")
    print("∙> h = f^2g^3  [declares h(x) = ffggg(x)]")
    print("∙> dot(x1, y1, z1, x2, y2, z2) = x1x2 + y1y2 + z1z2  (multiple parameters are supported)")
    print("∙> cross(a, b, c, d, e, f) = (bf-ce, cd-af, ae-bd)  (tuples are supported)")
    print("∙> g(x) = x > 3 && x^2 || x <= 3 && 2x  (domains can be declared using booleans and logical and/or)")
    print("∙> pi = 3.14; r = 3  (pi and e are (re)defineable. 'del' them to reset")
    print("∙> pir^2  (parser recognizes this as pi∙r^2, unless a variable 'pir' also exists)")
    print("∙> a = b = c = ab = bc = ac = abc = 1; abc  (multiple possible parses will trigger a warning)")
    print("∙> sigma(f, l, u) = l <= u && f(l) + sigma(f, l+1, u) || f(l)   (recursive functions are supported)")
    print()
