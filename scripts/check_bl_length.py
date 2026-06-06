#!/usr/bin/env python3
"""Warn when BL clauses in a spec exceed the recommended sentence count.

The Maui SDD convention is one declarative sentence per `BL-XXX` / `DQ-XXX`
clause. Embedded rationale, cross-references, and code hand-holding belong in
the change log or `DV-XXX` rows, not the clause itself. See
`knowledge/standards/sdd-conventions.md` § Tightening.

This script flags any clause whose body exceeds `--max-sentences` (default 2).
It's a warning, not a hard error, so authors can choose to leave a longer
clause when there's no clean way to split.

Usage:
    python check_bl_length.py [--specs-dir specs] [--max-sentences 2] [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Matches the opening line of a BL/DQ clause. Tolerates both `**BL-001:**` and
# `**BL-001**:` forms (colon inside or outside the bold).
CLAUSE_OPENING = re.compile(
    r"""
    ^\s*-\s+                            # bullet
    \*\*(?P<id>(?:BL|DQ)-\d{3,4})       # **BL-001
    [:\.]?\*\*                          # optional `:` then closing `**`
    [:\.]?\s*                           # optional outside `:` and ws
    (?P<first>.*)$                      # rest of the opening line
    """,
    re.VERBOSE,
)

# Crude sentence splitter: terminating punctuation followed by whitespace +
# uppercase, or end of string. Doesn't try to handle e.g., i.e., etc. — false
# positives push the author to rewrite, which is the desired outcome.
SENTENCE_END = re.compile(r"[.!?](?:\s+(?=[A-Z])|\s*$)")


def count_sentences(body: str) -> int:
    """Return a sentence count for a clause body."""
    cleaned = body.strip()
    if not cleaned:
        return 0
    matches = list(SENTENCE_END.finditer(cleaned))
    return max(len(matches), 1)


def iter_clauses(text: str):
    """Yield (id, body) pairs for each BL/DQ clause in the spec text.

    A clause body runs from the opening line until the next blank line, the
    next clause opening, or a sub-bullet (line starting with two-space-then-`-`).
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = CLAUSE_OPENING.match(lines[i])
        if not m:
            i += 1
            continue
        clause_id = m.group("id")
        body_parts = [m.group("first").strip()]
        i += 1
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                break
            if CLAUSE_OPENING.match(line):
                break
            if re.match(r"^\s+-\s", line):  # sub-bullet (code pointer, etc.)
                break
            body_parts.append(line.strip())
            i += 1
        yield clause_id, " ".join(p for p in body_parts if p)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs-dir", default="specs", help="Path to specs directory (default: specs)")
    parser.add_argument(
        "--max-sentences",
        type=int,
        default=2,
        help="Warn if a clause exceeds this many sentences (default: 2)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when warnings are found (default: warnings only)",
    )
    args = parser.parse_args()

    specs_dir = Path(args.specs_dir).resolve()
    if not specs_dir.exists():
        print(f"No specs directory at {specs_dir} — skipping BL-length check.")
        return 0

    warnings: list[str] = []
    total_clauses = 0
    for spec_file in sorted(specs_dir.rglob("*.md")):
        text = spec_file.read_text(encoding="utf-8")
        for clause_id, body in iter_clauses(text):
            total_clauses += 1
            sentences = count_sentences(body)
            if sentences > args.max_sentences:
                try:
                    rel = spec_file.relative_to(Path.cwd())
                except ValueError:
                    rel = spec_file
                warnings.append(f"  {rel}: {clause_id} runs {sentences} sentences (max {args.max_sentences})")

    if warnings:
        print(f"\n{len(warnings)} clause(s) exceed the sentence budget:\n")
        for line in warnings:
            print(line)
        print(
            "\nTighten by moving embedded rationale to the change log or a DV row, "
            "and removing duplicate cross-references. See "
            "`knowledge/standards/sdd-conventions.md` § Tightening."
        )
        return 1 if args.strict else 0

    print(f"OK: {total_clauses} clause(s) checked across {specs_dir.name}/; all within {args.max_sentences} sentences.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
