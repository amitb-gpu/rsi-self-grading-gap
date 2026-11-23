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
