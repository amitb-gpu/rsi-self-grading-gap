_HEX = frozenset('0123456789abcdefABCDEF')


def _v4(s):
    parts = s.split('.')
    if len(parts) != 4:
        raise ValueError(s)
    n = 0
    for p in parts:
        if not (p.isascii() and p.isdigit()) or len(p) > 3:
            raise ValueError(s)
        if p != '0' and p[0] == '0':
            raise ValueError(s)
        v = int(p)
        if v > 255:
            raise ValueError(s)
        n = (n << 8) | v
    return n


def _v6(s):
    if '/' in s:
        raise ValueError(s)
    addr, sep, scope = s.partition('%')
    if sep and (not scope or '%' in scope):
        raise ValueError(s)
    if not addr:
        raise ValueError(s)
    parts = addr.split(':')
    if len(parts) < 3:
        raise ValueError(s)
    if '.' in parts[-1]:
        n = _v4(parts.pop())
        parts.append('%x' % ((n >> 16) & 0xFFFF))
        parts.append('%x' % (n & 0xFFFF))
    if len(parts) > 9:
        raise ValueError(s)
    skip = None
    for i in range(1, len(parts) - 1):
        if not parts[i]:
            if skip is not None:
                raise ValueError(s)
            skip = i
    if skip is not None:
        hi = skip
        lo = len(parts) - skip - 1
        if not parts[0]:
            hi -= 1
            if hi:
                raise ValueError(s)
        if not parts[-1]:
            lo -= 1
            if lo:
                raise ValueError(s)
        if 8 - (hi + lo) < 1:
            raise ValueError(s)
        sk = 8 - (hi + lo)
    else:
        if len(parts) != 8 or not parts[0] or not parts[-1]:
            raise ValueError(s)
        hi, lo, sk = len(parts), 0, 0
    sel = parts[:hi] + (parts[len(parts) - lo:] if lo else [])
    vals = []
    for h in sel:
        if not h or len(h) > 4 or not _HEX.issuperset(h):
            raise ValueError(s)
        vals.append(int(h, 16))
    full = vals[:hi] + [0] * sk + vals[hi:]
    best_s, best_l = -1, 0
    i = 0
    while i < 8:
        if full[i] == 0:
            j = i
            while j < 8 and full[j] == 0:
                j += 1
            if j - i > best_l:
                best_s, best_l = i, j - i
            i = j
        else:
            i += 1
    hx = ['%x' % v for v in full]
    if best_l > 1:
        out = ':'.join(hx[:best_s]) + '::' + ':'.join(hx[best_s + best_l:])
    else:
        out = ':'.join(hx)
    if sep:
        out += '%' + scope
    return out


def solve(address):
    try:
        n = _v4(address)
        return (4, '.'.join(str((n >> k) & 255) for k in (24, 16, 8, 0)))
    except ValueError:
        pass
    return (6, _v6(address))
