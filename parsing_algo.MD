(Deprecated, here for historical purposes :))

Parsing Algorithm
─────────────────
At any arbitrary point in the evaluation, we do this:

1) Read token.

2) If WordToken, split it and continue at same index.

3) If Value,
    (A) If L is None, store Value into L and advance to next index (only happens at the start).
    (B) else if L exists, but there is no prevailing operator, set the prevailing operator to implicit_mult, and continue at the current index.
    (C) else if L and prev_infix_opr exist, peek at next token (expecting an operator).
        If next token is a Value, WordToken or prefix, next_opr is taken to be implicit_mult, else it is taken as is.
        1. If next operator has a higher power than prevailing, recurse with that same value as L.
        2. If next operator has a lower or equal power than prevailing, return the result with that value as R.
        3. If next operator has the same power as prevailing, perform the prevailing operation and store that into L.

4) If Operator:
    (A) If prefix (UL), recurse.
    (B) If postfix (UR), perform the operation on L and return it.
    (C) If infix,
        1. If L is None or if there is a prevailing operator, throw error.
        2. Otherwise, store it as the prevailing operator and continue.

5) If None, we have reached the end of the evaluation. Return L.