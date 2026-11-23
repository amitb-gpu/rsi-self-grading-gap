Iter1: train.py changed: data on GPU, bf16 autocast, batch 64, lr 2e-3 peak w/ warmup+cosine (time-based), AdamW betas .9/.98, grad clip 1, fused.
Measured (seed 1, 2 of 4 evals used): new 1.6238 bpb; baseline 2.0556 bpb.
Next: try larger model (d=384, 6 layers), torch.compile, RoPE, batch size/lr sweep; train_s was 42 so budget margin could shrink.
Iter2: only 1 eval used. Changed model to d=384, 6 layers, 6 heads (10.9M params). Seed 1: 1.6209 bpb (train_s 42.0) vs iter1 1.6238 with d=256/4L: gain is within likely seed noise. Baseline 2.0556 is from iter1 (not re-measured).
Next: torch.compile, RoPE, batch/lr sweep, check seed variance (run seed 2).
