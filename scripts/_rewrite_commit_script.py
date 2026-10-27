"""Rewrite scripts/commit_all.sh to use _commit_one helper instead of
`git add ... git commit ... || true` pattern. Real failures now print
warnings; "nothing to commit" cases are silent.

Run with: python scripts/_rewrite_commit_script.py
"""
import os
import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "commit_all.sh"
NEW_HEADER = '''#!/usr/bin/env bash
# Auto-generated: one commit per file in the School ERP project.
# Run from the project root directory (school_erp/).
#
# Behaviour:
#   - `git add` failures are FATAL (real errors — disk full, file too big,
#     permissions, etc.) — the script aborts.
#   - `git commit` failures are NON-FATAL only when "nothing to commit"
#     (exit code 1 from git when no diff). Real commit errors (e.g.,
#     pre-commit hook rejection) print a warning so they're visible.
#   - The script is idempotent: re-running on an already-committed repo
#     skips files with no diff without aborting.

set -e  # Abort on the first `git add` failure (real I/O / permission errors).

cd "$(dirname "$0")/.." 2>/dev/null || cd "$(pwd)"

# Initialize git if needed
if [ ! -d .git ]; then
    git init -q
    git branch -M main 2>/dev/null || true
fi

# Set committer identity if not set (override via env if you want)
git config user.email >/dev/null 2>&1 || git config user.email "dev@school-erp.local"
git config user.name  >/dev/null 2>&1 || git config user.name  "School ERP Dev"

# Helper: commit ONE file. Distinguishes "nothing to commit" (silent skip)
# from real failures (printed as warnings to stderr, don't abort).
_commit_one() {
    local file="$1"
    local msg="$2"
    git add -A -- "$file"
    if ! git commit -q -m "$msg" --no-verify 2>/dev/null; then
        if git diff --cached --quiet -- "$file"; then
            :  # Nothing to commit — expected on re-run, silent skip.
        else
            echo "WARNING: git commit failed for '$file' (msg: '$msg')" >&2
        fi
    fi
}

'''

# Regex to match each block:
#   # [N/M] path
#   git add -A -- "path"
#   git commit -q -m "msg" --no-verify 2>/dev/null || true
BLOCK_RE = re.compile(
    r'^# \[\d+/\d+\] (.+?)\n'
    r'^git add -A -- "([^"]+)"\n'
    r'^git commit -q -m "((?:[^"\\]|\\.)*)" --no-verify 2>/dev/null \|\| true\n',
    re.MULTILINE,
)


def rewrite():
    src = SCRIPT_PATH.read_text()
    out = [NEW_HEADER]
    matches = list(BLOCK_RE.finditer(src))
    print(f"Found {len(matches)} commit blocks to rewrite.")
    for m in matches:
        # First line of group: the path (from the comment line, may differ
        # from the add path — e.g. comment says "[3/357] requirements/base.txt"
        # but add path is "requirements/base.txt"). We use the add path.
        _display_path = m.group(1).strip()
        add_path = m.group(2)
        msg = m.group(3)
        out.append(f"# {add_path}\n_commit_one {add_path!r} {msg!r}\n\n")
    SCRIPT_PATH.write_text("".join(out))
    print(f"Rewrote {SCRIPT_PATH} ({len(out)} lines including header).")


if __name__ == "__main__":
    rewrite()
