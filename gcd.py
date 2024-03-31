def gcd(*nums):
    lst = list(set(nums))
    while len(lst) > 1:
        smallest = min(lst)
        lst = [m for x in lst if (m := x % smallest) > 0] + [smallest]
    return lst[0]

assert gcd(8, 12) == 4
assert gcd(15, 25) == 5
assert gcd(18, 24) == 6

# Edge cases
assert gcd(17, 23) == 1
assert gcd(20, 30) == 10

# Large numbers
assert gcd(123456789, 987654321) == 9
assert gcd(100, 100) == 100

assert gcd(6, 9, 12) == 3  # GCD of multiple numbers
assert gcd(24, 36, 48) == 12  # GCD of multiple numbers
assert gcd(7, 14, 21, 28) == 7  # GCD of multiple numbers
assert gcd(60, 75, 90, 105, 120) == 15  # GCD of multiple numbers