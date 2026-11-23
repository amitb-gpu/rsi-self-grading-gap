"""Task registry.

Each task asks the loop to reimplement one CPython 3.12.7 standard-library
function *exactly*, without importing it. Ground truth is CPython itself, so
the reference was written by neither the model under study nor the study's
author (see PREREGISTRATION.md, "Instrument independence").

A task defines:
  module      top-level stdlib module the solution may not import
  blocked     stdlib source files removed from the task sandbox interpreter
  contract    the solve() signature and return convention shown to the loop
  dist        prose description of the input distribution, shown to BOTH arms
  gen(rng)    -> (args, kwargs) one random input
  reference(args, kwargs) -> raw CPython result (only ever run in the full env)
  canon(x)    -> JSON-able canonical form used for exact comparison

Exceptions are canonicalised as {"raises": <ExceptionClassName>}.
"""
from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import Any, Callable


def to_jsonable(x: Any) -> Any:
    if isinstance(x, (list, tuple)):
        return [to_jsonable(v) for v in x]
    if isinstance(x, dict):
        return {str(k): to_jsonable(v) for k, v in x.items()}
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    return repr(x)


@dataclass(frozen=True)
class Task:
    name: str
    module: str
    blocked: tuple[str, ...]
    contract: str
    dist: str
    gen: Callable[[random.Random], tuple[list, dict]]
    reference: Callable[[list, dict], Any]
    canon: Callable[[Any], Any] = to_jsonable
    group: str = "pilot_v1"          # pilot_v1 (ceilinged in pilot) | v2_candidate
    probe: str = ""                  # sandbox check that must FAIL; default "import <module>"
    qualname: str = ""


def pick(rng: random.Random, xs):
    return xs[rng.randrange(len(xs))]


def join_frags(rng, frags, lo, hi):
    return "".join(pick(rng, frags) for _ in range(rng.randint(lo, hi)))


# --------------------------------------------------------------------- shlex
SHLEX_FRAGS = [
    "foo", "bar", "a b", " ", "  ", "\t", "\n", "'", '"', "\\", "\\\\", "\\'",
    '\\"', "'x y'", '"x y"', '"a\\"b"', "'a\\'", "#", "# c", "x#y", "=", "a=b",
    "$HOME", "`", ";", "|", "&&", "(", ")", "*", "~", "é", "-", "--opt",
    "''", '""', "\\ ", "\\\n", "\r",
]


def shlex_gen(rng):
    s = join_frags(rng, SHLEX_FRAGS, 1, 9)
    kw = {}
    if rng.random() < 0.35:
        kw["comments"] = True
    if rng.random() < 0.25:
        kw["posix"] = False
    return [s], kw


def shlex_ref(args, kw):
    import shlex
    return shlex.split(*args, **kw)


# ------------------------------------------------------------------ textwrap
TW_WORDS = [
    "a", "an", "the", "word", "wrapping", "supercalifragilistic",
    "well-known", "e-mail", "re-re-re-entry", "x--y", "--", "-dash", "end.",
    "Mr.", "Done!", "Why?", "ok.", "  ", " ", "\t", "\n", "\r", "\x0b", "\x0c",
    "tab\tbed", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "1,000", "(paren)", "\"quote.\"",
]


def textwrap_gen(rng):
    text = " ".join(pick(rng, TW_WORDS) for _ in range(rng.randint(0, 14)))
    width = pick(rng, [1, 2, 3, 5, 8, 10, 12, 15, 20, 30, 0, -1]) if rng.random() < 0.95 else 70
    kw: dict = {}
    for key, p in [("break_long_words", 0.4), ("break_on_hyphens", 0.4),
                   ("drop_whitespace", 0.3), ("expand_tabs", 0.3),
                   ("replace_whitespace", 0.3), ("fix_sentence_endings", 0.3)]:
        if rng.random() < p:
            kw[key] = rng.random() < 0.5
    if rng.random() < 0.3:
        kw["initial_indent"] = pick(rng, ["", " ", "* ", ">>> ", "\t"])
    if rng.random() < 0.3:
        kw["subsequent_indent"] = pick(rng, ["", " ", "  ", "-- "])
    if rng.random() < 0.2:
        kw["tabsize"] = pick(rng, [0, 1, 4, 8])
    if rng.random() < 0.3:
        kw["max_lines"] = pick(rng, [1, 2, 3])
        if rng.random() < 0.5:
            kw["placeholder"] = pick(rng, [" [...]", "...", "", " ~"])
    return [text, width], kw


def textwrap_ref(args, kw):
    import textwrap
    return textwrap.wrap(*args, **kw)


