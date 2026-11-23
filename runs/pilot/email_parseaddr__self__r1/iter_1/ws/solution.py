SPACE = ' '
EMPTYSTRING = ''


def quote(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


class AddrlistClass:
    def __init__(self, field):
        self.specials = '()<>@,:;.\"[]'
        self.pos = 0
        self.LWS = ' \t'
        self.CR = '\r\n'
        self.FWS = self.LWS + self.CR
        self.atomends = self.specials + self.LWS + self.CR
        self.phraseends = self.atomends.replace('.', '')
        self.field = field
        self.commentlist = []

    def gotonext(self):
        wslist = []
        while self.pos < len(self.field):
            if self.field[self.pos] in self.LWS + '\n\r':
                if self.field[self.pos] not in '\n\r':
                    wslist.append(self.field[self.pos])
                self.pos += 1
            elif self.field[self.pos] == '(':
                self.commentlist.append(self.getcomment())
            else:
                break
        return EMPTYSTRING.join(wslist)

    def getaddrlist(self):
        result = []
        while self.pos < len(self.field):
            ad = self.getaddress()
            if ad:
                result += ad
            else:
                result.append(('', ''))
        return result

    def getaddress(self):
        self.commentlist = []
        self.gotonext()

        oldpos = self.pos
        oldcl = self.commentlist
        plist = self.getphraselist()

        self.gotonext()
        returnlist = []

        if self.pos >= len(self.field):
            if plist:
                returnlist = [(SPACE.join(self.commentlist), plist[0])]

        elif self.field[self.pos] in '.@':
            self.pos = oldpos
            self.commentlist = oldcl
            addrspec = self.getaddrspec()
            returnlist = [(SPACE.join(self.commentlist), addrspec)]

        elif self.field[self.pos] == ':':
            returnlist = []
            fieldlen = len(self.field)
            self.pos += 1
            while self.pos < len(self.field):
                self.gotonext()
                if self.pos < fieldlen and self.field[self.pos] == ';':
                    self.pos += 1
                    break
                returnlist = returnlist + self.getaddress()

        elif self.field[self.pos] == '<':
            routeaddr = self.getrouteaddr()

            if self.commentlist:
                returnlist = [(SPACE.join(plist) + ' (' +
                               ' '.join(self.commentlist) + ')', routeaddr)]
            else:
                returnlist = [(SPACE.join(plist), routeaddr)]

        else:
            if plist:
                returnlist = [(SPACE.join(self.commentlist), plist[0])]
            elif self.field[self.pos] in self.specials:
                self.pos += 1

        self.gotonext()
        if self.pos < len(self.field) and self.field[self.pos] == ',':
            self.pos += 1
        return returnlist

    def getrouteaddr(self):
        if self.field[self.pos] != '<':
            return

        expectroute = False
        self.pos += 1
        self.gotonext()
        adlist = ''
        while self.pos < len(self.field):
            if expectroute:
                self.getdomain()
                expectroute = False
            elif self.field[self.pos] == '>':
                self.pos += 1
                break
            elif self.field[self.pos] == '@':
                self.pos += 1
                expectroute = True
            elif self.field[self.pos] == ':':
                self.pos += 1
            else:
                adlist = self.getaddrspec()
                self.pos += 1
                break
            self.gotonext()

        return adlist

    def getaddrspec(self):
        aslist = []

        self.gotonext()
        while self.pos < len(self.field):
            preserve_ws = True
            if self.field[self.pos] == '.':
                if aslist and not aslist[-1].strip():
                    aslist.pop()
                aslist.append('.')
                self.pos += 1
                preserve_ws = False
            elif self.field[self.pos] == '"':
                aslist.append('"%s"' % quote(self.getquote()))
            elif self.field[self.pos] in self.atomends:
                if aslist and not aslist[-1].strip():
                    aslist.pop()
                break
            else:
                aslist.append(self.getatom())
            ws = self.gotonext()
            if preserve_ws and ws:
                aslist.append(ws)

        if self.pos >= len(self.field) or self.field[self.pos] != '@':
            return EMPTYSTRING.join(aslist)

        aslist.append('@')
        self.pos += 1
        self.gotonext()
        domain = self.getdomain()
        if not domain:
            return EMPTYSTRING
        return EMPTYSTRING.join(aslist) + domain

    def getdomain(self):
        sdlist = []
        while self.pos < len(self.field):
            if self.field[self.pos] in self.LWS:
                self.pos += 1
            elif self.field[self.pos] == '(':
                self.commentlist.append(self.getcomment())
            elif self.field[self.pos] == '[':
                sdlist.append(self.getdomainliteral())
            elif self.field[self.pos] == '.':
                self.pos += 1
                sdlist.append('.')
            elif self.field[self.pos] == '@':
                return EMPTYSTRING
            elif self.field[self.pos] in self.atomends:
                break
            else:
                sdlist.append(self.getatom())
        return EMPTYSTRING.join(sdlist)

    def getdelimited(self, beginchar, endchars, allowcomments=True):
        if self.field[self.pos] != beginchar:
            return ''

        slist = ['']
        quote = False
        self.pos += 1
        while self.pos < len(self.field):
            if quote:
                slist.append(self.field[self.pos])
                quote = False
            elif self.field[self.pos] in endchars:
                self.pos += 1
                break
            elif allowcomments and self.field[self.pos] == '(':
                slist.append(self.getcomment())
                continue
            elif self.field[self.pos] == '\\':
                quote = True
            else:
                slist.append(self.field[self.pos])
            self.pos += 1

        return EMPTYSTRING.join(slist)

    def getquote(self):
        return self.getdelimited('"', '"', False)

    def getcomment(self):
        return self.getdelimited('(', ')', True)

    def getdomainliteral(self):
        return '[%s]' % self.getdelimited('[', ']', False)

    def getatom(self, atomends=None):
        atomlist = ['']
        if atomends is None:
            atomends = self.atomends

        while self.pos < len(self.field):
            if self.field[self.pos] in atomends:
                break
            else:
                atomlist.append(self.field[self.pos])
            self.pos += 1

        return EMPTYSTRING.join(atomlist)

    def getphraselist(self):
        plist = []

        while self.pos < len(self.field):
            if self.field[self.pos] in self.FWS:
                self.pos += 1
            elif self.field[self.pos] == '"':
                plist.append(self.getquote())
            elif self.field[self.pos] == '(':
                self.commentlist.append(self.getcomment())
            elif self.field[self.pos] in self.phraseends:
                break
            else:
                plist.append(self.getatom(self.phraseends))

        return plist


def _addresslist(field):
    return AddrlistClass(field).getaddrlist()


def solve(addr, *, strict=True):
    if not strict:
        addrs = _addresslist(addr)
        if not addrs:
            return ('', '')
        return addrs[0]

    if isinstance(addr, list):
        addr = addr[0]
    if not isinstance(addr, str):
        return ('', '')

    s = addr.replace('\\(', '').replace('\\)', '')
    if s.count('(') != s.count(')'):
        addr = "('', '')"
    addrs = [('', '') if '[' in v[1] else v for v in _addresslist(addr)]
    if not addrs or len(addrs) > 1:
        return ('', '')
    return addrs[0]
