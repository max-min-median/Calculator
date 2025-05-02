# __MaxCalc__
This calculator started as an idea for a project for [REDACTED: name of a particular online course] which I felt would be difficult enough to test my own limits as well as be an actual functional tool that I would use for my day job (math tutor).
- Intended to perform quick algebraic calculations.
- Main feature: Flexible and 'loose' parsing of algebraic expressions, much like how one would write them out.

## Installation
1. Clone the repository.
2. Run calculator.py
```
python calculator.py
```
-----------

## Commands
| Command | Description |
| ------- | ----------- |
| `help`  | shows this page |
| `vars`  | displays user-defined variables |
| `del [v1] [v2] ...` | deletes one or more user-defined variables |
| `prec N` | set working precision to `10^(-N)`, i.e. `N` decimal places |
| `disp N` | set final display precision to `N` decimal places |
| `frac N` | set length limit for fractions to be displayed |
| `debug [on/off]` | debug mode shows calculation steps |
| `sto[re] \| = \| -> <varName>` | store previous calculation into 'varName' |

| Hotkeys | Description |
| ------- | ----------- |
| `Shift + <Arrow>` | Text selection |
| `Ctrl + <Arrow>` | Jumps forward/backward by one word |
| `Ctrl + X / C / V` | Cut / Copy / Paste |
| `Ctrl + A` | Select all |
| `Ctrl + Bkspc` | Delete word at cursor |

-----------
## Things to try
| Input | Notes |
| ---------- | ----- |
| `2{3-4[5+65(3!` | Multiple bracket types are supported, and brackets are auto-closed |
| `x = 2; 2x + 1/x` | Semicolons separate expressions and evaluate to the rightmost expression |

- Whitespace has an effect on precedence. Some examples:

| Input | Notes |
| ---------- | ----- |
| `a = 2/3x; b = 2/3 x` | `a` evaluates as `2/(3x)`, `b` evaluates as `(2x)/3` |
| `a = sin pi/2; b = sinpi/2` | `a` evaluates as `sin (pi/2)`, `b` evaluates as `(sin pi)/2` |
| `4x^3/5` | evaluates as `(4x^3)/5` |
| `a = 1/2/3/4; b = 1/2 / 3/4; c = 1 / 2/3 / 4` | Give these a try! |

- The previous calculation is automatically stored as `ans`:

| Input | Notes |
| ---------- | ----- |
| `ans` | shows previous calculation |
| `2ans` (repeatedly) | number keeps doubling |
| `ans % 2 && 3ans + 1 \|\| ans / 2` (repeatedly) | Collatz sequence starting with `ans` |

- You can store and use your own variables:

| Input | Notes |
| ---------- | ----- |
| `a = b = c = 9` | assignments can be chained |
| `(a = 3)a(b = 5)bb` | not sure why you would ever do this, but it's `1125` |
| `a^bc^d` | evaluates as `a^(b*(c^d))`, unless `bc` exists, in which case it would be `a^(bc^d)` |
| `pi = 3.14; r = 3` | `pi` and `e` are (re)defineable. Use `del` to reset |
| `pir^2` | evaluated as `pi∙r^2`, unless a variable `pir` also exists, in which case it would be `(pir)^2` |
| `a = b = c = ab = bc = ac = abc = 1; abc` | multiple possible parses will trigger a warning |

- You can define your own functions. Use `vars` to see some preset functions.

| Input | Notes |
| ---------- | ----- |
| `square(x) = x^2` | not very necessary, but you do you :) |
| `quad(a, b, c) = ((-b - sqrt(b^2 - 4ac))/2a, (-b + sqrt(b^2 - 4ac))/2a)` | quadratic solver |
| `hero(a, b, c) = sqrt((a + b + c)(a + b - c)(b + c - a)(c + a - b)/16)` | Hero's formula for area of triangles |
| `g(x) = x > 3 && x^2 \|\| x <= 3 && 2x` | domains can be declared using booleans and logical and/or |
| `h = gff` | composite functions are supported |
| `h = f^2g^3` | declares h(x) = ffggg(x) |
| `dot((x1, y1, z1), (x2, y2, z2)) = x1x2 + y1y2 + z1z2` | multiple parameters are supported |
| `cross((a, b, c), (d, e, f)) = (bf-ce, cd-af, ae-bd)` | tuples are supported, even as parameters |
| `sigma(f, l, u) = l <= u && f(l) + sigma(f, l+1, u) \|\| f(l)` | recursive functions are supported |
| `collatz(n) = n > 1 && 1 + (n % 2 && collatz(3n + 1) \|\| collatz(n/2))` | Collatz number-of-steps-to-reach-1 |
| `collatz(n) = n > 1 ? 1 + (n % 2 ? collatz(3n + 1) : collatz(n/2)) : 0` | Alternative of above, using ternaries |
| `(1 + i)(2 - 3i)` | Complex numbers are fully implemented |
| `a = 2e^(ipi/4); b = i^i^i; c = sin(i)` | Try some fun complex calculations |

-----------
## List of currently supported math operators/functions:

| Type | Operator |
| ---------- | ----- |
| Arithmetic | `+`, `-`, `*`, `/`, `%`, `^`, `sqrt` |
| Combinatoric | `P`, `C`, `!` |
| Trigonometric | `sin`, `cos`, `tan`, `sec`, `cosec\|csc`, `cot` |
| Inverse Trig | `a[rc]sin`, `a[rc]cos`, `a[rc]tan` |
| Hyperbolic | `sinh`, `cosh`, `tanh` |
| Logarithmic | `ln`, `lg` |
| Logical | `&&`, `\|\|` |
| Equality | `==`, `!=` |
| Relational | `<`, `<=`, `>`, `>=` |
| Ternary | `<expression> ? <trueVal> : <falseVal>` |
| Complex | `abs`, `arg`, `conj`, `Re`, `Im` |

