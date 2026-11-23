Iter1: changed train.py: bf16 autocast, GPU-side batching, bs64, lr 2e-3 peak w/ warmup+time-based cosine, AdamW betas .95, clip 1.0.
Measured seed1: new 1.631 vs baseline 2.061 (baseline official mean 2.0099). Single runs only; noise ~±0.05.
Next: bigger/deeper model, torch.compile, tune lr/batch, SwiGLU/RoPE, eval-time tricks.
Iter2: tried model size only (seed1, single runs): d384/6L/6h -> 1.658; d256/6L -> 1.636; iter1 d256/4L -> 1.631 (official 1.634). No gain from size; reverted train.py to d256/4L (identical to iter1). Used 2 of 4 evals.
Next: torch.compile (watch compile time inside budget), RoPE/SwiGLU, batch/lr tuning, EMA of weights.
