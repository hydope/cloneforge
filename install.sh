#!/usr/bin/env bash
# CloneForge one-command install: venv + core deps + Piper test voices.
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e . numpy piper-tts

mkdir -p models
for v in amy lessac; do
  base="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/${v}/medium/en_US-${v}-medium"
  [ -f "models/en_US-${v}-medium.onnx" ] || curl -sL -o "models/en_US-${v}-medium.onnx" "${base}.onnx"
  [ -f "models/en_US-${v}-medium.onnx.json" ] || curl -sL -o "models/en_US-${v}-medium.onnx.json" "${base}.onnx.json"
done

echo "Installed. Try:"
echo "  .venv/bin/cloneforge doctor"
echo "  .venv/bin/cloneforge route --lang en --sample 8 --priority accuracy"