# ------------------------------------------------------------------- fnmatch
FN_NAME_CHARS = "abcAB.-_/[]!^*?\\0 "
FN_PAT_TOKENS = [
    "a", "b", "c", "A", ".", "-", "/", "*", "**", "?", "[abc]", "[!a]", "[^a]",
    "[a-c]", "[c-a]", "[]]", "[!]]", "[]", "[!]", "[", "]", "[a-]", "[-a]",
    "[a-c-e]", "\\", "\\*", "[\\]", "[[]", "[*]", "[?]", "[!-]", "[--0]", " ",
]


def _instantiate(rng, tok):
    """A string the token plausibly matches (not guaranteed: odd tokens pass through)."""
    if tok == "*" or tok == "**":
        return "".join(pick(rng, "abc.") for _ in range(rng.randint(0, 2)))
    if tok == "?":
        return pick(rng, "abcA.-/")
    if tok.startswith("[") and tok.endswith("]") and len(tok) > 2:
        body = tok[1:-1]
        if body[:1] in "!^" and len(body) > 1:
            return pick(rng, "xyzB0")
        if len(body) == 3 and body[1] == "-":
            return body[0]
        return pick(rng, body)
    return tok


def _fn_name(rng, toks):
    if rng.random() < 0.5:
        name = "".join(_instantiate(rng, t) for t in toks)
        if rng.random() < 0.3 and name:
            i = rng.randrange(len(name))
            name = name[:i] + pick(rng, FN_NAME_CHARS) + name[i + 1:]
        return name
    return "".join(pick(rng, FN_NAME_CHARS) for _ in range(rng.randint(0, 6)))


def fnmatch_gen(rng):
    toks = [pick(rng, FN_PAT_TOKENS) for _ in range(rng.randint(0, 5))]
    names = [_fn_name(rng, toks) for _ in range(8)]
    return [names, "".join(toks)], {}


def fnmatch_ref(args, kw):
    import fnmatch
    return fnmatch.filter(*args)


# ------------------------------------------------------------------- urlsplit
URL_SCHEMES = ["http", "HTTP", "https", "git+ssh", "a.b-c", "1http", "mailto", "file", "x", ""]
URL_HOSTS = ["example.com", "EXAMPLE.com", "127.0.0.1", "[::1]", "[::1", "::1]", "[v1.fe]",
             "user@h", "user:pw@h", "u@v@h", "h:80", "h:", "h:abc", "h:99999", "", "℀x", "ex／a"]
URL_PATHS = ["", "/", "/a/b", "a/b", "//x", "/a;p", "/%20", "/a b", "/a:b"]
URL_EXTRA = ["", "?q=1", "?", "?a=1&b=2", "#f", "#", "?q#f", "#f?q", "?q#f#g"]


def urlsplit_gen(rng):
    lead = pick(rng, ["", "", "", " ", "\x00", "\x1f "])
    scheme = pick(rng, URL_SCHEMES)
    sep = pick(rng, ["://", ":", ":/", "", "//"])
    url = (lead + scheme + sep + pick(rng, URL_HOSTS) + pick(rng, URL_PATHS)
           + pick(rng, URL_EXTRA))
    if rng.random() < 0.2:
        i = rng.randint(0, len(url))
        url = url[:i] + pick(rng, ["\t", "\n", "\r"]) + url[i:]
    kw: dict = {}
    if rng.random() < 0.2:
        kw["scheme"] = pick(rng, ["https", "ftp"])
    if rng.random() < 0.2:
        kw["allow_fragments"] = False
    return [url], kw


def urlsplit_ref(args, kw):
    import urllib.parse
    return tuple(urllib.parse.urlsplit(*args, **kw))


# ------------------------------------------------------------------ parseaddr
PA_FRAGS = [
    "John", "Doe", " ", "  ", "john", "@", "example.com", "<", ">", "\"", "\"J D\"",
    "(comment)", "(", ")", ",", ".", "..", "\\", "\\\"", ":", ";", "a@b", "<a@b>",
    "j.d@ex.org", "Mary <m@x.io>", "@x", "x@", "[1.2.3.4]", "\t", "é",
]


PA_LOCAL = ["john", "j.d", "a", "first.last", "x+tag", "\"q u\"", "o'brien", "john", "mary_k",
            "a..b", ""]
PA_DOMAIN = ["example.com", "ex.org", "b", "sub.ex.co.uk", "example.com", "ex.org", "mail.io",
             "[1.2.3.4]", "ex..com", ""]
PA_NAME = ["", "John Doe", "\"Doe, John\"", "Mary", "\"J \\\"Q\\\" D\"", "Zoë", "(c) J"]


