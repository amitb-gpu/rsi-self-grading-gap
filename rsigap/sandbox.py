"""Per-task sandbox interpreters with the reference module removed.

Each sandbox is a hard-link copy of the bare `rsigap-sbx` conda env (same
CPython 3.12.7 build as the reference env) with the task's target module
source and bytecode deleted. The loop's `python3` resolves to this
interpreter, so CPython cannot be used as an oracle by importing it.

This is not a security boundary: the agent could still open the reference
source from another env with open(). That is forbidden by the instructions
and detected post hoc by rsigap.audit (see PREREGISTRATION.md, Deviations).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .tasks import TASKS

BASE_ENV = Path.home() / "miniforge3" / "envs" / "rsigap-sbx"
WORK = Path.home() / "rsigap-work"
SBX_DIR = WORK / "sbx"
STDLIB = Path("lib") / "python3.12"


def sandbox_python(task_name: str) -> Path:
    return SBX_DIR / task_name / "bin" / "python3"


def build(task_name: str) -> Path:
    task = TASKS[task_name]
    dest = SBX_DIR / task_name
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-al", str(BASE_ENV), str(dest)], check=True)
    for rel in task.blocked:
        src = dest / STDLIB / rel
        src.unlink()
        stem = Path(rel).stem
        for pyc in (src.parent / "__pycache__").glob(f"{stem}.*.pyc"):
            pyc.unlink()
    py = sandbox_python(task_name)
    probe = subprocess.run([str(py), "-I", "-c", f"import {task.module}"], capture_output=True)
    if probe.returncode == 0:
        raise RuntimeError(f"sandbox for {task_name} can still import {task.module}")
    return py


def build_all() -> None:
    for name in TASKS:
        print(name, build(name))


if __name__ == "__main__":
    build_all()
