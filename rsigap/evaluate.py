"""Run solve() from a solution file on case inputs; optionally score against expected.

Standard library only: this file runs under the *sandbox* interpreter with -I,
both as the harness's grading child and (copied verbatim) as the loop's own
`evaluate.py`. It is identical in both arms; only the cases file differs.

Usage:
  python3 evaluate.py SOLUTION CASES.json              # score; print summary + failures
  python3 evaluate.py SOLUTION CASES.json --raw OUT    # write canonical outputs only (harness)

CASES.json is a list of {"args": [...], "kwargs": {...}, "expected": ...}.
Outputs are compared after canonicalisation: tuples become lists, and an
exception becomes {"raises": "<ExceptionClassName>"}; a case that runs over
PER_CASE_S seconds becomes {"timeout": true}.
"""
import importlib.util
import json
import signal
import sys

PER_CASE_S = 1.0


class _CaseTimeout(BaseException):
    pass


def _alarm(signum, frame):
    raise _CaseTimeout


def to_jsonable(x):
    if isinstance(x, (list, tuple)):
        return [to_jsonable(v) for v in x]
    if isinstance(x, dict):
        return {str(k): to_jsonable(v) for k, v in x.items()}
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    return repr(x)


def load_solve(path):
    spec = importlib.util.spec_from_file_location("solution_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.solve


def run_cases(path, cases):
    try:
        solve = load_solve(path)
    except BaseException as e:  # noqa: BLE001
        return [{"load_error": type(e).__name__}] * len(cases)
    signal.signal(signal.SIGALRM, _alarm)
    out = []
    for c in cases:
        signal.setitimer(signal.ITIMER_REAL, PER_CASE_S)
        try:
            r = to_jsonable(solve(*c["args"], **c.get("kwargs", {})))
        except _CaseTimeout:
            r = {"timeout": True}
        except KeyboardInterrupt:
            raise
        except BaseException as e:  # noqa: BLE001
            r = {"raises": type(e).__name__}
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        out.append(r)
    return out


def canon_eq(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def main(argv):
    sol, cases_path = argv[1], argv[2]
    with open(cases_path, encoding="utf-8") as f:
        cases = json.load(f)
    got = run_cases(sol, cases)
    if len(argv) > 4 and argv[3] == "--raw":
        with open(argv[4], "w", encoding="utf-8") as f:
            json.dump(got, f, ensure_ascii=False)
        return 0
    fails = [(c, g) for c, g in zip(cases, got) if not canon_eq(c["expected"], g)]
    n = len(cases)
    print(f"passed {n - len(fails)}/{n} = {((n - len(fails)) / n if n else 0):.4f}")
    for c, g in fails[:15]:
        print(json.dumps({"args": c["args"], "kwargs": c.get("kwargs", {}),
                          "expected": c["expected"], "got": g}, ensure_ascii=False))
    if len(fails) > 15:
        print(f"... {len(fails) - 15} more failures")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
