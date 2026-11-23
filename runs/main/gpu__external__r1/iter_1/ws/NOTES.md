Iter1: changed train.py: bf16 autocast, GPU-side batching, bs64, lr 2e-3 peak w/ warmup+time-based cosine, AdamW betas .95, clip 1.0.
Measured seed1: new 1.631 vs baseline 2.061 (baseline official mean 2.0099). Single runs only; noise ~±0.05.
Next: bigger/deeper model, torch.compile, tune lr/batch, SwiGLU/RoPE, eval-time tricks.
