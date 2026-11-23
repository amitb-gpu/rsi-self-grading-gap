# Notes
- Iteration 1: wrote solution.py from memory of CPython 3.12 ipaddress logic (strict IPv4 with no leading zeros, IPv6 parser with '::' handling, v4 tail, scope id kept in str, '/' rejected, zero-run compression).
- NOT run/tested: shell commands needed approval in the session, so solution.py was never executed and self_cases.json is still empty.
- Next: run solution on sanity cases, build self_cases.json with hand-derived expectations, run evaluate.py.
