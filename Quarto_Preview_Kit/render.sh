#!/usr/bin/env bash
set -e
infile="${1:-in/sample.tex}"
base="$(basename "$infile" .tex)"
outfile="out/${base}.html"

if command -v quarto >/dev/null 2>&1; then
  echo "Using Quarto…"
  quarto render "$infile" \
    --to html \
    --output "$outfile" \
    --filters env-to-callout.lua \
    --css preview.css \
    --css rtl-baseline.css \
    --css styles.css || true
elif command -v pandoc >/dev/null 2>&1; then
  echo "Using Pandoc…"
  pandoc "$infile" -o "$outfile" \
    --standalone --mathjax \
    --lua-filter=env-to-details.lua \
    -M lang=he -M dir=rtl \
    --css=preview.css \
    --css=rtl-baseline.css \
    --css=styles.css
else
  echo "Install Quarto or Pandoc to preview."
  exit 1
fi
echo "Done → $outfile"
