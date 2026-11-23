import re

_incomplete = re.compile('&[a-zA-Z#]')
_entityref = re.compile('&([a-zA-Z][-.a-zA-Z0-9]*)[^a-zA-Z0-9]')
_charref = re.compile('&#(?:[0-9]+|[xX][0-9a-fA-F]+)[^0-9a-fA-F]')
_starttagopen = re.compile('<[a-zA-Z]')
_commentclose = re.compile(r'--\s*>')
_tagfind = re.compile(r'([a-zA-Z][^\t\n\r\f />\x00]*)(?:\s|/(?!>))*')
_attrfind = re.compile(
    r'((?<=[\'"\s/])[^\s/>][^\s/=>]*)(\s*=+\s*'
    r'(\'[^\']*\'|"[^"]*"|(?![\'"])[^>\s]*))?(?:\s|/(?!>))*')
_locate = re.compile(r"""
  <[a-zA-Z][^\t\n\r\f />\x00]*
  (?:[\s/]*
    (?:(?<=['"\s/])[^\s/>][^\s/=>]*
      (?:\s*=+\s*
        (?:'[^']*'
          |"[^"]*"
          |(?!['"])[^>\s]*
         )
        \s*
       )?(?:\s|/(?!>))*
     )*
   )?
  \s*
""", re.VERBOSE)
_endtagfind = re.compile(r'</\s*([a-zA-Z][-.a-zA-Z0-9:_]*)\s*>')
_declname = re.compile(r'[a-zA-Z][-_.a-zA-Z0-9]*\s*')
_msclose = re.compile(r']\s*]\s*>')
_msmclose = re.compile(r']\s*>')
_normal = re.compile('[&<]')


