#!/usr/bin/env python3
"""Read-only lint checks for source-backed knowledge repositories."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath


EXCLUDED_DIRS = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "build",
    "dist",
}

INDEX_NAME_RE = re.compile(
    r"(README|INDEX|STATUS|MAP|REGISTRY|LOG|BACKLOG|WORKFLOW|RULES|AUDIT|COVERAGE)",
    re.IGNORECASE,
)
STATUS_RE = re.compile(
    r"(^|\n)(status\s*:|Status\s*:|\u0421\u0442\u0430\u0442\u0443\u0441\s*:)",
    re.IGNORECASE,
)
SOURCE_RE = re.compile(
    r"(source|sources|source_id|provenance|csp_event|csp event|"
    r"\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a)",
    re.IGNORECASE,
)
SOURCE_ID_RE = re.compile(r"(?im)^\s*(source_id|Source ID)\s*:\s*([A-Za-z0-9_.:-]+)\s*$")
DATE_RE = re.compile(
    r"(?im)^\s*(date|updated|last verified|imported on|retrieval date)\s*:\s*(\d{4}-\d{2}-\d{2})\s*$"
)
CSP_EVENT_RE = re.compile(r"(csp_event|CSP Event|csp event|projects/.+/events/.+\.md)", re.IGNORECASE)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)|`([^`]+\.md)`")


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    detail: str


def normalize(path: Path | str) -> str:
    return PurePosixPath(str(path).replace("\\", "/")).as_posix()


def run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def is_git_repo(repo: Path) -> bool:
    result = run_git(repo, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def iter_markdown(repo: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo.rglob("*.md"):
        rel_parts = path.relative_to(repo).parts
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        files.append(path)
    return sorted(files)


def git_changed_markdown(repo: Path, base: str) -> list[Path]:
    if not is_git_repo(repo):
        return []

    files: set[str] = set()
    commands = (
        ["diff", "--name-only", f"{base}...HEAD"],
        ["diff", "--name-only"],
        ["diff", "--name-only", "--cached"],
        ["ls-files", "--others", "--exclude-standard"],
    )
    for command in commands:
        result = run_git(repo, command)
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            rel = line.strip()
            if rel.lower().endswith(".md"):
                files.add(normalize(rel))

    paths = [repo / rel for rel in sorted(files)]
    return [path for path in paths if path.exists()]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def collect_links(repo: Path, files: list[Path]) -> set[str]:
    links: set[str] = set()
    for path in files:
        if not INDEX_NAME_RE.search(path.name):
            continue
        base = path.parent
        for match in MD_LINK_RE.finditer(read_text(path)):
            raw = match.group(1) or match.group(2) or ""
            raw = raw.split("#", 1)[0]
            if raw.startswith(("http://", "https://", "mailto:")):
                continue
            target = (base / raw).resolve()
            try:
                links.add(normalize(target.relative_to(repo.resolve())))
            except ValueError:
                links.add(normalize(raw))
    return links


def is_control_doc(path: Path) -> bool:
    return INDEX_NAME_RE.search(path.name) is not None or "00_META" in path.parts


def stale_dates(text: str, stale_days: int, today: dt.date) -> list[str]:
    stale: list[str] = []
    for label, value in DATE_RE.findall(text):
        try:
            date_value = dt.date.fromisoformat(value)
        except ValueError:
            continue
        age = (today - date_value).days
        if age > stale_days:
            stale.append(f"{label}: {value} is {age} days old")
    return stale


def lint_file(
    repo: Path,
    path: Path,
    linked_paths: set[str],
    changed_paths: set[str],
    stale_days: int,
    today: dt.date,
) -> list[Finding]:
    rel = normalize(path.relative_to(repo))
    text = read_text(path)
    findings: list[Finding] = []

    if not STATUS_RE.search(text):
        findings.append(Finding("warning", "missing_status", rel, "No status marker found."))

    if not SOURCE_RE.search(text) and not is_control_doc(path):
        findings.append(
            Finding("warning", "missing_source", rel, "No obvious source/provenance marker found.")
        )

    if not is_control_doc(path) and rel not in linked_paths:
        findings.append(
            Finding("info", "possible_orphan", rel, "File is not linked from an obvious index/map/status file.")
        )

    for detail in stale_dates(text, stale_days=stale_days, today=today):
        findings.append(Finding("info", "stale_date", rel, detail))

    if rel in changed_paths and not CSP_EVENT_RE.search(text):
        findings.append(
            Finding(
                "warning",
                "missing_csp_event_reference",
                rel,
                "Changed file has no obvious CSP event reference.",
            )
        )

    return findings


def find_duplicate_source_ids(repo: Path, files: list[Path]) -> list[Finding]:
    seen: dict[str, str] = {}
    findings: list[Finding] = []
    for path in files:
        rel = normalize(path.relative_to(repo))
        for _, source_id in SOURCE_ID_RE.findall(read_text(path)):
            if source_id in seen:
                findings.append(
                    Finding(
                        "error",
                        "duplicate_source_id",
                        rel,
                        f"Source ID also appears in {seen[source_id]}.",
                    )
                )
            else:
                seen[source_id] = rel
    return findings


def build_report(repo: Path, args: argparse.Namespace) -> dict[str, object]:
    all_files = iter_markdown(repo)
    changed_files = git_changed_markdown(repo, args.base)
    files = changed_files if args.changed_only else all_files
    linked_paths = collect_links(repo, all_files)
    changed_paths = {normalize(path.relative_to(repo)) for path in changed_files}
    today = dt.date.today()

    findings: list[Finding] = []
    for path in files:
        findings.extend(
            lint_file(
                repo=repo,
                path=path,
                linked_paths=linked_paths,
                changed_paths=changed_paths,
                stale_days=args.stale_days,
                today=today,
            )
        )
    findings.extend(find_duplicate_source_ids(repo, all_files))

    if args.max_findings >= 0:
        visible_findings = findings[: args.max_findings]
    else:
        visible_findings = findings

    counts = {
        "error": sum(1 for finding in findings if finding.severity == "error"),
        "warning": sum(1 for finding in findings if finding.severity == "warning"),
        "info": sum(1 for finding in findings if finding.severity == "info"),
    }

    return {
        "repository": str(repo),
        "repo_alias": args.repo_alias,
        "mode": "changed-only" if args.changed_only else "full",
        "files_scanned": len(files),
        "changed_markdown_files": len(changed_files),
        "findings_total": len(findings),
        "counts": counts,
        "findings": [asdict(finding) for finding in visible_findings],
        "truncated": len(visible_findings) < len(findings),
    }


def render_text(report: dict[str, object]) -> str:
    counts = report["counts"]
    assert isinstance(counts, dict)
    lines = [
        "# Knowledge lint report",
        "",
        f"Repository: {report['repository']}",
        f"Alias: {report['repo_alias'] or 'unknown'}",
        f"Mode: {report['mode']}",
        f"Files scanned: {report['files_scanned']}",
        f"Changed markdown files: {report['changed_markdown_files']}",
        f"Findings: {report['findings_total']} "
        f"(errors: {counts.get('error', 0)}, warnings: {counts.get('warning', 0)}, info: {counts.get('info', 0)})",
        "",
    ]

    findings = report["findings"]
    assert isinstance(findings, list)
    if not findings:
        lines.append("No findings.")
    else:
        lines.append("## Findings")
        for finding in findings:
            assert isinstance(finding, dict)
            lines.append(
                f"- [{finding['severity']}] {finding['code']} "
                f"`{finding['path']}` - {finding['detail']}"
            )
        if report["truncated"]:
            lines.append("- Output truncated. Increase --max-findings or use --format json.")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", help="Target knowledge repository path.")
    parser.add_argument("--repo-alias", default="", help="Repository alias from CSP.")
    parser.add_argument("--changed-only", action="store_true", help="Scan changed Markdown files only.")
    parser.add_argument("--base", default="origin/main", help="Git base for changed-only mode.")
    parser.add_argument("--stale-days", type=int, default=180, help="Date age that counts as stale.")
    parser.add_argument("--max-findings", type=int, default=80, help="Maximum findings to print; -1 means all.")
    parser.add_argument("--format", choices={"text", "json"}, default="text", help="Output format.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings or errors.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists() or not repo.is_dir():
        raise SystemExit(f"Repository path does not exist or is not a directory: {repo}")

    report = build_report(repo, args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))

    counts = report["counts"]
    assert isinstance(counts, dict)
    if counts.get("error", 0) > 0 or (
        args.strict and (counts.get("warning", 0) > 0 or counts.get("error", 0) > 0)
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
