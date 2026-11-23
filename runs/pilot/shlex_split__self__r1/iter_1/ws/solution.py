def solve(s, comments=False, posix=True):
    ws = ' \t\r\n'
    commenters = '#' if comments else ''
    quotes = '\'"'
    esc = '\\'
    escq = '"'
    n = len(s)
    i = 0
    out = []

    def skipline(i):
        j = s.find('\n', i)
        return n if j < 0 else j + 1

    while True:
        state = ' '
        token = ''
        quoted = False
        escapedstate = ' '
        while True:
            if i < n:
                c = s[i]
                i += 1
            else:
                c = ''
            if state == ' ':
                if not c:
                    state = None
                    break
                elif c in ws:
                    if token or (posix and quoted):
                        break
                    continue
                elif c in commenters:
                    i = skipline(i)
                elif posix and c in esc:
                    escapedstate = 'a'
                    state = c
                elif c in quotes:
                    if not posix:
                        token = c
                    state = c
                else:
                    token = c
                    state = 'a'
            elif state in quotes:
                quoted = True
                if not c:
                    raise ValueError("No closing quotation")
                if c == state:
                    if not posix:
                        token += c
                        state = ' '
                        break
                    state = 'a'
                elif posix and c in esc and state in escq:
                    escapedstate = state
                    state = c
                else:
                    token += c
            elif state in esc:
                if not c:
                    raise ValueError("No escaped character")
                if escapedstate in quotes and c != state and c != escapedstate:
                    token += state
                token += c
                state = escapedstate
            else:  # 'a'
                if not c:
                    state = None
                    break
                elif c in ws:
                    state = ' '
                    if token or (posix and quoted):
                        break
                    continue
                elif c in commenters:
                    i = skipline(i)
                    if posix:
                        state = ' '
                        if token or (posix and quoted):
                            break
                elif posix and c in quotes:
                    state = c
                elif posix and c in esc:
                    escapedstate = 'a'
                    state = c
                else:
                    token += c
        if token == '' and not (posix and quoted):
            return out
        out.append(token)
