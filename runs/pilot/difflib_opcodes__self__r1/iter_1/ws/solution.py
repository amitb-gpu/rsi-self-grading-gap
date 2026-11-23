def solve(a, b, autojunk=True):
    la, lb = len(a), len(b)
    b2j = {}
    for i, elt in enumerate(b):
        b2j.setdefault(elt, []).append(i)
    if autojunk and lb >= 200:
        ntest = lb // 100 + 1
        for elt in [e for e, idx in b2j.items() if len(idx) > ntest]:
            del b2j[elt]

    def flm(alo, ahi, blo, bhi):
        besti, bestj, bestsize = alo, blo, 0
        j2len = {}
        for i in range(alo, ahi):
            new = {}
            for j in b2j.get(a[i], ()):
                if j < blo:
                    continue
                if j >= bhi:
                    break
                k = new[j] = j2len.get(j - 1, 0) + 1
                if k > bestsize:
                    besti, bestj, bestsize = i - k + 1, j - k + 1, k
            j2len = new
        while besti > alo and bestj > blo and a[besti - 1] == b[bestj - 1]:
            besti -= 1
            bestj -= 1
            bestsize += 1
        while (besti + bestsize < ahi and bestj + bestsize < bhi
               and a[besti + bestsize] == b[bestj + bestsize]):
            bestsize += 1
        return besti, bestj, bestsize

    queue = [(0, la, 0, lb)]
    blocks = []
    while queue:
        alo, ahi, blo, bhi = queue.pop()
        i, j, k = flm(alo, ahi, blo, bhi)
        if k:
            blocks.append((i, j, k))
            if alo < i and blo < j:
                queue.append((alo, i, blo, j))
            if i + k < ahi and j + k < bhi:
                queue.append((i + k, ahi, j + k, bhi))
    blocks.sort()
    merged = []
    i1 = j1 = k1 = 0
    for i2, j2, k2 in blocks:
        if i1 + k1 == i2 and j1 + k1 == j2:
            k1 += k2
        else:
            if k1:
                merged.append((i1, j1, k1))
            i1, j1, k1 = i2, j2, k2
    if k1:
        merged.append((i1, j1, k1))
    merged.append((la, lb, 0))

    ops = []
    i = j = 0
    for ai, bj, size in merged:
        tag = ''
        if i < ai and j < bj:
            tag = 'replace'
        elif i < ai:
            tag = 'delete'
        elif j < bj:
            tag = 'insert'
        if tag:
            ops.append((tag, i, ai, j, bj))
        i, j = ai + size, bj + size
        if size:
            ops.append(('equal', ai, i, bj, j))
    return ops
