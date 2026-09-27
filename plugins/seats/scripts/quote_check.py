#!/usr/bin/env python3
"""Check that a quote appears verbatim in the source texts, ignoring line breaks and runs of spaces.
Usage: python3 quote_check.py "the quote"   -> prints FOUND <file> or NOT FOUND. Exit code 0 if found."""
import sys, re, pathlib
def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()
q = norm(" ".join(sys.argv[1:]))
hits = [p.name for p in sorted(pathlib.Path(__file__).parent.glob("*.txt")) if q in norm(p.read_text())]
print("FOUND " + ", ".join(hits) if hits else "NOT FOUND")
sys.exit(0 if hits else 1)
