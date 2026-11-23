# Notes
- Iter 1: wrote solution.py from memory of CPython 3.12 textwrap (wordsep_re, _wrap_chunks, _handle_long_word, placeholder logic).
- No reference available; self_cases.json is still empty (expected values can't be verified without CPython's textwrap). Hand-derived cases would be the next step.
- Untested: an empty-text/width edge cases, max_lines with placeholder edge paths, tabsize negative.
