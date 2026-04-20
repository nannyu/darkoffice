#!/usr/bin/env bash
set -euo pipefail

echo "== DarkOffice skill env check =="
echo "workspace: $(pwd)"

python3 --version
node --version
npm --version

echo "== Runtime checks =="
npm run -s skill:health > /dev/null
echo "skill:health ok"

echo "Environment check passed."
