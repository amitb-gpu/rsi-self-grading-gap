# Task: reimplement `pprint.pformat` from CPython 3.12.7, exactly

You are one iteration of an automated improvement loop (iteration 1 of 1).
Each iteration is a fresh session; only the files in this directory persist.
Keep every file you create, including scratch files, inside this directory.

## Contract
```
def solve(obj, indent=1, width=80, depth=None, *, compact=False, sort_dicts=True, underscore_numbers=False) -> str
Return exactly pprint.pformat(obj, indent, width, depth, compact=compact, sort_dicts=sort_dicts, underscore_numbers=underscore_numbers) as CPython 3.12.7 does.
```
Write it as `solve` in `solution.py`. Use only the Python standard library.
The module `pprint` has been removed from this interpreter, and you must not
import it, read its source, or look for any copy of it elsewhere on disk. Work
only inside this directory. Doing otherwise voids the run.

## Evaluation distribution
Your solution will be scored on a hidden held-out sample of inputs drawn from
this distribution, by exact comparison with CPython 3.12.7's real output. You
never see that sample or its score.

obj is a random nested structure of depth 1-4 built from lists (0-6 items), dicts (0-5 string keys such as 'a', 'zeta', 'Alpha', '10', '2', '', a long key), strings (short, empty, with quotes/tab/newline/non-ASCII, or repeated up to 8x so they get long), ints (including large and negative), floats and True/False/None. width is 8-80 in ~90% of inputs; indent, depth, compact, sort_dicts and underscore_numbers are each set to a non-default value in 20-35% of inputs.

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
