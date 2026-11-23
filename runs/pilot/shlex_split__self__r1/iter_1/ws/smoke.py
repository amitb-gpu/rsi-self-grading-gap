from solution import solve as f
print(f('a "b c" d\\ e #x\nf', True), f('a"b"c \'\' x', False), f('a#b c', True, False), f('a"b"c \'\' x'))
for t in ['"a', 'a\\']:
    try:
        f(t)
    except ValueError as e:
        print(e)
