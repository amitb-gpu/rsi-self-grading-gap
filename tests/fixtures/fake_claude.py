#!/usr/bin/env python3
"""Stand-in for `claude -p` in plumbing tests: writes a partial solution, self cases, report."""
import json, os
from pathlib import Path
ws = Path.cwd()
assert "TASK.md" in os.listdir(ws)
(ws / "solution.py").write_text("def solve(s, comments=False, posix=True):\n    return s.split()\n")
if (ws / "self_cases.json").exists():
    (ws / "self_cases.json").write_text(json.dumps([
        {"args": ["a b"], "kwargs": {}, "expected": ["a", "b"]},
        {"args": ["'a b'"], "kwargs": {}, "expected": ["'a", "b'"]},  # wrong label, solution agrees
    ]))
(ws / "NOTES.md").write_text("iter done\n")
(ws / "report.json").write_text(json.dumps({"estimated_pass_rate": 0.9, "basis": "fake"}))
assert os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") and not os.environ.get("ANTHROPIC_API_KEY")
print(json.dumps({"type": "system", "subtype": "init", "mcp_servers": [], "plugins": [],
                  "tools": ["Read", "Write", "Edit", "Bash"], "claude_code_version": "fake",
                  "model": "fake", "apiKeySource": "none"}))
print(json.dumps({"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Write", "input": {"file_path": str(ws / "solution.py")}}]}}))
print(json.dumps({"type": "result", "is_error": False, "num_turns": 1, "total_cost_usd": 0,
                  "duration_ms": 1, "modelUsage": {"fake": {}}, "result": "ok"}))
