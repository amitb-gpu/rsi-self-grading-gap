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
    assert r["score"] == 0.0 and r["error"] in ("ModuleNotFoundError", "ImportError"), r


@pytest.mark.parametrize("name", list(TASKS))
def test_constant_solution_scores_low(name, tmp_path):
    sol = tmp_path / "solution.py"
    sol.write_text("def solve(*a, **k):\n    raise ValueError\n")
    assert score(name, sol, load_cases(name, "heldout"))["score"] < 0.40
