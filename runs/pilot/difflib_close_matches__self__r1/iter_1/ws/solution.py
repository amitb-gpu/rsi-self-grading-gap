import heapq


class _SM:
    def __init__(self):
        self.a = self.b = None

    def set_seq2(self, b):
        self.b = b
        self.b2j = d = {}
        for i, elt in enumerate(b):
            d.setdefault(elt, []).append(i)
        self.bpopular = popular = set()
        n = len(b)
        if n >= 200:
            ntest = n // 100 + 1
            for elt, idxs in list(d.items()):
                if len(idxs) > ntest:
                    popular.add(elt)
            for elt in popular:
                del d[elt]

    def find_longest_match(self, alo, ahi, blo, bhi):
        a, b, b2j = self.a, self.b, self.b2j
        besti, bestj, bestsize = alo, blo, 0
        j2len = {}
        for i in range(alo, ahi):
            j2lenget = j2len.get
            newj2len = {}
            for j in b2j.get(a[i], ()):
                if j < blo:
                    continue
                if j >= bhi:
                    break
                k = newj2len[j] = j2lenget(j - 1, 0) + 1
                if k > bestsize:
                    besti, bestj, bestsize = i - k + 1, j - k + 1, k
            j2len = newj2len
        # no junk: extension only matters for popular elements
        while besti > alo and bestj > blo and a[besti-1] == b[bestj-1]:
            besti, bestj, bestsize = besti-1, bestj-1, bestsize+1
        while (besti+bestsize < ahi and bestj+bestsize < bhi
               and a[besti+bestsize] == b[bestj+bestsize]):
            bestsize += 1
        return besti, bestj, bestsize

    def matching_blocks(self):
        la, lb = len(self.a), len(self.b)
        queue = [(0, la, 0, lb)]
        blocks = []
        while queue:
            alo, ahi, blo, bhi = queue.pop()
            i, j, k = self.find_longest_match(alo, ahi, blo, bhi)
            if k:
                blocks.append((i, j, k))
                if alo < i and blo < j:
                    queue.append((alo, i, blo, j))
                if i + k < ahi and j + k < bhi:
                    queue.append((i + k, ahi, j + k, bhi))
        return blocks

    def ratio(self):
        m = sum(t[2] for t in self.matching_blocks())
        length = len(self.a) + len(self.b)
        return 2.0 * m / length if length else 1.0

    def quick_ratio(self):
        fullbcount = {}
        for elt in self.b:
            fullbcount[elt] = fullbcount.get(elt, 0) + 1
        avail = {}
        matches = 0
        for elt in self.a:
            if elt in avail:
                numb = avail[elt]
            else:
                numb = fullbcount.get(elt, 0)
            avail[elt] = numb - 1
            if numb > 0:
                matches += 1
        length = len(self.a) + len(self.b)
        return 2.0 * matches / length if length else 1.0

    def real_quick_ratio(self):
        la, lb = len(self.a), len(self.b)
        length = la + lb
        return 2.0 * min(la, lb) / length if length else 1.0


def solve(word, possibilities, n=3, cutoff=0.6):
    if not n > 0:
        raise ValueError("n must be > 0: %r" % (n,))
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result = []
    s = _SM()
    s.set_seq2(word)
    for x in possibilities:
        s.a = x
        if s.real_quick_ratio() >= cutoff and s.quick_ratio() >= cutoff:
            r = s.ratio()
            if r >= cutoff:
                result.append((r, x))
    result = heapq.nlargest(n, result)
    return [x for score, x in result]
