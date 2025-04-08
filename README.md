# __Calculator__
This calculator started as an idea for a project for [REDACTED: name of a particular online course] which I felt would be difficult enough to test my own limits as well as be an actual functional tool that I would use for my day job (math tutor).
As such, the main feature of this calculator is its flexible parsing of algebraic expressions that one would key in much like how one would write them out.

## Installation
1. Clone the repository.
2. Install requirements.
```
pip install -r requirements.txt
```
3. Run Calculator.py
```
python Calculator.py
```

## Commands
| Command | Description |
| ------- | ----------- |
| `help`  | a simple quickstart guide |
| `vars`  | displays a list of all user-defined variables |
| `del [v1] [v2] ...` | deletes one or more user-defined variables |

## Things to try
| Expression | Notes |
| ---------- | ----- |
| `2{3-4[5+65(3!` | Multiple bracket types are supported, and brackets are auto-closed |
| `x = 2; 2x + 1/x` | Semicolons separate expressions and evaluate to the rightmost expression |
| `a = 2/3x; b = 2/3 x` | `a` evaluates as `2/(3x)`, `b` evaluates as `2x/3` |
| `a^bc^d` | Evaluates as `a^(b*(c^d))` |
| `a = b = c = 9` | Assignments can be chained |
| `f(x) = x^2` | A simple square function |
| `g(x) = x > 3 && x^2 \|\| x <= 3 && 2x` | Domains can be declared using booleans and logical and/or |
| `h = gff` | Composite functions are supported; Functions are first-class |
| `h = f^2g^3` | Declares h(x) = ffggg(x) |
| `dot(x1, y1, z1, x2, y2, z2) = x1x2 + y1y2 + z1z2` | Multiple parameters are supported |
| `cross(a, b, c, d, e, f) = (bf-ce, cd-af, ae-bd)` | Tuples are supported |
| `g(x) = x > 3 && x^2 \|\| x <= 3 && 2x` | Domains can be declared sing booleans and logical AND/OR |
| `pi = 3.14; r = 3` | `pi` and `e` are (re)defineable. Use `del` to reset |
| `pir^2` | Parser recognizes this as `pi∙r^2`, unless a variable `pir` also exists |
| `a = b = c = ab = bc = ac = abc = 1; abc` | Multiple possible tokenizations will trigger a warning |
| `sigma(f, l, u) = l <= u && f(l) + sigma(f, l+1, u) \|\| f(l)` | Recursive functions are supported |
