import json
R = {"raises": "ValueError"}
cases = [
    (["appel", ["ape", "apple", "peach", "puppy"]], {}, ["apple", "ape"]),
    (["wheel", ["ape", "apple", "peach", "puppy"]], {}, []),
    (["apple", ["apple", "apply", "ape", "maple"]], {"n": 1}, ["apple"]),
    (["apple", ["apply", "ape", "maple"]], {"n": 2}, ["maple", "apply"]),
    (["banana", ["bandana", "banana", "bananas", ""]], {}, ["banana", "bandana", "bananas"]),
    (["", [""]], {}, [""]),
    (["", ["a"]], {"cutoff": 0.0}, ["a"]),
    (["a", ["a", "aaaa"]], {"cutoff": 0.9}, ["a"]),
    (["apple", ["ape"]], {"n": 0}, R),
    (["apple", ["ape"]], {"cutoff": 1.5}, R),
    (["apple", ["ape"]], {"cutoff": -0.1}, R),
    (["apple", []], {}, []),
    (["apple", ["apple"]], {"cutoff": 1.0}, ["apple"]),
    (["apple", ["apply"]], {"cutoff": 0.9}, []),
    (["apple", ["apply"]], {"cutoff": 0.75}, ["apply"]),
]
for w in ["apple", "banana", "maple", "ape", "aaaa", "a", "apply", "bandana"]:
    cases.append(([w, [w, "zzzz"]], {"n": 2}, [w]))
for w in ["apple", "banana", "maple", "ape", "aaaa", "a", "apply"]:
    cases.append(([w, []], {"cutoff": 0.0}, []))
json.dump([{"args": a, "kwargs": k, "expected": e} for a, k, e in cases],
          open("self_cases.json", "w"))
