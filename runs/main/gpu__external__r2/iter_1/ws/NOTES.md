# Notes
Iter 1: changed train.py: data on GPU, bf16 autocast, batch 64, AdamW lr 2e-3 (betas .9/.95, wd .01), 5% warmup + cosine to 5%, grad clip 1, stop at budget-4s (train_s ~41).
Measured (evaluate.py, 2 of 4 runs used): seed1 1.6317, seed2 1.6390. Baseline official mean 2.0099 (not re-run by me).
Next: try bigger model/torch.compile, use remaining ~4s margin (train_s 41 of 45), RoPE/RMSNorm, tune lr/batch.
