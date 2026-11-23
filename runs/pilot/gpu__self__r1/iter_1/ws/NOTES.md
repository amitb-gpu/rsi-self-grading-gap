# Notes
Iter 1: changed baseline to lr 2e-3 (warmup 100, cosine to 5%), betas (.9,.98), wd .05, batch 64,
bf16 autocast, torch.compile, fused AdamW, grad clip 1.0, stop at budget-3s.
Measured: 1 evaluate.py run, seed 1 -> val bpb 1.6967 (train_s 42.0, valid).
NOT measured: the original baseline (my attempt to run it was blocked; the baseline number in report.json is a guess).
Next: measure baseline for real; try larger model/more layers (d=384), RMSNorm/RoPE, tune lr/batch, use the extra ~2s of budget (compile time counts).
