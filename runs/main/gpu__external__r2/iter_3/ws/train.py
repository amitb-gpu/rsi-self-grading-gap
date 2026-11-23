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
    def __init__(self, d=384, n_layer=6, n_head=6):
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
    data = torch.from_numpy(np.fromfile(os.path.join(data_dir, "train.bin"), dtype=np.uint8)).to(device).long()
    model = ByteGPT().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=0.01, betas=(0.9, 0.95), fused=True)
    LR = 2e-3
    batch = 64
    total = budget_s - 3.0
    ar = torch.arange(CTX + 1, device=device)
    model.train()
    while True:
        el = time.time() - t0
        if el >= total:
            break
        p = el / total
        lr = LR * min(1.0, (p + 1e-9) / 0.05) * (0.05 + 0.95 * 0.5 * (1 + math.cos(math.pi * p)))
        for g in opt.param_groups:
            g["lr"] = lr
        ix = torch.randint(0, len(data) - CTX - 1, (batch,), device=device)
        w = data[ix[:, None] + ar]
        x, y = w[:, :-1], w[:, 1:]
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits = model(x)
        loss = F.cross_entropy(logits.float().view(-1, 256), y.reshape(-1))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    torch.cuda.synchronize()
    model.eval()
    return model