def _structured_addr(rng):
    addr = pick(rng, PA_LOCAL) + "@" + pick(rng, PA_DOMAIN)
    form = rng.random()
    name = pick(rng, PA_NAME)
    if form < 0.4:
        return f"{name} <{addr}>".strip()
    if form < 0.6:
        return f"{addr} ({pick(rng, ['comment', 'John', 'a (nested) c', ''])})"
    if form < 0.9:
        return addr
    return f"{name} <{addr}>, {pick(rng, PA_LOCAL)}@{pick(rng, PA_DOMAIN)}"


def parseaddr_gen(rng):
    if rng.random() < 0.8:
        addr = _structured_addr(rng)
        if rng.random() < 0.3:
            i = rng.randint(0, len(addr))
            addr = addr[:i] + pick(rng, PA_FRAGS) + addr[i:]
    else:
        addr = join_frags(rng, PA_FRAGS, 1, 6)
    kw = {}
    if rng.random() < 0.25:
        kw["strict"] = False
    return [addr], kw


def parseaddr_ref(args, kw):
    import email.utils
    return email.utils.parseaddr(*args, **kw)


# ------------------------------------------------------------------ ipaddress
def _valid_v4(rng):
    return ".".join(str(pick(rng, [0, 1, 7, 10, 127, 168, 192, 254, 255, rng.randint(0, 255)])) for _ in range(4))


def _valid_v6(rng):
    groups = [pick(rng, ["0", "0", "0", "1", "ffff", "FFFF", "fe80", "abcd", "db8", "2001", "00a0", "0000"])
              for _ in range(8)]
    style = rng.random()
    if style < 0.35:
        return ":".join(groups)
    if style < 0.75:  # compress a random run with '::'
        i = rng.randint(0, 7)
        j = rng.randint(i, 8)
        return ":".join(groups[:i]) + "::" + ":".join(groups[j:])
    return ":".join(groups[:6]) + ":" + _valid_v4(rng)  # embedded IPv4 tail


IP_MUTATIONS = [
    lambda rng, s: s + pick(rng, ["%eth0", "%1", "%", "%a%b", "%/x"]),
    lambda rng, s: s.replace(".", ".0", 1),
    lambda rng, s: s.replace(":", ":::", 1),
    lambda rng, s: s + pick(rng, [":1", ".1", "/24", " ", ":"]),
    lambda rng, s: pick(rng, [" ", "[", "::", "0"]) + s,
    lambda rng, s: s.replace(pick(rng, ["1", "0", "f", "a"]), pick(rng, ["g", "256", "00000", ""]), 1),
    lambda rng, s: s.upper(),
]


def ip_gen(rng):
    r = rng.random()
    if r < 0.85:
        s = _valid_v4(rng) if rng.random() < 0.4 else _valid_v6(rng)
        if rng.random() < 0.45:
            s = pick(rng, IP_MUTATIONS)(rng, s)
    else:
        s = pick(rng, ["::", "::1", "::ffff:1.2.3.4", "1::", "::1.2.3.4", "1:2:3:4:5:6:7:8",
                       "1:2:3:4:5:6:7::", "::2:3:4:5:6:7:8", "0.0.0.0", "localhost", "",
                       "1.2.3.4/24", "[::1]", "::ffff:0:0", "fe80::1%eth0", "1:2:3:4:5:6:1.2.3.4",
                       "01.2.3.4", "1.2.3", "1:2:3:4:5:6:7:8:9", ":::"])
    return [s], {}


def ip_ref(args, kw):
    import ipaddress
    a = ipaddress.ip_address(*args)
    return (a.version, str(a))


