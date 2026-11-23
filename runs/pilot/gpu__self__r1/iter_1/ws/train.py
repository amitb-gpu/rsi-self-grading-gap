"""Baseline training recipe: a small byte-level GPT on enwik8.

Contract (enforced by evaluate.py / the harness):
    train(data_dir: str, seed: int, budget_s: float, device: str) -> torch.nn.Module
The returned model maps a LongTensor of byte ids [B, T] (T <= 256) to logits [B, T, 256],
must be causal (logits at position t depend only on bytes <= t), and train() must return
within budget_s seconds of wall-clock time. Train only on data_dir/train.bin.
"""
import math
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

CTX = 256


class Block(nn.Module):
    def __init__(self, d, n_head):
        super().__init__()
        self.n_head = n_head
        self.ln1 = nn.LayerNorm(d)
        self.qkv = nn.Linear(d, 3 * d)
        self.proj = nn.Linear(d, d)
        self.ln2 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d))

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(C, dim=2)
        q, k, v = (t.view(B, T, self.n_head, C // self.n_head).transpose(1, 2) for t in (q, k, v))
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.proj(y.transpose(1, 2).contiguous().view(B, T, C))
        return x + self.mlp(self.ln2(x))


class ByteGPT(nn.Module):
    def __init__(self, d=256, n_layer=4, n_head=4):
        super().__init__()
        self.tok = nn.Embedding(256, d)
        self.pos = nn.Embedding(CTX, d)
        self.blocks = nn.ModuleList(Block(d, n_head) for _ in range(n_layer))
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, 256, bias=False)

    def forward(self, idx):
        T = idx.shape[1]
        x = self.tok(idx) + self.pos(torch.arange(T, device=idx.device))
        for b in self.blocks:
            x = b(x)
        return self.head(self.ln(x))


def train(data_dir, seed, budget_s, device):
    t0 = time.time()
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    data = np.memmap(os.path.join(data_dir, "train.bin"), dtype=np.uint8, mode="r")
    model = ByteGPT().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=0.05, betas=(0.9, 0.98), fused=True)
    batch = 64
    peak, warm = 2e-3, 100
    T_end = budget_s - 3.0
    cmodel = torch.compile(model)
    model.train()
    step = 0
    tl = time.time()
    while True:
        el = time.time() - t0
        if el >= T_end:
            break
        frac = el / T_end
        lr = peak * min(1.0, (step + 1) / warm) * (0.05 + 0.95 * 0.5 * (1 + math.cos(math.pi * frac)))
        for g in opt.param_groups:
            g["lr"] = lr
        ix = rng.integers(0, len(data) - CTX - 1, size=batch)
        x = torch.from_numpy(np.stack([data[i:i + CTX] for i in ix]).astype(np.int64)).to(device)
        y = torch.from_numpy(np.stack([data[i + 1:i + 1 + CTX] for i in ix]).astype(np.int64)).to(device)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = F.cross_entropy(cmodel(x).float().view(-1, 256), y.view(-1))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        step += 1
    torch.cuda.synchronize()
    model.eval()
    return model
