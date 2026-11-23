# Notes
- Iter 1: solution.py is a from-memory port of CPython 3.12.7 email._parseaddr.AddrlistClass plus the
  strict-mode wrapper (paren-count pre-check replaces input with "('', '')"; '[' in address -> ('',''); !=1 addr -> ('','')).
- No reference available, so unverified against real CPython. self_cases.json left empty (no trustworthy expected values).
- Next: hand-derive cases from known CPython behaviour; re-check getaddrspec/getdomain details against memory.
