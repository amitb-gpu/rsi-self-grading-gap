import re


def _translate(pat):
    res = []
    i, n = 0, len(pat)
    while i < n:
        c = pat[i]
        i += 1
        if c == '*':
            if not res or res[-1] != '.*':
                res.append('.*')
        elif c == '?':
            res.append('.')
        elif c == '[':
            j = i
            if j < n and pat[j] == '!':
                j += 1
            if j < n and pat[j] == ']':
                j += 1
            while j < n and pat[j] != ']':
                j += 1
            if j >= n:
                res.append('\\[')
            else:
                stuff = pat[i:j]
                if '-' not in stuff:
                    stuff = stuff.replace('\\', r'\\')
                else:
                    chunks = []
                    k = i + 2 if pat[i] == '!' else i + 1
                    while True:
                        k = pat.find('-', k, j)
                        if k < 0:
                            break
                        chunks.append(pat[i:k])
                        i = k + 1
                        k = k + 3
                    chunk = pat[i:j]
                    if chunk:
                        chunks.append(chunk)
                    else:
                        chunks[-1] += '-'
                    for k in range(len(chunks) - 1, 0, -1):
                        if chunks[k - 1][-1] > chunks[k][0]:
                            chunks[k - 1] = chunks[k - 1][:-1] + chunks[k][1:]
                            del chunks[k]
                    stuff = '-'.join(s.replace('\\', r'\\').replace('-', r'\-')
                                     for s in chunks)
                stuff = re.sub(r'([&~|])', r'\\\1', stuff)
                i = j + 1
                if not stuff:
                    res.append('(?!)')
                elif stuff == '!':
                    res.append('.')
                else:
                    if stuff[0] == '!':
                        stuff = '^' + stuff[1:]
                    elif stuff[0] in ('^', '['):
                        stuff = '\\' + stuff
                    res.append('[%s]' % stuff)
        else:
            res.append(re.escape(c))
    return '(?s:%s)\\Z' % ''.join(res)


def solve(names, pat):
    match = re.compile(_translate(pat)).match
    return [n for n in names if match(n)]