TASKS: dict[str, Task] = {
    "shlex_split": Task(
        name="shlex_split", module="shlex", blocked=("shlex.py",),
        contract="def solve(s, comments=False, posix=True) -> list[str]\n"
                 "Behave exactly like shlex.split(s, comments=comments, posix=posix) in CPython 3.12.7, "
                 "including raising ValueError in the same situations.",
        dist="s is a concatenation of 1-9 fragments drawn from: plain words, spaces, tabs, "
             "newlines, carriage returns, single and double quotes (balanced and unbalanced), "
             "backslashes and backslash escapes, '#' comments, shell punctuation (; | && ( ) ` $ * ~ =), "
             "a non-ASCII letter, option-like words. comments=True in ~35% of inputs; posix=False in ~25%.",
        gen=shlex_gen, reference=shlex_ref),
    "textwrap_wrap": Task(
        name="textwrap_wrap", module="textwrap", blocked=("textwrap.py",),
        contract="def solve(text, width=70, **kwargs) -> list[str]\n"
                 "Behave exactly like textwrap.wrap(text, width, **kwargs) in CPython 3.12.7 for every "
                 "TextWrapper keyword argument, including raising ValueError in the same situations.",
        dist="text is 0-14 space-joined tokens drawn from: short and very long words, hyphenated words, "
             "'--', sentence-ending words ('end.', 'Mr.', 'Why?'), and whitespace tokens (spaces, tab, "
             "newline, \\r, \\v, \\f). width is one of 1,2,3,5,8,10,12,15,20,30,0,-1 (rarely 70). Each of "
             "break_long_words, break_on_hyphens, drop_whitespace, expand_tabs, replace_whitespace, "
             "fix_sentence_endings, initial_indent, subsequent_indent, tabsize, max_lines and placeholder "
             "is independently set to a non-default-or-default value in 20-40% of inputs.",
        gen=textwrap_gen, reference=textwrap_ref),
    "fnmatch_filter": Task(
        name="fnmatch_filter", module="fnmatch", blocked=("fnmatch.py",),
        contract="def solve(names, pat) -> list[str]\n"
                 "Behave exactly like fnmatch.filter(names, pat) in CPython 3.12.7 on POSIX (case-sensitive, "
                 "order and duplicates preserved).",
        dist="pat is 0-5 tokens drawn from literals, "
             "'*', '**', '?', bracket expressions (positive, '!'- and '^'-negated, ranges including "
             "reversed ranges, empty '[]', ']' as first member, unclosed '[', '-' at either end, "
             "backslashes inside and outside brackets). names is a list of 8 strings; each name, independently, "
             "is with probability 50% built to plausibly match pat token by token (then has one character "
             "replaced ~30% of the time), and otherwise is 0-6 random characters from 'abcAB.-_/[]!^*?\\\\0 '.",
        gen=fnmatch_gen, reference=fnmatch_ref),
    "urllib_urlsplit": Task(
        name="urllib_urlsplit", module="urllib.parse", blocked=("urllib/parse.py",),
        contract="def solve(url, scheme='', allow_fragments=True) -> tuple[str, str, str, str, str]\n"
                 "Return exactly tuple(urllib.parse.urlsplit(url, scheme, allow_fragments)) as CPython 3.12.7 "
                 "does (scheme, netloc, path, query, fragment), including raising ValueError in the same "
                 "situations.",
        dist="url = optional leading junk (space, NUL, \\x1f) + scheme (valid, uppercase, with '+', "
             "starting with a digit, or empty) + separator ('://', ':', ':/', '', '//') + host part "
             "(names, IPv4, bracketed/half-bracketed IPv6, userinfo with '@' and ':', ports that are "
             "numeric/empty/non-numeric/out of range, a few non-ASCII hosts) + path + query/fragment "
             "variants. ~20% have a tab/newline/CR inserted at a random position. scheme default is "
             "overridden in ~20%; allow_fragments=False in ~20%.",
        gen=urlsplit_gen, reference=urlsplit_ref),
    "email_parseaddr": Task(
        name="email_parseaddr", module="email.utils", blocked=("email/utils.py",),
        contract="def solve(addr, *, strict=True) -> tuple[str, str]\n"
                 "Behave exactly like email.utils.parseaddr(addr, strict=strict) in CPython 3.12.7.",
        dist="~80% of addr values are structured: 'Name <local@domain>', 'local@domain (comment)', a bare "
             "'local@domain', or two comma-separated addresses, with locals and domains that are ordinary, "
             "dotted, quoted, tagged, double-dotted, empty, or domain literals, and display names that are "
             "plain, quoted (with commas or escaped quotes), non-ASCII or comment-like; ~30% of those have one "
             "junk fragment inserted at a random position. The other ~20% are a concatenation of 1-6 junk "
             "fragments (names, spaces, tab, '@', angle brackets, quotes, parens, commas, dots, backslashes, "
             "':' ';', whole addresses). strict=False in ~25% of inputs.",
        gen=parseaddr_gen, reference=parseaddr_ref),
    "ipaddress_ip_address": Task(
        name="ipaddress_ip_address", module="ipaddress", blocked=("ipaddress.py",),
        contract="def solve(address: str) -> tuple[int, str]\n"
                 "Return (a.version, str(a)) where a = ipaddress.ip_address(address) in CPython 3.12.7, "
                 "or raise ValueError exactly when ip_address would.",
        dist="address is a string. ~85% start from a valid address (40% IPv4 dotted quad; 60% IPv6 in full, "
             "'::'-compressed, or embedded-IPv4-tail form, with mixed-case and zero-padded groups); about "
             "45% of those are then mutated once (append a '%' scope id, insert a leading zero, triple a "
             "colon, append ':1'/'.1'/'/24'/space/':', prepend space/'['/'::'/'0', replace a digit with "
             "'g'/'256'/'00000'/'', or upper-case). ~15% are hand-picked edge cases (::, ::1, v4-mapped, "
             "zone ids, CIDR suffix, brackets, empty, 'localhost', too few/many parts).",
        gen=ip_gen, reference=ip_ref),
}


