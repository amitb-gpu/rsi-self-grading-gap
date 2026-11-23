Iter1: train.py now uses GPU-resident data, bf16 autocast, batch 64, AdamW lr 2e-3 (betas .9/.95) with warmup + cosine to 5%, grad clip 1, fused. Same model.
Measured (seed 1, 1 run each): new 1.629 bpb, baseline 2.052. 2 of 4 evaluate calls used.
Next: bigger/wider model or more layers, torch.compile, tune lr/batch, RoPE/RMSNorm, ensure train_s stays <45.