class _P:
    def __init__(self):
        self.out = []
        self.raw = ''
        self.cdata = None
        self.interesting = _normal

    def feed(self, d):
        self.raw += d
        self.goahead(0)

    def close(self):
        self.goahead(1)

    def set_cdata(self, e):
        self.cdata = e
        self.interesting = re.compile(r'</%s' % e, re.I)

    def clear_cdata(self):
        self.cdata = None
        self.interesting = _normal

    def data(self, t):
        self.out.append(['data', t])

    def goahead(self, end):
        raw = self.raw
        i = 0
        n = len(raw)
        while i < n:
            m = self.interesting.search(raw, i)
            if m:
                j = m.start()
            else:
                if self.cdata:
                    break
                j = n
            if i < j:
                self.data(raw[i:j])
            i = j
            if i == n:
                break
            if raw.startswith('<', i):
                if _starttagopen.match(raw, i):
                    k = self.parse_starttag(i)
                elif raw.startswith('</', i):
                    k = self.parse_endtag(i)
                elif raw.startswith('<!--', i):
                    k = self.parse_comment(i)
                elif raw.startswith('<?', i):
                    k = self.parse_pi(i)
                elif raw.startswith('<!', i):
                    k = self.parse_html_decl(i)
                elif i + 1 < n:
                    self.data('<')
                    k = i + 1
                else:
                    break
                if k < 0:
                    if not end:
                        break
                    k = raw.find('>', i + 1)
                    if k < 0:
                        k = raw.find('<', i + 1)
                        if k < 0:
                            k = i + 1
                    else:
                        k += 1
                    self.data(raw[i:k])
                i = k
            elif raw.startswith('&#', i):
                m = _charref.match(raw, i)
                if m:
                    self.out.append(['charref', m.group()[2:-1]])
                    k = m.end()
                    if not raw.startswith(';', k - 1):
                        k -= 1
                    i = k
                    continue
                else:
                    if ';' in raw[i:]:
                        self.data(raw[i:i + 2])
                        i += 2
                    break
            elif raw.startswith('&', i):
                m = _entityref.match(raw, i)
                if m:
                    self.out.append(['entityref', m.group(1)])
                    k = m.end()
                    if not raw.startswith(';', k - 1):
                        k -= 1
                    i = k
                    continue
                m = _incomplete.match(raw, i)
                if m:
                    if end and m.group() == raw[i:]:
                        i += 1
                    break
                elif i + 1 < n:
                    self.data('&')
                    i += 1
                else:
                    break
            else:
                raise AssertionError('interesting.search() lied')
        if end and i < n and not self.cdata:
            self.data(raw[i:n])
            i = n
        self.raw = raw[i:]

    def parse_starttag(self, i):
        raw = self.raw
        endpos = self.check_whole(i)
        if endpos < 0:
            return endpos
        attrs = []
        m = _tagfind.match(raw, i + 1)
        k = m.end()
        tag = m.group(1).lower()
        while k < endpos:
            m = _attrfind.match(raw, k)
            if not m:
                break
            name, rest, val = m.group(1, 2, 3)
            if not rest:
                val = None
            elif val[:1] == "'" == val[-1:] or val[:1] == '"' == val[-1:]:
                val = val[1:-1]
            attrs.append([name.lower(), val])
            k = m.end()
        e = raw[k:endpos].strip()
        if e not in ('>', '/>'):
            self.data(raw[i:endpos])
            return endpos
        if e.endswith('/>'):
            self.out.append(['startendtag', tag, attrs])
        else:
            self.out.append(['starttag', tag, attrs])
            if tag in ('script', 'style'):
                self.set_cdata(tag)
        return endpos

    def check_whole(self, i):
        raw = self.raw
        m = _locate.match(raw, i)
        j = m.end()
        nxt = raw[j:j + 1]
        if nxt == '>':
            return j + 1
        if nxt == '/':
            if raw.startswith('/>', j):
                return j + 2
            if raw.startswith('/', j):
                return -1
            return j if j > i else i + 1
        if nxt == '':
            return -1
        if nxt in 'abcdefghijklmnopqrstuvwxyz=/ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            return -1
        return j if j > i else i + 1

    def parse_endtag(self, i):
        raw = self.raw
        m = raw.find('>', i + 1)
        if m < 0:
            return -1
        gtpos = m + 1
        match = _endtagfind.match(raw, i)
        if not match:
            if self.cdata is not None:
                self.data(raw[i:gtpos])
                return gtpos
            nm = _tagfind.match(raw, i + 2)
            if not nm:
                if raw[i:i + 3] == '</>':
                    return i + 3
                return self.parse_bogus(i)
            tag = nm.group(1).lower()
            gt = raw.find('>', nm.end())
            self.out.append(['endtag', tag])
            return gt + 1
        elem = match.group(1).lower()
        if self.cdata is not None and elem != self.cdata:
            self.data(raw[i:gtpos])
            return gtpos
        self.out.append(['endtag', elem])
        self.clear_cdata()
        return gtpos

    def parse_bogus(self, i):
        pos = self.raw.find('>', i + 2)
        if pos == -1:
            return -1
        self.out.append(['comment', self.raw[i + 2:pos]])
        return pos + 1

    def parse_comment(self, i):
        m = _commentclose.search(self.raw, i + 4)
        if not m:
            return -1
        self.out.append(['comment', self.raw[i + 4:m.start()]])
        return m.end()

    def parse_pi(self, i):
        j = self.raw.find('>', i + 2)
        if j < 0:
            return -1
        self.out.append(['pi', self.raw[i + 2:j]])
        return j + 1

    def parse_html_decl(self, i):
        raw = self.raw
        if raw[i:i + 3] == '<![':
            return self.parse_marked(i)
        if raw[i:i + 9].lower() == '<!doctype':
            gt = raw.find('>', i + 9)
            if gt == -1:
                return -1
            self.out.append(['decl', raw[i + 2:gt]])
            return gt + 1
        return self.parse_bogus(i)

    def parse_marked(self, i):
        raw = self.raw
        n = len(raw)
        s = i + 3
        if s == n:
            return -1
        m = _declname.match(raw, s)
        if not m:
            raise AssertionError('expected name token')
        if s + len(m.group()) == n:
            return -1
        name = m.group().strip().lower()
        if name in ('temp', 'cdata', 'ignore', 'include', 'rcdata'):
            mm = _msclose.search(raw, i + 3)
        elif name in ('if', 'else', 'endif'):
            mm = _msmclose.search(raw, i + 3)
        else:
            raise AssertionError('unknown status keyword')
        if not mm:
            return -1
        self.out.append(['unknown_decl', raw[i + 3:mm.start()]])
        return mm.end()


def solve(html: str) -> list:
    p = _P()
    p.feed(html)
    p.close()
    return p.out