# =====================================================================================
# v2 candidates (pre-committed in PREREGISTRATION 8.3). Inputs are JSON-representable.
# =====================================================================================

# ------------------------------------------------------------------- pprint.pformat
PP_WORDS = ["a", "bb", "key", "value", "x y", "long string with several words in it", "",
            "quote's", 'dq"', "tab\there", "newline\nhere", "ünï", "0", "None"]


def _pp_obj(rng, depth):
    r = rng.random()
    if depth <= 0 or r < 0.35:
        return pick(rng, [
            lambda: pick(rng, PP_WORDS) * rng.choice([1, 1, 1, 3, 8]),
            lambda: rng.choice([0, 1, -7, 42, 12345678, 10 ** 12, -(10 ** 9) - 1]),
            lambda: rng.choice([0.5, 1e-7, 3.14159, -2.0, 1e22]),
            lambda: rng.choice([True, False, None]),
        ])()
    if r < 0.7:
        return [_pp_obj(rng, depth - 1) for _ in range(rng.randint(0, 6))]
    keys = rng.sample(["a", "b", "zeta", "Alpha", "10", "2", "k" * 12, "", "mid key"], rng.randint(0, 5))
    return {k: _pp_obj(rng, depth - 1) for k in keys}


def pprint_gen(rng):
    obj = _pp_obj(rng, rng.randint(1, 4))
    kw = {}
    if rng.random() < 0.9:
        kw["width"] = pick(rng, [8, 12, 16, 20, 30, 40, 60, 80])
    if rng.random() < 0.3:
        kw["indent"] = pick(rng, [0, 2, 4])
    if rng.random() < 0.2:
        kw["depth"] = pick(rng, [1, 2])
    if rng.random() < 0.35:
        kw["compact"] = True
    if rng.random() < 0.25:
        kw["sort_dicts"] = False
    if rng.random() < 0.2:
        kw["underscore_numbers"] = True
    return [obj], kw


def pprint_ref(args, kw):
    import pprint
    return pprint.pformat(*args, **kw)


# ------------------------------------------------------------ difflib get_opcodes
def _seq(rng, alphabet, lo, hi):
    return "".join(pick(rng, alphabet) for _ in range(rng.randint(lo, hi)))


def opcodes_gen(rng):
    r = rng.random()
    if r < 0.45:  # short strings, b an edited copy of a
        a = _seq(rng, "abcde ", 0, 25)
        b = list(a)
        for _ in range(rng.randint(0, 5)):
            op = rng.random()
            i = rng.randint(0, len(b))
            if op < 0.4:
                b.insert(i, pick(rng, "abcdexy "))
            elif op < 0.7 and b:
                del b[min(i, len(b) - 1)]
            elif b:
                b[min(i, len(b) - 1)] = pick(rng, "abxyz")
        b = "".join(b)
    elif r < 0.7:  # lists of lines
        lines = ["def f():", "    return 1", "", "x = 2", "# c", "pass", "    pass", "}"]
        a = [pick(rng, lines) for _ in range(rng.randint(0, 12))]
        b = [ln if rng.random() < 0.75 else pick(rng, lines) for ln in a]
        if rng.random() < 0.5:
            b.insert(rng.randint(0, len(b)), pick(rng, lines))
    else:  # long b to exercise autojunk (>= 200 items) with popular elements
        a = _seq(rng, "ab c", 20, 80)
        b = _seq(rng, "aab c", 200, 260)
    kw = {}
    if rng.random() < 0.3:
        kw["autojunk"] = False
    return [a, b], kw


def opcodes_ref(args, kw):
    import difflib
    return difflib.SequenceMatcher(None, *args, **kw).get_opcodes()


# ------------------------------------------------------- difflib get_close_matches
CM_BASE = ["apple", "apply", "ape", "peach", "appel", "maple", "applet", "pineapple", "happy",
           "grape", "april", "pple", "a", "", "aaaa", "banana", "bandana", "cabana"]


def _mutate(rng, w):
    w = list(w)
    for _ in range(rng.randint(0, 3)):
        i = rng.randint(0, len(w))
        op = rng.random()
        if op < 0.4:
            w.insert(i, pick(rng, "aelpnx"))
        elif op < 0.7 and w:
            del w[min(i, len(w) - 1)]
        elif w:
            w[min(i, len(w) - 1)] = pick(rng, "aelpnx")
    return "".join(w)


def close_gen(rng):
    word = pick(rng, CM_BASE) if rng.random() < 0.6 else _mutate(rng, pick(rng, CM_BASE))
    poss = [pick(rng, CM_BASE) if rng.random() < 0.5 else _mutate(rng, pick(rng, CM_BASE))
            for _ in range(rng.randint(0, 12))]
    kw = {}
    if rng.random() < 0.5:
        kw["n"] = pick(rng, [1, 2, 5])
    if rng.random() < 0.6:
        kw["cutoff"] = pick(rng, [0.0, 0.3, 0.5, 0.75, 0.9])
    return [word, poss], kw


