#!/usr/bin/env bash
# Run all CPU (Category A) OzCore artifact launchers.
set -euo pipefail
ART="${1:-./ozcore-artifact}"
cd "$ART"
for s in tab2 tab4 tab5 tab6 fig2 fig3 fig5 fig10 fig11-12 fig13 fig14-15 fig16; do
  echo "===== $s"
  bash "scripts/$s.sh"
done
