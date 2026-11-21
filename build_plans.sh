#!/bin/sh
# Rebuild the four woodworking plans: models and HTML (Python), PDFs and page pictures (one Chromium, closed
# right away), then PDF metadata. Playwright is looked up through NODE_PATH.
set -e
cd "$(dirname "$0")"
for d in sauna-hat-peg-rail:peg_rail.py sauna-bench-headrest:headrest.py sauna-bench-backrest:backrest.py sauna-bucket-stand:bucket_stand.py; do
  (cd "${d%%:*}" && python3 "${d##*:}")
done
flock /tmp/freebies-chromium.lock env NODE_PATH="${PLAYWRIGHT_NODE_PATH:-/opt/carmax/node_modules}" \
  node render_plans.js sauna-hat-peg-rail sauna-bench-headrest sauna-bench-backrest sauna-bucket-stand
python3 - <<'PY'
import dvx_plans as dp
for d, t, s in [
    ("sauna-hat-peg-rail", "Peg rail for sauna hats and towels", "Woodworking plan with a drilling template"),
    ("sauna-bench-headrest", "Sauna bench headrest", "Woodworking plan with a full-size side template"),
    ("sauna-bench-backrest", "Sauna bench backrest", "Woodworking plan"),
    ("sauna-bucket-stand", "Sauna bucket stand", "Woodworking plan with a full-size runner template")]:
    dp.finalize_pdf(f"{d}/{d}-plan.pdf", f"{t} - DIVELUX plan", s, "sauna, woodworking, plan, DIVELUX")
    print("metadata:", d)
PY