def close_ref(args, kw):
    import difflib
    return difflib.get_close_matches(*args, **kw)


# ------------------------------------------------------- email.utils.parsedate_tz
PD_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Monday", "mon", "Xyz"]
PD_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
             "jan", "JANUARY", "Sept", "Foo"]
PD_TZ = ["+0000", "-0500", "+0530", "-1200", "+2400", "GMT", "UT", "UTC", "EST", "EDT", "PST",
         "pdt", "Z", "A", "XYZ", "+05", "-0", "", "", ""]


def parsedate_gen(rng):
    odd = rng.random() < 0.5  # about half the inputs get odd values; the rest are mostly well-formed
    day = str(pick(rng, [1, 2, 9, 10, 23, 31] + ([32, 0] if odd else [])))
    mon = pick(rng, PD_MONTHS[:12] * 3 + (PD_MONTHS[12:] if odd else []))
    year = str(pick(rng, [2026, 1999, 2026, 1999, 26, 99, 70, 69] + ([0, 3, 100, 10000, 1900] if odd else [])))
    hh = pick(rng, ["00", "9", "23"] + (["24", "25"] if odd else []))
    mm = pick(rng, ["00", "05", "59"] + (["60"] if odd else []))
    ss = pick(rng, ["00", "30", "59"] + (["61"] if odd else []))
    time = pick(rng, [f"{hh}:{mm}:{ss}"] * 3 + [f"{hh}:{mm}", ""] + ([f"{hh}.{mm}.{ss}", f"{hh}:{mm}:{ss}.5"] if odd else []))
    tz = pick(rng, PD_TZ)
    parts = [day, mon, year, time, tz]
    order = rng.random()
    if order < 0.15:
        parts = [mon, day, year, time, tz]
    elif order < 0.25:
        parts = [day, mon, time, year, tz]
    elif order < 0.3:
        parts = [year, mon, day, time, tz]
    s = " ".join(p for p in parts if p)
    if rng.random() < 0.6:
        s = pick(rng, PD_DAYS) + pick(rng, [", ", " ", ",", ",  "]) + s
    if rng.random() < 0.15:
        s = s.replace(" ", pick(rng, ["  ", "-", ", "]), 1)
    if rng.random() < 0.1:
        s = pick(rng, ["", " ", "2026-11-23T10:00:00Z", "garbage", "1 Jan"]) if rng.random() < 0.5 else s + " (EST)"
    return [s], {}


def parsedate_ref(args, kw):
    import email.utils
    return email.utils.parsedate_tz(*args)


# ----------------------------------------------------------- html.parser events
HP_FRAGS = ["text", " ", "\n", "<p>", "</p>", "<P CLASS=x>", "<a href='u'>", '<a href="v" id=b>',
            "<br/>", "<br />", "<img src=x alt>", "</a>", "<!-- c -->", "<!---->", "<!-- unclosed",
            "<!DOCTYPE html>", "<?php echo 1 ?>", "<![CDATA[x<y]]>", "&amp;", "&lt", "&#65;",
            "&#x41;", "&#xZZ;", "&bogus;", "& ", "<", ">", "< p>", "</ p>", "<script>if(a<b){}</script>",
            "<style>p>a{}</style>", "<script>x</scr", "</>", "<a b='c>", "<div data-x=\"1\" hidden>",
            "<!x>", "<!>", "</div  >", "<td nowrap>", "<1abc>"]


def htmlparser_gen(rng):
    return [join_frags(rng, HP_FRAGS, 1, 8)], {}


