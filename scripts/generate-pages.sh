#!/usr/bin/env bash
# Generate and deploy Guardian dashboard to GitHub Pages
set -euo pipefail

guardian generate-pages --audit-dir ~/.guardian/audit --output ./_pages
git checkout gh-pages 2>/dev/null || git checkout --orphan gh-pages
cp -r _pages/* .
git add .
git commit -m "Update dashboard [skip ci]"
git push origin gh-pages
