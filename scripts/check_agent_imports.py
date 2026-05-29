#!/usr/bin/env python3
"""Validate that `@./.maui/...` imports in AGENT examples resolve to real files.

The README.md and various runbooks contain example `AGENT.md` blocks that show
consuming repos how to import shared standards from the `.maui` submodule. If
those paths drift (file renamed, moved, deleted) the examples silently break in
every consumer repo. This script parses the example blocks and verifies every
referenced file exists.

Run locally:
    python scripts/check_agent_imports.py

Or in CI via `.github/workflows/imports-check.yml`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files that may contain `@./.maui/...` example import lines. Add more as new
# files appear that document the import pattern.
FILES_TO_CHECK = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "knowledge" / "AGENT.base.md",
    REPO_ROOT / "knowledge" / "runbooks" / "tamanu-dbt-setup.md",
    REPO_ROOT / "knowledge" / "runbooks" / "onboarding-checklist.md",
]

# Match lines like:
#   @./.maui/knowledge/standards/dbt-conventions.md
#   @./.maui/knowledge/architecture/data-architecture.md
IMPORT_PATTERN = re.compile(r"@\./\.maui/(?P<path>[\w./\-]+)")


def find_imports(text: str) -> list[str]:
    """Return all distinct `@./.maui/<path>` references in the text."""
    return sorted({m.group("path") for m in IMPORT_PATTERN.finditer(text)})


def main() -> int:
    missing: list[tuple[Path, str]] = []
    checked = 0

    for source_file in FILES_TO_CHECK:
        if not source_file.exists():
            print(f"WARN: source file not present: {source_file.relative_to(REPO_ROOT)}")
            continue

        text = source_file.read_text(encoding="utf-8")
        imports = find_imports(text)
        for imp in imports:
            checked += 1
            target = REPO_ROOT / imp
            if not target.exists():
                missing.append((source_file, imp))

    if missing:
        print(f"\n{len(missing)} broken import(s) found:\n")
        for source_file, imp in missing:
            rel = source_file.relative_to(REPO_ROOT)
            print(f"  {rel}: @./.maui/{imp}  ->  does not exist")
        print(
            "\nFix by either: (a) restoring the file at the referenced path, "
            "or (b) updating the example to point at the new path."
        )
        return 1

    print(f"OK: {checked} `@./.maui/...` import(s) checked across {len(FILES_TO_CHECK)} files; all resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
