class Number:
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        return self.value * 10 + other.value * 10

print(Number(5) + 6)