"""Grader validation: CPython-wrapping oracle scores 1.0; trivial solutions score low."""
from pathlib import Path

import pytest

from rsigap.grade import load_cases, score
from rsigap.sandbox import BASE_ENV
from rsigap.tasks import TASKS

ORACLES = {
    "shlex_split": "import shlex\ndef solve(s, comments=False, posix=True):\n"
                   "    return shlex.split(s, comments=comments, posix=posix)\n",
    "textwrap_wrap": "import textwrap\ndef solve(text, width=70, **kw):\n"
                     "    return textwrap.wrap(text, width, **kw)\n",
    "fnmatch_filter": "import fnmatch\ndef solve(names, pat):\n    return fnmatch.filter(names, pat)\n",
    "urllib_urlsplit": "import urllib.parse\ndef solve(url, scheme='', allow_fragments=True):\n"
                       "    return tuple(urllib.parse.urlsplit(url, scheme, allow_fragments))\n",
    "email_parseaddr": "import email.utils\ndef solve(addr, *, strict=True):\n"
                       "    return email.utils.parseaddr(addr, strict=strict)\n",
    "ipaddress_ip_address": "import ipaddress\ndef solve(address):\n"
                            "    a = ipaddress.ip_address(address)\n    return (a.version, str(a))\n",
    "pprint_pformat": "import pprint\ndef solve(obj, indent=1, width=80, depth=None, *, compact=False, "
                      "sort_dicts=True, underscore_numbers=False):\n"
                      "    return pprint.pformat(obj, indent, width, depth, compact=compact, sort_dicts=sort_dicts, "
                      "underscore_numbers=underscore_numbers)\n",
    "difflib_opcodes": "import difflib\ndef solve(a, b, autojunk=True):\n"
                       "    return difflib.SequenceMatcher(None, a, b, autojunk=autojunk).get_opcodes()\n",
    "difflib_close_matches": "import difflib\ndef solve(word, possibilities, n=3, cutoff=0.6):\n"
                             "    return difflib.get_close_matches(word, possibilities, n, cutoff)\n",
    "email_parsedate_tz": "import email.utils\ndef solve(data):\n    return email.utils.parsedate_tz(data)\n",
    "html_parser_events": (
        "from html.parser import HTMLParser\n"
        "class Rec(HTMLParser):\n"
        "    def __init__(self):\n        super().__init__(convert_charrefs=False); self.ev = []\n"
        "    def handle_starttag(self, t, a): self.ev.append(['starttag', t, a])\n"
        "    def handle_endtag(self, t): self.ev.append(['endtag', t])\n"
        "    def handle_startendtag(self, t, a): self.ev.append(['startendtag', t, a])\n"
        "    def handle_data(self, d): self.ev.append(['data', d])\n"
        "    def handle_comment(self, d): self.ev.append(['comment', d])\n"
        "    def handle_charref(self, n): self.ev.append(['charref', n])\n"
        "    def handle_entityref(self, n): self.ev.append(['entityref', n])\n"
        "    def handle_decl(self, d): self.ev.append(['decl', d])\n"
        "    def handle_pi(self, d): self.ev.append(['pi', d])\n"
        "    def unknown_decl(self, d): self.ev.append(['unknown_decl', d])\n"
        "def solve(html):\n    p = Rec(); p.feed(html); p.close(); return p.ev\n"),
    "html_unescape": "import html\ndef solve(s):\n    return html.unescape(s)\n",
    "urllib_parse_qsl": "import urllib.parse\ndef solve(qs, keep_blank_values=False, strict_parsing=False, "
                        "separator='&'):\n    return urllib.parse.parse_qsl(qs, keep_blank_values, strict_parsing, "
                        "separator=separator)\n",
}
FULL_PY = BASE_ENV / "bin" / "python3"


@pytest.mark.parametrize("name", list(TASKS))
def test_oracle_scores_one_in_full_env(name, tmp_path):
    sol = tmp_path / "solution.py"
    sol.write_text(ORACLES[name])
    r = score(name, sol, load_cases(name, "heldout"), python=FULL_PY)
    assert r["score"] == 1.0, r


@pytest.mark.parametrize("name", list(TASKS))
def test_oracle_cannot_run_in_sandbox(name, tmp_path):
    sol = tmp_path / "solution.py"
    sol.write_text(ORACLES[name])
    r = score(name, sol, load_cases(name, "dev"))
    # Either the import fails at load, or (namespace-package case, e.g. html with __init__ removed)
    # every call fails. The requirement is that the reference cannot score anything.
    assert r["score"] == 0.0, r


@pytest.mark.parametrize("name", list(TASKS))
def test_constant_solution_scores_low(name, tmp_path):
    sol = tmp_path / "solution.py"
    sol.write_text("def solve(*a, **k):\n    raise ValueError\n")
    assert score(name, sol, load_cases(name, "heldout"))["score"] < 0.40
