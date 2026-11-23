"""Train a recipe once and score it in bits per byte (bpb).

The harness runs the pristine copy of this file. Each workspace gets a copy as
`evaluate.py` with the split fixed to val; the harness hash-checks that copy.

  python evaluator.py --ws DIR --seed N [--split val|test] [--budget 45] [--data-dir D] [--out J]

Steps: take the GPU lock; import DIR/train.py; time train(data_dir, seed, budget, "cuda");
check causality; score bpb on fixed, evenly spaced 256-byte windows of the split.
A run is INVALID if train() raises, overruns budget + GRACE_S seconds, returns a non-causal
model, or produces non-finite loss. The harness scores invalid runs as 8.0 bpb (uniform).
"""
import argparse
import fcntl
import importlib.util
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path

GRACE_S = 10.0
CTX = 256
N_WINDOWS = 1024
LOCK = Path.home() / "rsigap-work" / "gpu.lock"


def load_train(ws, recipe="train.py"):
    sys.path.insert(0, str(ws))
    spec = importlib.util.spec_from_file_location("train_under_test", str(Path(ws) / recipe))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.train


def windows(np, data):
    starts = np.linspace(0, len(data) - CTX - 2, N_WINDOWS).astype(np.int64)
    return np.stack([data[s:s + CTX + 1] for s in starts]).astype(np.int64)


def causal_ok(torch, model, w):
    x = torch.from_numpy(w[:8, :CTX]).cuda()
    x2 = x.clone()
    g = torch.Generator(device="cpu").manual_seed(0)
    x2[:, CTX // 2:] = torch.randint(0, 256, (8, CTX - CTX // 2), generator=g).cuda()
    with torch.no_grad():
        a = model(x).float()[:, :CTX // 2]
        b = model(x2).float()[:, :CTX // 2]
    return bool(((a - b).abs().max() <= 1e-2 * (1 + a.abs().max())).item())


def bpb(torch, model, w):
    F = torch.nn.functional
    tot, n = 0.0, 0
    with torch.no_grad():
        for i in range(0, len(w), 64):
            chunk = torch.from_numpy(w[i:i + 64]).cuda()
            logits = model(chunk[:, :CTX]).float()
            loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), chunk[:, 1:].reshape(-1), reduction="sum")
            tot += loss.item()
            n += chunk[:, 1:].numel()
    return tot / n / math.log(2)


def run(ws, seed, split, budget, data_dir, eval_file=None, recipe="train.py"):
    import numpy as np
    import torch
    out = {"seed": seed, "split": split, "budget_s": budget, "recipe": recipe, "valid": False}
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            train = load_train(ws, recipe)
            torch.cuda.synchronize()
            t0 = time.time()
            model = train(str(data_dir), seed, budget, "cuda")
            torch.cuda.synchronize()
            out["train_s"] = round(time.time() - t0, 2)
            model.eval()
            out["n_params"] = sum(p.numel() for p in model.parameters())
            fname = {"val": "val.bin", "test": "test.bin"}[split]
            data = np.fromfile(eval_file or os.path.join(data_dir, fname), dtype=np.uint8)
            w = windows(np, data)
            out["causal"] = causal_ok(torch, model, w)
            out["bpb"] = bpb(torch, model, w)
            out["overrun"] = out["train_s"] > budget + GRACE_S
            out["valid"] = out["causal"] and not out["overrun"] and math.isfinite(out["bpb"])
        except Exception as e:  # noqa: BLE001
            out["error"] = f"{type(e).__name__}: {e}"[:500]
            out["traceback"] = traceback.format_exc()[-2000:]
        finally:
            torch.cuda.empty_cache()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", default=".")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--split", default="val", choices=["val", "test"])
    ap.add_argument("--budget", type=float, default=45.0)
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--recipe", default="train.py", help="recipe file in --ws to train (e.g. baseline_train.py)")
    ap.add_argument("--eval-file", default=None, help="harness only: score this file instead of data-dir/<split>.bin")
    a = ap.parse_args()
    # Agent-side cap and log: set by the harness for the agent's session only.
    log, cap = os.environ.get("RSIGAP_EVAL_LOG"), int(os.environ.get("RSIGAP_MAX_EVALS", "0") or 0)
    if log and cap:
        used = len(Path(log).read_text().splitlines()) if Path(log).exists() else 0
        if used >= cap:
            print(json.dumps({"refused": f"evaluation limit reached ({cap} per iteration)"}))
            return
    data_dir = a.data_dir or str(Path(a.ws) / "data")
    if Path(a.recipe).name != a.recipe:
        print(json.dumps({"refused": "--recipe must be a file name in the workspace"}))
        return
    res = run(Path(a.ws).resolve(), a.seed, a.split, a.budget, data_dir, a.eval_file, a.recipe)
    if a.out:
        Path(a.out).write_text(json.dumps(res))
    if log and cap:
        with open(log, "a") as f:
            f.write(json.dumps({k: v for k, v in res.items() if k != "traceback"}) + "\n")
    shown = {k: v for k, v in res.items() if k != "traceback"}
    print(json.dumps(shown))
    if "traceback" in res:
        print(res["traceback"], file=sys.stderr)


if __name__ == "__main__":
    main()
