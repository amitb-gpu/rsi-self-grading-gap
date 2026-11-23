import re

_HEX = set('0123456789abcdefABCDEF')
_asciire = re.compile('([\x00-\x7f]+)')


def _to_bytes(s):
    if '%' not in s:
        return s.encode('latin-1')
    bits = s.split('%')
    res = [bits[0].encode('latin-1')]
    for item in bits[1:]:
        if len(item) >= 2 and item[0] in _HEX and item[1] in _HEX:
            res.append(bytes([int(item[:2], 16)]) + item[2:].encode('latin-1'))
        else:
            res.append(b'%' + item.encode('latin-1'))
    return b''.join(res)


def _unquote(s):
    if '%' not in s:
        return s
    bits = _asciire.split(s)
    out = [bits[0]]
    for i in range(1, len(bits), 2):
        out.append(_to_bytes(bits[i]).decode('utf-8', 'replace'))
        out.append(bits[i + 1])
    return ''.join(out)


def solve(qs, keep_blank_values=False, strict_parsing=False, separator='&'):
    if not separator or not isinstance(separator, str):
        raise ValueError("Separator must be of type string or bytes.")
    if not qs:
        return []
    r = []
    for nv_s in qs.split(separator):
        if not nv_s and not strict_parsing:
            continue
        nv = nv_s.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError("bad query field: %r" % (nv_s,))
            if keep_blank_values:
                nv.append('')
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            r.append((_unquote(nv[0].replace('+', ' ')), _unquote(nv[1].replace('+', ' '))))
    return r
