"""Run one (task, arm, replicate) improvement loop with headless Claude Code.

Per iteration t = 1..T:
  1. write TASK.md for iteration t; delete any stale report.json
  2. run `claude -p` in the workspace (fresh session; files persist)
  3. snapshot workspace + transcript into the repo (runs/<run_id>/iter_<t>/)
  4. grade solution.py: sealed held-out (truth), dev (truth, second sample),
     and the loop's own evaluation file (external: dev_cases; self: self_cases)
  5. audit the transcript and workspace; append a hash-chained ledger record

The loop never sees held-out cases or held-out scores.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from . import audit as audit_mod
from .cases import DEV_DIR, ROOT
from .grade import load_cases, score
from .prompts import ARM_CASES_FILE, PROMPT, task_md
from .sandbox import WORK, sandbox_python
from .tasks import TASKS

MODEL = os.environ.get("RSIGAP_MODEL", "claude-sonnet-5-5")
CLAUDE_BIN = os.environ.get("RSIGAP_CLAUDE_BIN", "claude")  # overridable for plumbing tests only
ITER_TIMEOUT_S = 20 * 60
# Per-session cap on the CLI's reported cost. On a plan token this is the API-equivalent
# (notional) cost: nothing is billed per token, but the cap keeps compute per session bounded.
ITER_BUDGET_USD = float(os.environ.get("RSIGAP_ITER_BUDGET_USD", "4"))
TOKEN_FILE = Path.home() / ".config" / "rsigap" / "claude_oauth_token"
SESSION_SETTINGS = json.dumps({"autoMemoryEnabled": False, "disableAllHooks": True})
ALLOWED = ["Read", "Write", "Edit", "Bash(python3:*)", "Bash(python:*)"]
DISALLOWED = ["WebFetch", "WebSearch", "Glob", "Grep", "Agent", "Task", "NotebookEdit", "TodoWrite"]
LEDGER = ROOT / "runs" / "ledger.jsonl"
SNAP_GLOBS = ["*.py", "*.md", "*.json"]
SNAP_MAX_BYTES = 2_000_000


def run_id(task: str, arm: str, rep: int) -> str:
    return f"{task}__{arm}__r{rep}"


def stub(task_name: str) -> str:
    sig = TASKS[task_name].contract.splitlines()[0]
    return f"{sig}:\n    raise NotImplementedError\n"


def init_workspace(task: str, arm: str, ws: Path) -> None:
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    (ws / "solution.py").write_text(stub(task))
    (ws / "NOTES.md").write_text("")
    shutil.copy(Path(__file__).with_name("evaluate.py"), ws / "evaluate.py")
    if arm == "external":
        shutil.copy(DEV_DIR / f"{task}.json", ws / "dev_cases.json")
    else:
        (ws / "self_cases.json").write_text("[]")


def oauth_token() -> str:
    """Claude plan token from `claude setup-token`: env CLAUDE_CODE_OAUTH_TOKEN, else TOKEN_FILE
    (mode 600). Never logged. Sessions bill the user's plan, never the per-token API: any
    ANTHROPIC_API_KEY in the environment is removed before the CLI starts."""
    t = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
    if not t and TOKEN_FILE.exists():
        if TOKEN_FILE.stat().st_mode & 0o077:
            raise PermissionError(f"{TOKEN_FILE} must not be readable by group/others (chmod 600)")
        t = TOKEN_FILE.read_text().strip()
    if not t:
        raise RuntimeError(f"no plan token: run `claude setup-token` and save it to {TOKEN_FILE}")
    return t


def claude_env(task: str) -> dict:
    drop = ("CLAUDECODE", "CLAUDE_CODE_", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY")
    env = {k: v for k, v in os.environ.items() if not k.startswith(drop)}
    env["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token()
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] = "1"
    env["PATH"] = f"{sandbox_python(task).parent}:/usr/local/bin:/usr/bin:/bin:{Path.home() / '.local/bin'}"
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    env.pop("CONDA_PREFIX", None)
    return env


def isolation_check(init: dict | None) -> dict:
    """From the session's init event: anything beyond the built-in harness is a leak."""
    if not init:
        return {"init_seen": False, "ok": False}
    mcp = init.get("mcp_servers") or []
    plugins = init.get("plugins") or []
    tools = sorted(init.get("tools") or [])
    return {"init_seen": True, "ok": not mcp and not plugins, "mcp_servers": mcp, "plugins": plugins,
            "tools": tools, "cli_version": init.get("claude_code_version"), "model": init.get("model"),
            "api_key_source": init.get("apiKeySource")}


