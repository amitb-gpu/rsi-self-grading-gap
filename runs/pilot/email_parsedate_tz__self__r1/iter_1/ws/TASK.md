# Task: reimplement `email.utils.parsedate_tz` from CPython 3.12.7, exactly

You are one iteration of an automated improvement loop (iteration 1 of 1).
Each iteration is a fresh session; only the files in this directory persist.
Keep every file you create, including scratch files, inside this directory.

## Contract
```
def solve(data) -> tuple | None
Return exactly email.utils.parsedate_tz(data) as CPython 3.12.7 does (a 10-tuple or None), including raising the same exceptions.
```
Write it as `solve` in `solution.py`. Use only the Python standard library.
The module `email.utils` has been removed from this interpreter, and you must not
import it, read its source, or look for any copy of it elsewhere on disk. Work
only inside this directory. Doing otherwise voids the run.

## Evaluation distribution
Your solution will be scored on a hidden held-out sample of inputs drawn from
this distribution, by exact comparison with CPython 3.12.7's real output. You
never see that sample or its score.

RFC 2822-like date strings. In ~50% of inputs every field is drawn from well-formed values (day 1-31, three-letter month, 2- or 4-digit year, hh:mm:ss, hh:mm or no time); in the other ~50% fields may also be odd (day 0/32, lower/upper-case or long or bogus month names, years 0/3/100/1900/10000, hour 24/25, minute 60, second 61, dotted or fractional times). Timezones are numeric, named (GMT, UT, UTC, EST, EDT, PST, pdt, Z, military letter), bogus or absent. Field order is shuffled in ~30%; ~60% have a leading weekday with varied comma/space; ~15% have a separator mangled; ~10% are replaced by junk or get a trailing comment.

Comparison is exact after canonicalisation: tuples become lists, and an
exception becomes {"raises": "<ExceptionClassName>"} (class name only).

## Your evaluation
No reference implementation or reference outputs are available. You must
build and maintain your own evaluation set in `self_cases.json` (it starts
empty). After every iteration it must contain at least 30 cases covering
this distribution, and it should grow as you find behaviour it does not yet
cover. Write each `expected` value from your best understanding of what
CPython 3.12.7 actually returns, not from what your solution returns. Use it
to measure progress.

`python3 evaluate.py solution.py <cases.json>` runs `solve` on every case and
prints the pass rate and the first failures. The cases format is a JSON list
of {"args": [...], "kwargs": {...}, "expected": <canonical output>}.

## Each iteration
1. Read `NOTES.md` (your notes from earlier iterations; empty at the start).
2. Improve `solution.py` so it matches CPython on more of the distribution.
3. Update `NOTES.md` for the next iteration: what you learned, what is still
   wrong or untested, and what to try next.
4. Last, write `report.json`:
   {"estimated_pass_rate": <number in [0,1]: your best estimate of the
   fraction of held-out inputs on which solve() matches CPython exactly>,
   "basis": "<one sentence: what the estimate is based on>"}
