Iter1: train.py changed: data on GPU, bf16 autocast, batch 64, lr 2e-3 peak w/ warmup+cosine (time-based), AdamW betas .9/.98, grad clip 1, fused.
Measured (seed 1, 2 of 4 evals used): new 1.6238 bpb; baseline 2.0556 bpb.
Next: try larger model (d=384, 6 layers), torch.compile, RoPE, batch size/lr sweep; train_s was 42 so budget margin could shrink.