def run_claude(task: str, ws: Path, transcript: Path) -> dict:
    # Isolation without --bare (which accepts only API keys): no user/local settings (so no user
    # plugins, hooks or permission rules), hooks and auto-memory off, CLAUDE.md discovery off, no
    # MCP. The agent's context is Claude Code's built-in prompt + TASK.md, identical across arms.
    cmd = [CLAUDE_BIN, "-p", PROMPT, "--model", MODEL, "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project", "--settings", SESSION_SETTINGS,
           "--allowedTools", *ALLOWED, "--disallowedTools", *DISALLOWED,
           "--strict-mcp-config", "--no-session-persistence",
           "--max-budget-usd", str(ITER_BUDGET_USD)]
    t0 = time.time()
    with transcript.open("w") as fh:
        try:
            p = subprocess.run(cmd, cwd=ws, env=claude_env(task), stdout=fh, stderr=subprocess.STDOUT,
                               stdin=subprocess.DEVNULL, timeout=ITER_TIMEOUT_S)
            rc, timed_out = p.returncode, False
        except subprocess.TimeoutExpired:
            rc, timed_out = None, True
    meta = {"returncode": rc, "timed_out": timed_out, "wall_s": round(time.time() - t0, 1)}
    init = None
    for line in transcript.read_text(errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init" and init is None:
            init = ev
        if ev.get("type") == "result":
            meta.update({k: ev.get(k) for k in ("is_error", "num_turns", "total_cost_usd", "duration_ms")})
            meta["models"] = sorted((ev.get("modelUsage") or {}).keys())
            meta["result_excerpt"] = str(ev.get("result", ""))[:300]
    meta["isolation"] = isolation_check(init)
    return meta


def snapshot(ws: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for g in SNAP_GLOBS:
        for f in ws.glob(g):
            if f.name in ("evaluate.py", "dev_cases.json") or f.stat().st_size > SNAP_MAX_BYTES:
                continue
            shutil.copy(f, dest / f.name)


def read_report(ws: Path) -> dict:
    p = ws / "report.json"
    if not p.exists():
        return {"present": False, "estimated_pass_rate": None}
    try:
        r = json.loads(p.read_text())
        e = float(r.get("estimated_pass_rate"))
        return {"present": True, "estimated_pass_rate": e if 0.0 <= e <= 1.0 else None,
                "basis": str(r.get("basis", ""))[:500]}
    except Exception as ex:  # noqa: BLE001
        return {"present": True, "estimated_pass_rate": None, "parse_error": type(ex).__name__}


def own_eval(task: str, arm: str, ws: Path) -> dict:
    """Score on the loop's own measuring stick, computed by the harness (not self-reported)."""
    path = ws / ARM_CASES_FILE[arm]
    try:
        cases = json.loads(path.read_text())
        cases = [c for c in cases if isinstance(c, dict) and "args" in c and "expected" in c]
        for c in cases:
            c.setdefault("kwargs", {})
    except Exception as ex:  # noqa: BLE001
        return {"score": None, "n": 0, "error": f"unreadable:{type(ex).__name__}"}
    if not cases:
        return {"score": None, "n": 0, "error": "empty"}
    return score(task, ws / "solution.py", cases)


def last_hash() -> str:
    if not LEDGER.exists() or not LEDGER.read_text().strip():
        return "0" * 64
    return json.loads(LEDGER.read_text().strip().splitlines()[-1])["hash"]


def append_ledger(rec: dict) -> dict:
    """Append under an exclusive lock so concurrent runs keep one unbroken hash chain."""
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with (LEDGER.parent / ".ledger.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rec = {**rec, "prev_hash": last_hash()}
        rec["hash"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
        with LEDGER.open("a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def run(task: str, arm: str, rep: int, T: int, phase: str) -> None:
    rid = run_id(task, arm, rep)
    ws = WORK / "runs" / phase / rid / "ws"
    out = ROOT / "runs" / phase / rid
    init_workspace(task, arm, ws)
    held = load_cases(task, "heldout")
    dev = load_cases(task, "dev")
    dev_ref = DEV_DIR / f"{task}.json" if arm == "external" else None
    for t in range(1, T + 1):
        (ws / "TASK.md").write_text(task_md(TASKS[task], arm, t, T))
        (ws / "report.json").unlink(missing_ok=True)
        it = out / f"iter_{t}"
        it.mkdir(parents=True, exist_ok=True)
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        meta = run_claude(task, ws, it / "transcript.jsonl")
        snapshot(ws, it / "ws")
        rec = {
            "phase": phase, "run_id": rid, "task": task, "arm": arm, "rep": rep, "t": t, "T": T,
            "started_utc": started, "model_requested": MODEL, "claude": meta,
            "report": read_report(ws),
            "heldout": score(task, ws / "solution.py", held),
            "dev": score(task, ws / "solution.py", dev),
            "own": own_eval(task, arm, ws),
            "audit": audit_mod.audit(it / "transcript.jsonl", ws, TASKS[task].module, dev_ref),
            "solution_sha256": hashlib.sha256((ws / "solution.py").read_bytes()).hexdigest()
            if (ws / "solution.py").exists() else None,
        }
        iso = meta["isolation"]
        if not iso["ok"]:
            rec["audit"]["flags"]["isolation"] = [
                {k: iso.get(k) for k in ("init_seen", "mcp_servers", "plugins")}]
            rec["audit"]["violation"] = True
        rec = append_ledger(rec)
        print(json.dumps({k: rec[k] for k in ("run_id", "t")} | {
            "held": rec["heldout"]["score"], "own": rec["own"]["score"],
            "est": rec["report"]["estimated_pass_rate"], "viol": rec["audit"]["violation"],
            "wall_s": meta["wall_s"], "err": meta.get("is_error")}), flush=True)
        if meta.get("is_error") and t == 1 and not (ws / "report.json").exists():
            print(f"{rid}: claude error on first iteration, aborting run: {meta.get('result_excerpt')}")
            return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=list(TASKS))
    ap.add_argument("--arm", required=True, choices=["external", "self"])
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--T", type=int, default=5)
    ap.add_argument("--phase", default="main", choices=["pilot", "main"])
    a = ap.parse_args()
    run(a.task, a.arm, a.rep, a.T, a.phase)


if __name__ == "__main__":
    main()
