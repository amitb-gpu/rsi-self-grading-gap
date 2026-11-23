#!/usr/bin/env bash
# v0.2 main phase: sequential (one GPU), preregistered order. Refuses to start unless frozen.
set -euo pipefail
cd "$(dirname "$0")/.."
git tag --list prereg-gpu-frozen | grep -q . || { echo "prereg v0.2 not frozen"; exit 1; }
PY=~/miniforge3/envs/rsigap/bin/python
for spec in "self 1" "external 1" "external 2" "self 2"; do
  set -- $spec
  $PY -m rsigap.gpu.loop_gpu --arm "$1" --rep "$2" --T 3 --phase main 2>&1 | tee -a runs/logs/gpu_main.log
done
$PY -m rsigap.gpu.analyze_gpu main
