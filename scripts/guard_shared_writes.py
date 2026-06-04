#!/usr/bin/env python3
"""Fail when non-consolidator commits change shared CSP projection files."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import PurePosixPath


SHARED_CONTEXT_FILES = (
    "GLOBAL_INDEX",
    "GITHUB_ATLAS",
    "REPOSITORY_REGISTRY",
    "KNOWLEDGE_ROUTING",
    "REPOSITORY_REQUESTS",
    "ROADMAP",
)

SHARED_PROJECT_FILES = (
    "RUNTIME",
    "ROADMAP",
    "DECISIONS",
    "CONFLICTS",
    "THREADS",
    "KNOWLEDGE_SOURCES",
    "REPOSITORY_STATUS",
)

SHARED_FILE_PATTERNS = (
    re.compile(
        rf"^context/({'|'.join(SHARED_CONTEXT_FILES)})\.md$"
    ),
    re.compile(
        rf"^projects/[^/]+/({'|'.join(SHARED_PROJECT_FILES)})\.md$"
    ),
)

CONSOLIDATOR_MARKERS = (
    "csp-consolidator: true",
    "canonical consolidator",
    "consolidate",
    "consolidation",
)


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def normalize(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix()


def is_shared_file(path: str) -> bool:
    normalized = normalize(path)
    return any(pattern.match(normalized) for pattern in SHARED_FILE_PATTERNS)


def shared_file_specs(project: str = "*") -> list[str]:
    """Return human-readable shared-file specs for task packet boundaries."""
    return [
        *(f"context/{name}.md" for name in SHARED_CONTEXT_FILES),
        *(f"projects/{project}/{name}.md" for name in SHARED_PROJECT_FILES),
    ]


def changed_files(base: str, head: str) -> list[str]:
    output = run_git(["diff", "--name-only", "--diff-filter=ACMRTUXB", base, head])
    return [normalize(line.strip()) for line in output.splitlines() if line.strip()]


def commit_messages(base: str, head: str) -> str:
    return run_git(["log", "--format=%B", f"{base}..{head}"]).lower()


def has_consolidator_marker(base: str, head: str) -> bool:
    if os.environ.get("CSP_ALLOW_SHARED_WRITES", "").lower() in {"1", "true", "yes"}:
        return True

    messages = commit_messages(base, head)
    return any(marker in messages for marker in CONSOLIDATOR_MARKERS)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check that shared CSP files are changed only by consolidator commits."
    )
    parser.add_argument("base", help="Base git revision.")
    parser.add_argument("head", help="Head git revision.")
    args = parser.parse_args()

    shared_changes = [path for path in changed_files(args.base, args.head) if is_shared_file(path)]
    if not shared_changes:
        print("No shared CSP projection files changed.")
        return

    if has_consolidator_marker(args.base, args.head):
        print("Shared CSP projection files changed by a consolidator-marked commit.")
        return

    print("Shared CSP projection files changed without a consolidator marker:", file=sys.stderr)
    for path in shared_changes:
        print(f"- {path}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Producer chats may write only events and their own session card.", file=sys.stderr)
    print(
        "Use a commit message containing 'Consolidate' or trailer 'CSP-Consolidator: true' "
        "only for canonical consolidation commits.",
        file=sys.stderr,
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
