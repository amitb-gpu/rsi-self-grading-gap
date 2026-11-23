# Notes
Iter 1: changed train.py: data on GPU, bf16 autocast, batch 64, AdamW lr 2e-3 (betas .9/.95, wd .01), 5% warmup + cosine to 5%, grad clip 1, stop at budget-4s (train_s ~41).
Measured (evaluate.py, 2 of 4 runs used): seed1 1.6317, seed2 1.6390. Baseline official mean 2.0099 (not re-run by me).
Iter 2: model d=384, 6 layers, 6 heads (10.9M params), stop at budget-3s (train_s ~42), lr 2e-3. seed1 -> 1.6303 (iter1 small model seed1 1.6317: ~no gain). lr 1.2e-3 with this model -> 1.6663 (worse; try HIGHER lr e.g. 3e-3, untested). 2 eval runs used this iteration. Next: torch.compile, RoPE/RMSNorm, lr 3e-3, larger batch; bigger model alone is not helping (step-limited).
(Iter 1 next-list:) try bigger model/torch.compile, use remaining ~4s margin (train_s 41 of 45), RoPE/RMSNorm, tune lr/batch.
