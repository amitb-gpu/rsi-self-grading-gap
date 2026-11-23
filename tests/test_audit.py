import json

from rsigap.audit import audit, imports_module


def test_imports_module_routes():
    assert imports_module("import shlex", "shlex")
    assert imports_module("from urllib import parse", "urllib.parse")
    assert imports_module("import urllib.parse as up", "urllib.parse")
    assert imports_module("import importlib\nimportlib.import_module('email.utils')", "email.utils")
    assert imports_module("x = __import__('ipaddress')", "ipaddress")
    assert not imports_module("import re\n# shlex behaviour\ns = 'shlex'", "shlex")
    assert not imports_module("import re", "fnmatch")


def _transcript(tmp_path, uses):
    lines = [json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": n, "input": i} for n, i in uses]}})]
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join(lines))
    return p


def test_audit_flags(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "solution.py").write_text("import re\n")
    t = _transcript(tmp_path, [
        ("Read", {"file_path": str(ws / "NOTES.md")}),
        ("Bash", {"command": "python3 evaluate.py solution.py self_cases.json"}),
    ])
    assert not audit(t, ws, "shlex", None)["violation"]
    t = _transcript(tmp_path, [
        ("Read", {"file_path": "/home/manager/miniforge3/envs/rsigap/lib/python3.12/shlex.py"}),
        ("Bash", {"command": "python3 -c \"print(open('../../x').read())\""}),
        ("Grep", {"pattern": "shlex"}),
    ])
    f = audit(t, ws, "shlex", None)["flags"]
    assert f["path_outside_ws"] and f["bash_outside_ws"] and f["disallowed_tool"]