def htmlparser_ref(args, kw):
    from html.parser import HTMLParser

    class Rec(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.ev = []

        def handle_starttag(self, tag, attrs): self.ev.append(["starttag", tag, attrs])
        def handle_endtag(self, tag): self.ev.append(["endtag", tag])
        def handle_startendtag(self, tag, attrs): self.ev.append(["startendtag", tag, attrs])
        def handle_data(self, data): self.ev.append(["data", data])
        def handle_comment(self, data): self.ev.append(["comment", data])
        def handle_charref(self, name): self.ev.append(["charref", name])
        def handle_entityref(self, name): self.ev.append(["entityref", name])
        def handle_decl(self, decl): self.ev.append(["decl", decl])
        def handle_pi(self, data): self.ev.append(["pi", data])
        def unknown_decl(self, data): self.ev.append(["unknown_decl", data])

    p = Rec()
    p.feed(args[0])
    p.close()
    return p.ev


# ---------------------------------------------------------------- html.unescape
HU_FRAGS = ["a", " ", "&amp;", "&amp", "&AMP;", "&lt;", "&gt", "&quot;", "&nbsp;", "&copy",
            "&notin;", "&notit;", "&ampx", "&eacute;", "&Eacute", "&zwj;", "&hearts;", "&bogus;",
            "&#65;", "&#065", "&#x41;", "&#X41;", "&#x;", "&#;", "&#0;", "&#128;", "&#x80;", "&#150;",
            "&#xD800;", "&#x110000;", "&#1114111;", "&#9999999999;", "&#x1F600;", "&", "&&", "&;",
            "&LongLeftRightArrow;", "&ngE;", "&fjlig;", "&acE;", "&Tab;", "&NewLine;"]


def unescape_gen(rng):
    return [join_frags(rng, HU_FRAGS, 1, 6)], {}


def unescape_ref(args, kw):
    import html
    return html.unescape(*args)


# ------------------------------------------------------- urllib.parse.parse_qsl
QS_FRAGS = ["a=1", "b=", "=c", "d", "e=f=g", "a+b=c+d", "x=%20", "y=%2", "z=%zz", "u=%C3%A9",
            "v=%E9", "w=%F0%9F%98%80", "k%3Dv=1", "", "&", ";", "q=1;r=2", "%=%", "+=+", "s=%2B"]


def parseqsl_gen(rng):
    sep = "&" if rng.random() < 0.8 else ";"
    qs = sep.join(pick(rng, QS_FRAGS) for _ in range(rng.randint(1, 5)))
    kw = {}
    if rng.random() < 0.4:
        kw["keep_blank_values"] = True
    if rng.random() < 0.25:
        kw["strict_parsing"] = True
    if sep == ";" or rng.random() < 0.1:
        kw["separator"] = sep if sep == ";" else pick(rng, [";", "&&", ""])
    return [qs], kw


def parseqsl_ref(args, kw):
    import urllib.parse
    return urllib.parse.parse_qsl(*args, **kw)


V2 = {
    "pprint_pformat": Task(
        name="pprint_pformat", module="pprint", blocked=("pprint.py",), group="v2_candidate",
        qualname="pprint.pformat",
        contract="def solve(obj, indent=1, width=80, depth=None, *, compact=False, sort_dicts=True, "
                 "underscore_numbers=False) -> str\n"
                 "Return exactly pprint.pformat(obj, indent, width, depth, compact=compact, "
                 "sort_dicts=sort_dicts, underscore_numbers=underscore_numbers) as CPython 3.12.7 does.",
        dist="obj is a random nested structure of depth 1-4 built from lists (0-6 items), dicts "
             "(0-5 string keys such as 'a', 'zeta', 'Alpha', '10', '2', '', a long key), strings "
             "(short, empty, with quotes/tab/newline/non-ASCII, or repeated up to 8x so they get "
             "long), ints (including large and negative), floats and True/False/None. width is "
             "8-80 in ~90% of inputs; indent, depth, compact, sort_dicts and underscore_numbers "
             "are each set to a non-default value in 20-35% of inputs.",
        gen=pprint_gen, reference=pprint_ref),
    "difflib_opcodes": Task(
        name="difflib_opcodes", module="difflib", blocked=("difflib.py",), group="v2_candidate",
        qualname="difflib.SequenceMatcher.get_opcodes",
        contract="def solve(a, b, autojunk=True) -> list[tuple[str, int, int, int, int]]\n"
                 "Return exactly difflib.SequenceMatcher(None, a, b, autojunk=autojunk).get_opcodes() "
                 "as CPython 3.12.7 does. a and b are both strings or both lists of strings.",
        dist="~45%: a is a 0-25 character string over 'abcde ' and b is a copy with 0-5 random "
             "insertions/deletions/substitutions. ~25%: lists of 0-12 code-like lines, b a lightly "
             "edited copy. ~30%: a is 20-80 characters over 'ab c' and b is 200-260 characters over "
             "'aab c' (long enough for the autojunk heuristic). autojunk=False in ~30%.",
        gen=opcodes_gen, reference=opcodes_ref),
    "difflib_close_matches": Task(
        name="difflib_close_matches", module="difflib", blocked=("difflib.py",), group="v2_candidate",
        qualname="difflib.get_close_matches",
        contract="def solve(word, possibilities, n=3, cutoff=0.6) -> list[str]\n"
                 "Return exactly difflib.get_close_matches(word, possibilities, n, cutoff) as CPython "
                 "3.12.7 does, including raising ValueError in the same situations.",
        dist="word and the 0-12 possibilities are drawn from a fixed list of fruit-like words "
             "('apple', 'apply', 'ape', 'maple', 'banana', 'bandana', '', 'a', 'aaaa', ...), each "
             "independently mutated by 0-3 random edits with probability 40-50%. n is 1, 2 or 5 in "
             "~50% of inputs; cutoff is 0.0, 0.3, 0.5, 0.75 or 0.9 in ~60%.",
        gen=close_gen, reference=close_ref),
    "email_parsedate_tz": Task(
        name="email_parsedate_tz", module="email.utils", blocked=("email/utils.py", "email/_parseaddr.py"),
        group="v2_candidate", qualname="email.utils.parsedate_tz",
        probe="from email.utils import parsedate_tz",
        contract="def solve(data) -> tuple | None\n"
                 "Return exactly email.utils.parsedate_tz(data) as CPython 3.12.7 does (a 10-tuple or "
                 "None), including raising the same exceptions.",
        dist="RFC 2822-like date strings. In ~50% of inputs every field is drawn from well-formed values "
             "(day 1-31, three-letter month, 2- or 4-digit year, hh:mm:ss, hh:mm or no time); in the other "
             "~50% fields may also be odd (day 0/32, lower/upper-case or long or bogus month names, years "
             "0/3/100/1900/10000, hour 24/25, minute 60, second 61, dotted or fractional times). Timezones "
             "are numeric, named (GMT, UT, UTC, EST, EDT, PST, pdt, Z, military letter), bogus or absent. Field order is shuffled in ~30%; ~60% have a leading weekday "
             "with varied comma/space; ~15% have a separator mangled; ~10% are replaced by junk or get "
             "a trailing comment.",
        gen=parsedate_gen, reference=parsedate_ref),
    "html_parser_events": Task(
        name="html_parser_events", module="html.parser",
        blocked=("html/parser.py", "_markupbase.py", "html/__init__.py", "html/entities.py"),
        group="v2_candidate", qualname="html.parser.HTMLParser", probe="from html.parser import HTMLParser",
        contract="def solve(html: str) -> list\n"
                 "Feed html to a CPython 3.12.7 html.parser.HTMLParser(convert_charrefs=False), then call "
                 "close(), and return the handler calls in order as lists: ['starttag', tag, attrs], "
                 "['endtag', tag], ['startendtag', tag, attrs], ['data', text], ['comment', text], "
                 "['charref', name], ['entityref', name], ['decl', text], ['pi', text], "
                 "['unknown_decl', text]; attrs is a list of [name, value] pairs.",
        dist="html is a concatenation of 1-8 fragments: text, whitespace, start/end tags with upper/"
             "lower case and quoted/unquoted/valueless attributes (values contain no '&'), self-closing "
             "tags, comments (normal, empty, unclosed), doctype, processing instruction, CDATA, char/"
             "entity references (valid, malformed, unterminated), script/style elements (including "
             "unterminated), stray '<' and '>', malformed tags.",
        gen=htmlparser_gen, reference=htmlparser_ref),
    "html_unescape": Task(
        name="html_unescape", module="html", blocked=("html/__init__.py", "html/entities.py"),
        group="v2_candidate", qualname="html.unescape", probe="from html import unescape",
        contract="def solve(s: str) -> str\nReturn exactly html.unescape(s) as CPython 3.12.7 does.",
        dist="s is a concatenation of 1-6 fragments: plain text, named references with and without "
             "';' (common, rare, multi-codepoint, prefix-ambiguous like '&notit;' or '&ampx'), decimal "
             "and hex numeric references (valid, zero, the 0x80-0x9F range, surrogates, beyond "
             "U+10FFFF, huge, empty), and bare '&'.",
        gen=unescape_gen, reference=unescape_ref),
    "urllib_parse_qsl": Task(
        name="urllib_parse_qsl", module="urllib.parse", blocked=("urllib/parse.py",), group="v2_candidate",
        qualname="urllib.parse.parse_qsl",
        contract="def solve(qs, keep_blank_values=False, strict_parsing=False, separator='&') -> "
                 "list[tuple[str, str]]\n"
                 "Return exactly urllib.parse.parse_qsl(qs, keep_blank_values, strict_parsing, "
                 "separator=separator) as CPython 3.12.7 does (default encoding/errors), including "
                 "raising ValueError in the same situations.",
        dist="qs joins 1-5 fragments with '&' (~80%) or ';': key=value pairs, blank values, missing "
             "'=', extra '=', '+' signs, valid/truncated/invalid percent escapes, multi-byte and "
             "invalid UTF-8 escapes, empty segments. keep_blank_values=True in ~40%, "
             "strict_parsing=True in ~25%; separator is ';' when the string uses ';', and occasionally "
             "'&&' or ''.",
        gen=parseqsl_gen, reference=parseqsl_ref),
}
TASKS.update(V2)
STUDY_TASKS: list[str] = []  # filled at freeze by the PREREGISTRATION 8.3 rule
