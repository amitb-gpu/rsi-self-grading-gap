import re

_ws = '\t\n\x0b\x0c\r '
_wp = r'[\w!"\'&.,?]'
_lt = r'[^\d\W]'
_wsc = '[%s]' % re.escape(_ws)
_nws = '[^' + _wsc[1:]
_wordsep_re = re.compile(r'''
    ( %(ws)s+
    | (?<=%(wp)s) -{2,} (?=\w)
    | %(nws)s+? (?:
          -(?: (?<=%(lt)s{2}-) | (?<=%(lt)s-%(lt)s-))
          (?= %(lt)s -? %(lt)s)
        | (?=%(ws)s|\Z)
        | (?<=%(wp)s) (?=-{2,}\w)
        )
    )''' % {'wp': _wp, 'lt': _lt, 'ws': _wsc, 'nws': _nws}, re.VERBOSE)
_simple_re = re.compile(r'(%s+)' % _wsc)
_sent_re = re.compile(r'[a-z][\.\!\?][\"\']?\Z')
_trans = {ord(c): ord(' ') for c in _ws}


def solve(text, width=70, **kw):
    opts = dict(break_long_words=True, break_on_hyphens=True, drop_whitespace=True,
                expand_tabs=True, replace_whitespace=True, fix_sentence_endings=False,
                initial_indent='', subsequent_indent='', tabsize=8, max_lines=None,
                placeholder=' [...]')
    for k in kw:
        if k not in opts:
            raise TypeError(k)
    opts.update(kw)
    o = opts
    if o['expand_tabs']:
        text = text.expandtabs(o['tabsize'])
    if o['replace_whitespace']:
        text = text.translate(_trans)
    chunks = _wordsep_re.split(text) if o['break_on_hyphens'] else _simple_re.split(text)
    chunks = [c for c in chunks if c]
    if o['fix_sentence_endings']:
        i = 0
        while i < len(chunks) - 1:
            if chunks[i + 1] == " " and _sent_re.search(chunks[i]):
                chunks[i + 1] = "  "
                i += 2
            else:
                i += 1
    W = width
    if W <= 0:
        raise ValueError("invalid width %r (must be > 0)" % W)
    ml = o['max_lines']; ph = o['placeholder']
    init = o['initial_indent']; sub = o['subsequent_indent']
    if ml is not None:
        indent = sub if ml > 1 else init
        if len(indent) + len(ph.lstrip()) > W:
            raise ValueError("placeholder too large for max width")
    drop = o['drop_whitespace']
    lines = []
    chunks.reverse()
    while chunks:
        cur = []; cl = 0
        indent = sub if lines else init
        w = W - len(indent)
        if drop and chunks[-1].strip() == '' and lines:
            del chunks[-1]
        while chunks:
            l = len(chunks[-1])
            if cl + l <= w:
                cur.append(chunks.pop()); cl += l
            else:
                break
        if chunks and len(chunks[-1]) > w:
            sl = 1 if w < 1 else w - cl
            if o['break_long_words']:
                end = sl
                chunk = chunks[-1]
                if o['break_on_hyphens'] and len(chunk) > sl:
                    h = chunk.rfind('-', 0, sl)
                    if h > 0 and any(c != '-' for c in chunk[:h]):
                        end = h + 1
                cur.append(chunk[:end]); chunks[-1] = chunk[end:]
            elif not cur:
                cur.append(chunks.pop())
            cl = sum(map(len, cur))
        if drop and cur and cur[-1].strip() == '':
            cl -= len(cur[-1]); del cur[-1]
        if cur:
            if (ml is None or len(lines) + 1 < ml or
                    ((not chunks or drop and len(chunks) == 1 and not chunks[0].strip()) and cl <= w)):
                lines.append(indent + ''.join(cur))
            else:
                while cur:
                    if cur[-1].strip() and cl + len(ph) <= w:
                        cur.append(ph)
                        lines.append(indent + ''.join(cur))
                        break
                    cl -= len(cur[-1]); del cur[-1]
                else:
                    if lines:
                        prev = lines[-1].rstrip()
                        if len(prev) + len(ph) <= W:
                            lines[-1] = prev + ph
                            break
                    lines.append(indent + ph.lstrip())
                break
    return lines
