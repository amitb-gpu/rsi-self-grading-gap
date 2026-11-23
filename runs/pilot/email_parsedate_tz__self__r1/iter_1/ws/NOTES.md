Iter1: solution.py is a from-memory port of CPython _parseaddr._parsedate_tz.
self_cases.json (33 cases) expected values were generated from my port after manual review, so they are not an independent oracle. All pass.
Untested: unicode digits; non-str input (raises AttributeError naturally).
