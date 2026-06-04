#!/usr/bin/env python3
"""Validate that an ordinary CSP producer changed only append-safe files."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath


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


def run_check(args: list[str]) -> None:
    result = subprocess.run(
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def normalize(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix()


def changed_files() -> list[str]:
    files: set[str] = set()
    for args in (
        ["diff", "--name-only"],
        ["diff", "--name-only", "--cached"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        for line in run_git(args).splitlines():
            if line.strip():
                files.add(normalize(line.strip()))
    return sorted(files)


def is_allowed(path: str, project: str, session_id: str) -> bool:
    event_prefix = f"projects/{project}/events/"
    session_path = f"projects/{project}/sessions/{session_id}.md"
    return (
        path.startswith(event_prefix)
        and path.endswith(".md")
        and "/" not in path[len(event_prefix) :]
    ) or path == session_path


def allowed_write_specs(project: str, session_id: str = "<session-id>") -> list[str]:
    """Return the producer write surface in the same shape task packets use."""
    return [
        f"projects/{project}/events/*.md",
        f"projects/{project}/sessions/{session_id}.md",
    ]


def lint_changed_producer_files(paths: list[str]) -> None:
    markdown_paths = [
        path
        for path in paths
        if (
            path.endswith(".md")
            and (
                "/events/" in path
                or "/sessions/" in path
            )
            and Path(path).exists()
        )
    ]
    if not markdown_paths:
        return

    lint_script = Path(__file__).with_name("csp_lint.py")
    run_check([sys.executable, str(lint_script), "--strict", *markdown_paths])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check that producer changes touch only events and one session card."
    )
    parser.add_argument("--project", required=True, help="Project alias, for example csp-system.")
    parser.add_argument(
        "--session-id",
        required=True,
        help="Session card id without .md, for example 2026-05-08-codex-my-thread.",
    )
    args = parser.parse_args()

    changed = changed_files()
    forbidden = [
        path for path in changed if not is_allowed(path, args.project, args.session_id)
    ]

    if not forbidden:
        lint_changed_producer_files(changed)
        print("Producer changes are append-safe and lint-clean.")
        return

    print("Producer check failed. Ordinary chats may change only:", file=sys.stderr)
    print(f"- projects/{args.project}/events/*.md", file=sys.stderr)
    print(f"- projects/{args.project}/sessions/{args.session_id}.md", file=sys.stderr)
    print("", file=sys.stderr)
    print("Forbidden changes:", file=sys.stderr)
    for path in forbidden:
        print(f"- {path}", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
