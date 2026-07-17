#!/bin/sh
# Assemble the GitHub Pages site into docs/ (served from main:/docs).
# Run from the repository root. Requires pandoc.
set -e

cp data/output/lattice3d.html docs/explorer.html
cp data/output/paper.html docs/paper.html

pandoc docs/forward-predictions-2026.md -o docs/registry.html \
  --standalone --metadata title="LM-2026 Forward Prediction Registry" -c site.css
pandoc data/output/audit_report.md -o docs/audit.html \
  --standalone --metadata title="Historical Precision Audit" -c site.css
pandoc data/output/null_model_report.md -o docs/nullmodels.html \
  --standalone --metadata title="Null-Model Baseline Report" -c site.css

touch docs/.nojekyll
echo "site assembled in docs/"
