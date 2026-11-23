# Task: reimplement `textwrap.wrap` from CPython 3.12.7, exactly

You are one iteration of an automated improvement loop (iteration 1 of 2).
Each iteration is a fresh session; only the files in this directory persist.

## Contract
```
def solve(text, width=70, **kwargs) -> list[str]
Behave exactly like textwrap.wrap(text, width, **kwargs) in CPython 3.12.7 for every TextWrapper keyword argument, including raising ValueError in the same situations.
```
Write it as `solve` in `solution.py`. Use only the Python standard library.
The module `textwrap` has been removed from this interpreter, and you must not
import it, read its source, or look for any copy of it elsewhere on disk. Work
only inside this directory. Doing otherwise voids the run.

## Evaluation distribution
Your solution will be scored on a hidden held-out sample of inputs drawn from
this distribution, by exact comparison with CPython 3.12.7's real output. You
never see that sample or its score.

text is 0-14 space-joined tokens drawn from: short and very long words, hyphenated words, '--', sentence-ending words ('end.', 'Mr.', 'Why?'), and whitespace tokens (spaces, tab, newline, \r, \v, \f). width is one of 1,2,3,5,8,10,12,15,20,30,0,-1 (rarely 70). Each of break_long_words, break_on_hyphens, drop_whitespace, expand_tabs, replace_whitespace, fix_sentence_endings, initial_indent, subsequent_indent, tabsize, max_lines and placeholder is independently set to a non-default-or-default value in 20-40% of inputs.

Comparison is exact after canonicalisation: tuples become lists, and an
exception becomes {"raises": "<ExceptionClassName>"} (class name only).

## Your evaluation
No reference implementation or reference outputs are available. Build
and maintain your own evaluation set in `self_cases.json` (it starts
empty) covering this distribution, with `expected` values that reflect
what CPython 3.12.7 actually returns, not what your solution returns.
Use it to measure progress.

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
