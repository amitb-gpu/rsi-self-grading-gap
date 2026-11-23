import re

_scalars = (str, bytes, bytearray, float, complex, bool, type(None))


class _Key:
    __slots__ = ("obj",)

    def __init__(self, obj):
        self.obj = obj

    def __lt__(self, other):
        try:
            return self.obj < other.obj
        except TypeError:
            return (str(type(self.obj)), id(self.obj)) < (str(type(other.obj)), id(other.obj))


def _safe_tuple(t):
    return _Key(t[0]), _Key(t[1])


class _P:
    def __init__(self, indent, width, depth, compact, sort_dicts, un):
        indent = int(indent)
        width = int(width)
        if indent < 0:
            raise ValueError('indent must be >= 0')
        if depth is not None and depth <= 0:
            raise ValueError('depth must be > 0')
        if not width:
            raise ValueError('width must be != 0')
        self.ipl = indent
        self.width = width
        self.depth = depth
        self.compact = bool(compact)
        self.sort_dicts = sort_dicts
        self.un = un
        self.out = []

    def items_of(self, o):
        if self.sort_dicts:
            return sorted(o.items(), key=_safe_tuple)
        return list(o.items())

    def safe_repr(self, o, context, maxlevels, level):
        typ = type(o)
        if typ in _scalars:
            return repr(o), True, False
        if isinstance(o, int) and typ.__repr__ is int.__repr__:
            if self.un:
                return f"{o:_d}", True, False
            return repr(o), True, False
        if isinstance(o, dict) and typ.__repr__ is dict.__repr__:
            if not o:
                return "{}", True, False
            oid = id(o)
            if maxlevels and level >= maxlevels:
                return "{...}", False, oid in context
            if oid in context:
                return "<Recursion on %s with id=%s>" % (typ.__name__, oid), False, True
            context[oid] = 1
            readable = True
            recursive = False
            comps = []
            level += 1
            for k, v in self.items_of(o):
                kr, kd, kc = self.safe_repr(k, context, maxlevels, level)
                vr, vd, vc = self.safe_repr(v, context, maxlevels, level)
                comps.append("%s: %s" % (kr, vr))
                readable = readable and kd and vd
                recursive = recursive or kc or vc
            del context[oid]
            return "{%s}" % ", ".join(comps), readable, recursive
        if isinstance(o, (list, tuple)) and typ.__repr__ in (list.__repr__, tuple.__repr__):
            if isinstance(o, list):
                if not o:
                    return "[]", True, False
                fmt = "[%s]"
            elif len(o) == 1:
                fmt = "(%s,)"
            else:
                if not o:
                    return "()", True, False
                fmt = "(%s)"
            oid = id(o)
            if maxlevels and level >= maxlevels:
                return fmt % "...", False, oid in context
            if oid in context:
                return "<Recursion on %s with id=%s>" % (typ.__name__, oid), False, True
            context[oid] = 1
            readable = True
            recursive = False
            comps = []
            level += 1
            for x in o:
                r, d, c = self.safe_repr(x, context, maxlevels, level)
                comps.append(r)
                readable = readable and d
                recursive = recursive or c
            del context[oid]
            return fmt % ", ".join(comps), readable, recursive
        rep = repr(o)
        return rep, bool(rep and not rep.startswith('<')), False

    def _repr(self, o, context, level):
        return self.safe_repr(o, context.copy(), self.depth, level)[0]

    def _format(self, o, indent, allowance, context, level):
        w = self.out.append
        oid = id(o)
        if oid in context:
            w("<Recursion on %s with id=%s>" % (type(o).__name__, oid))
            return
        rep = self._repr(o, context, level)
        max_width = self.width - indent - allowance
        if len(rep) > max_width:
            typ = type(o)
            p = None
            if isinstance(o, str) and typ.__repr__ is str.__repr__:
                p = self.p_str
            elif isinstance(o, dict) and typ.__repr__ is dict.__repr__:
                p = self.p_dict
            elif isinstance(o, list) and typ.__repr__ is list.__repr__:
                p = self.p_list
            elif isinstance(o, tuple) and typ.__repr__ is tuple.__repr__:
                p = self.p_tuple
            if p is not None:
                context[oid] = 1
                p(o, indent, allowance, context, level + 1)
                del context[oid]
                return
        w(rep)

    def p_dict(self, o, indent, allowance, context, level):
        w = self.out.append
        w('{')
        if self.ipl > 1:
            w((self.ipl - 1) * ' ')
        if len(o):
            self.fmt_dict_items(self.items_of(o), indent, allowance + 1, context, level)
        w('}')

    def fmt_dict_items(self, items, indent, allowance, context, level):
        w = self.out.append
        indent += self.ipl
        delimnl = ',\n' + ' ' * indent
        last_index = len(items) - 1
        for i, (key, ent) in enumerate(items):
            last = i == last_index
            rep = self._repr(key, context, level)
            w(rep)
            w(': ')
            self._format(ent, indent + len(rep) + 2, allowance if last else 1, context, level)
            if not last:
                w(delimnl)

    def p_list(self, o, indent, allowance, context, level):
        w = self.out.append
        w('[')
        self.fmt_items(o, indent, allowance + 1, context, level)
        w(']')

    def p_tuple(self, o, indent, allowance, context, level):
        w = self.out.append
        w('(')
        end = ',)' if len(o) == 1 else ')'
        self.fmt_items(o, indent, allowance + len(end), context, level)
        w(end)

    def fmt_items(self, items, indent, allowance, context, level):
        w = self.out.append
        indent += self.ipl
        if self.ipl > 1:
            w((self.ipl - 1) * ' ')
        delimnl = ',\n' + ' ' * indent
        delim = ''
        width = max_width = self.width - indent + 1
        it = iter(items)
        try:
            next_ent = next(it)
        except StopIteration:
            return
        last = False
        while not last:
            ent = next_ent
            try:
                next_ent = next(it)
            except StopIteration:
                last = True
                max_width -= allowance
                width -= allowance
            if self.compact:
                rep = self._repr(ent, context, level)
                wd = len(rep) + 2
                if width < wd:
                    width = max_width
                    if delim:
                        delim = delimnl
                if width >= wd:
                    width -= wd
                    w(delim)
                    delim = ', '
                    w(rep)
                    continue
            w(delim)
            delim = delimnl
            self._format(ent, indent, allowance if last else 1, context, level)

    def p_str(self, o, indent, allowance, context, level):
        w = self.out.append
        if not len(o):
            w(repr(o))
            return
        chunks = []
        lines = o.splitlines(True)
        if level == 1:
            indent += 1
            allowance += 1
        max_width1 = max_width = self.width - indent
        for i, line in enumerate(lines):
            rep = repr(line)
            if i == len(lines) - 1:
                max_width1 -= allowance
            if len(rep) <= max_width1:
                chunks.append(rep)
            else:
                parts = re.findall(r'\S*\s*', line)
                parts.pop()
                max_width2 = max_width
                current = ''
                for j, part in enumerate(parts):
                    cand = current + part
                    if j == len(parts) - 1 and i == len(lines) - 1:
                        max_width2 -= allowance
                    if len(repr(cand)) > max_width2:
                        if current:
                            chunks.append(repr(current))
                        current = part
                    else:
                        current = cand
                if current:
                    chunks.append(repr(current))
        if len(chunks) == 1:
            w(chunks[0])
            return
        if level == 1:
            w('(')
        for i, rep in enumerate(chunks):
            if i > 0:
                w('\n' + ' ' * indent)
            w(rep)
        if level == 1:
            w(')')


def solve(obj, indent=1, width=80, depth=None, *, compact=False, sort_dicts=True, underscore_numbers=False) -> str:
    p = _P(indent, width, depth, compact, sort_dicts, underscore_numbers)
    p._format(obj, 0, 0, {}, 0)
    return ''.join(p.out)
