import random, json
from solution import solve
random.seed(1)
cases = []


def add(a, b, au=True):
    cases.append({"args": [a, b], "kwargs": {"autojunk": au},
                  "expected": [list(t) for t in solve(a, b, au)]})


# hand-derived
cases.append({"args": ["abcd", "bcde"], "kwargs": {}, "expected": [["delete", 0, 1, 0, 0], ["equal", 1, 4, 0, 3], ["insert", 4, 4, 3, 4]]})
cases.append({"args": ["", ""], "kwargs": {}, "expected": []})
cases.append({"args": ["qabxcd", "abycdf"], "kwargs": {}, "expected": [["delete", 0, 1, 0, 0], ["equal", 1, 3, 0, 2], ["replace", 3, 4, 2, 3], ["equal", 4, 6, 3, 5], ["insert", 6, 6, 5, 6]]})


def mut(s, n, al):
    s = list(s)
    for _ in range(n):
        r = random.choice("ids")
        p = random.randrange(len(s) + 1)
        if r == "i":
            s.insert(p, random.choice(al))
        elif s and p < len(s):
            if r == "d":
                del s[p]
            else:
                s[p] = random.choice(al)
    return "".join(s)


for _ in range(14):
    a = "".join(random.choice("abcde ") for _ in range(random.randint(0, 25)))
    add(a, mut(a, random.randint(0, 5), "abcde "), random.random() > .3)
for _ in range(8):
    a = ["    x = %d" % random.randint(0, 4) if random.random() < .5 else "def f%d():" % random.randint(0, 3) for _ in range(random.randint(0, 12))]
    b = list(a)
    for _ in range(2):
        if b:
            b[random.randrange(len(b))] = "return %d" % random.randint(0, 9)
    add(a, b, random.random() > .3)
for _ in range(10):
    a = "".join(random.choice("ab c") for _ in range(random.randint(20, 80)))
    b = "".join(random.choice("aab c") for _ in range(random.randint(200, 260)))
    add(a, b, random.random() > .4)
json.dump(cases, open("self_cases.json", "w"))
