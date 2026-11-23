Iter1: train.py now uses GPU-resident data, bf16 autocast, batch 64, AdamW lr 2e-3 (betas .9/.95) with warmup + cosine to 5%, grad clip 1, fused. Same model.
Measured (seed 1, 1 run each): new 1.629 bpb, baseline 2.052. 2 of 4 evaluate calls used.
Next: bigger/wider model or more layers, torch.compile, tune lr/batch, RoPE/RMSNorm, ensure train_s stays <45.
Iter2: tried d=384, 6 layers, 6 heads (10.9M params): seed1 bpb 1.638 (slightly worse than 1.629 for 256/4; too few steps in 45s). Reverted to 256/4 (train.py identical to iter1). 1 eval call used this iter.
Next: torch.compile for throughput, RMSNorm/RoPE, lr/batch tuning; bigger model doesn't pay without speedups.
Iter3: first eval (sed was denied, train.py unchanged) reproduced iter1: 1.6295 seed1. Then batch 128, peak lr 3e-3: seed1 1.599. 2 of 4 evals used. Baseline ~2.052 (iter1 measurement, not re-measured).
Next: try batch 256/lr 4e-3, torch.compile, RMSNorm/RoPE; only one seed measured so far.
