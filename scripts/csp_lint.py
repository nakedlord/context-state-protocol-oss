#!/usr/bin/env python3
"""Warn about CSP event/session shape without blocking legacy history by default."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


ALLOWED_STATUSES = {
    "active",
    "paused",
    "merged",
    "obsolete",
    "conflicted",
    "archived",
}

EVENT_REQUIRED_FIELDS = (
    "id",
    "date",
    "type",
    "project",
    "thread",
    "source",
    "status",
    "summary",
)

SESSION_REQUIRED_FIELDS = (
    "id",
    "project",
    "agent",
    "thread",
    "status",
    "updated",
)

EXECUTION_RECORD_FROM = "2026-05-18"
SYSTEM_IMPACT_FROM = "2026-05-20"

IMPACTFUL_EVENT_TYPES = {
    "architecture_update",
    "context_consolidation",
    "conflict",
    "knowledge_update",
    "product_update",
    "repository_request",
    "routing_question",
    "runtime_update",
}

IMPACT_HINTS = (
    "agent method",
    "architecture",
    "automation",
    "ci",
    "conflict",
    "contract",
    "decision",
    "playbook",
    "product",
    "protocol",
    "repository",
    "routing",
    "system impact",
    "workflow",
)


@dataclass(frozen=True)
class MarkdownDoc:
    path: Path
    meta: dict[str, str]
    body: str


@dataclass(frozen=True)
class Issue:
    path: Path
    message: str


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


def normalize_path(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix()


def parse_front_matter(path: Path) -> MarkdownDoc:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    meta: dict[str, str] = {}

    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                body = "\n".join(lines[index + 1 :]).strip()
                return MarkdownDoc(path=path, meta=meta, body=body)
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip().strip('"')

    return MarkdownDoc(path=path, meta=meta, body=text.strip())


def has_heading(body: str, heading: str) -> bool:
    return re.search(rf"^##\s+{re.escape(heading)}\s*$", body, re.MULTILINE) is not None


def metadata_date(value: str) -> str:
    match = re.match(r"\d{4}-\d{2}-\d{2}", value)
    return match.group(0) if match else ""


def date_on_or_after(value: str, threshold: str) -> bool:
    date = metadata_date(value)
    return bool(date and date >= threshold)


def is_event_path(path: Path) -> bool:
    normalized = normalize_path(path.as_posix())
    return re.match(r"^projects/[^/]+/events/[^/]+\.md$", normalized) is not None


def is_session_path(path: Path) -> bool:
    normalized = normalize_path(path.as_posix())
    return re.match(r"^projects/[^/]+/sessions/[^/]+\.md$", normalized) is not None


def project_from_path(path: Path) -> str:
    parts = PurePosixPath(normalize_path(path.as_posix())).parts
    return parts[1] if len(parts) >= 2 and parts[0] == "projects" else ""


def matching_sessions(root: Path, project: str, event_id: str, thread: str) -> list[Path]:
    sessions_dir = root / "projects" / project / "sessions"
    if not sessions_dir.exists():
        return []

    matches: list[Path] = []
    same_id = sessions_dir / f"{event_id}.md"
    if same_id.exists():
        matches.append(same_id)

    for path in sessions_dir.glob("*.md"):
        if path in matches:
            continue
        doc = parse_front_matter(path)
        if thread and doc.meta.get("thread") == thread:
            matches.append(path)

    return matches


def looks_system_impactful(doc: MarkdownDoc) -> bool:
    event_type = doc.meta.get("type", "")
    if event_type in IMPACTFUL_EVENT_TYPES:
        return True

    haystack = f"{doc.meta.get('summary', '')}\n{doc.body}".lower()
    return any(hint in haystack for hint in IMPACT_HINTS)


def validate_required_fields(
    doc: MarkdownDoc,
    required: tuple[str, ...],
    issues: list[Issue],
) -> None:
    for field in required:
        if field not in doc.meta:
            issues.append(Issue(doc.path, f"missing front matter field `{field}`"))

    for key in doc.meta:
        if key.lower() in required and key != key.lower():
            issues.append(
                Issue(
                    doc.path,
                    f"front matter key `{key}` should be lower-case `{key.lower()}`",
                )
            )


def validate_status(doc: MarkdownDoc, issues: list[Issue]) -> None:
    status = doc.meta.get("status", "")
    if not status:
        return

    if status not in ALLOWED_STATUSES:
        issues.append(
            Issue(
                doc.path,
                f"invalid status `{status}`; use one of {', '.join(sorted(ALLOWED_STATUSES))}",
            )
        )

    if status == "needs_consolidation":
        issues.append(
            Issue(
                doc.path,
                "`needs_consolidation` belongs in durable/execution status or next actions, not front matter `status`",
            )
        )


def validate_filename_id(doc: MarkdownDoc, issues: list[Issue]) -> None:
    doc_id = doc.meta.get("id", "")
    if doc_id and doc.path.stem != doc_id:
        issues.append(Issue(doc.path, f"filename stem does not match id `{doc_id}`"))


def validate_project_field(doc: MarkdownDoc, issues: list[Issue]) -> None:
    path_project = project_from_path(doc.path)
    meta_project = doc.meta.get("project", "")
    if path_project and meta_project and path_project != meta_project:
        issues.append(
            Issue(
                doc.path,
                f"project field `{meta_project}` does not match path project `{path_project}`",
            )
        )


def validate_date_field(doc: MarkdownDoc, field: str, issues: list[Issue]) -> None:
    value = doc.meta.get(field, "")
    if value and not metadata_date(value):
        issues.append(Issue(doc.path, f"`{field}` should start with YYYY-MM-DD"))


def validate_event(doc: MarkdownDoc, root: Path) -> list[Issue]:
    issues: list[Issue] = []
    validate_required_fields(doc, EVENT_REQUIRED_FIELDS, issues)
    validate_status(doc, issues)
    validate_filename_id(doc, issues)
    validate_project_field(doc, issues)
    validate_date_field(doc, "date", issues)

    if date_on_or_after(doc.meta.get("date", ""), EXECUTION_RECORD_FROM) and not has_heading(
        doc.body, "Execution Record"
    ):
        issues.append(
            Issue(
                doc.path,
                f"events dated {EXECUTION_RECORD_FROM} or later should include `## Execution Record`",
            )
        )

    if (
        date_on_or_after(doc.meta.get("date", ""), SYSTEM_IMPACT_FROM)
        and looks_system_impactful(doc)
        and not has_heading(doc.body, "System Impact")
    ):
        issues.append(
            Issue(
                doc.path,
                "likely system-impactful event should include `## System Impact` or explain no impact",
            )
        )

    project = doc.meta.get("project", project_from_path(doc.path))
    event_id = doc.meta.get("id", doc.path.stem)
    thread = doc.meta.get("thread", "")
    if date_on_or_after(doc.meta.get("date", ""), EXECUTION_RECORD_FROM):
        if project and not matching_sessions(root, project, event_id, thread):
            issues.append(
                Issue(
                    doc.path,
                    "newer event has no matching session card by id or thread",
                )
            )

    return issues


def validate_session(doc: MarkdownDoc) -> list[Issue]:
    issues: list[Issue] = []
    validate_required_fields(doc, SESSION_REQUIRED_FIELDS, issues)
    validate_status(doc, issues)
    validate_filename_id(doc, issues)
    validate_project_field(doc, issues)
    validate_date_field(doc, "updated", issues)

    if date_on_or_after(doc.meta.get("updated", ""), EXECUTION_RECORD_FROM) and not has_heading(
        doc.body, "Event Summary"
    ):
        issues.append(
            Issue(
                doc.path,
                f"sessions updated {EXECUTION_RECORD_FROM} or later should include `## Event Summary`",
            )
        )

    if not has_heading(doc.body, "Next Action"):
        issues.append(Issue(doc.path, "session card should include `## Next Action`"))

    return issues


def changed_markdown_paths(base: str, head: str) -> list[Path]:
    output = run_git(["diff", "--name-only", "--diff-filter=ACMRTUXB", base, head])
    return [
        Path(normalize_path(line.strip()))
        for line in output.splitlines()
        if line.strip().endswith(".md")
    ]


def changed_markdown_statuses(base: str, head: str) -> dict[Path, str]:
    output = run_git(["diff", "--name-status", "--diff-filter=ACMRTUXB", base, head])
    statuses: dict[Path, str] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            path = parts[2]
        elif len(parts) >= 2:
            path = parts[1]
        else:
            continue

        if path.endswith(".md"):
            statuses[Path(normalize_path(path))] = status[0]
    return statuses


def discover_markdown_paths(root: Path, project: str | None) -> list[Path]:
    project_dirs = [root / "projects" / project] if project else sorted((root / "projects").glob("*"))
    paths: list[Path] = []
    for project_dir in project_dirs:
        if not project_dir.is_dir() or project_dir.name == "_template":
            continue
        for folder in ("events", "sessions"):
            paths.extend(sorted((project_dir / folder).glob("*.md")))
    return [path.relative_to(root) for path in paths]


def selected_paths(args: argparse.Namespace, root: Path) -> list[Path]:
    if args.paths:
        return [Path(normalize_path(path)) for path in args.paths]
    if args.changed:
        return changed_markdown_paths(args.changed[0], args.changed[1])
    return discover_markdown_paths(root, args.project)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lint CSP event and session Markdown shape.")
    parser.add_argument("paths", nargs="*", help="Specific Markdown paths to lint.")
    parser.add_argument(
        "--changed",
        nargs=2,
        metavar=("BASE", "HEAD"),
        help="Lint event/session files changed between two git revisions.",
    )
    parser.add_argument("--project", help="Limit full scan to one project alias.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when warnings are found.",
    )
    parser.add_argument(
        "--strict-new",
        action="store_true",
        help="Exit non-zero only for warnings on newly added event/session files in --changed range.",
    )
    parser.add_argument(
        "--strict-touched",
        action="store_true",
        help="Exit non-zero for warnings on any changed event/session files in --changed range.",
    )
    args = parser.parse_args()

    root = Path.cwd().resolve()
    issues: list[Issue] = []
    paths = selected_paths(args, root)
    strict_paths: set[Path] = set()

    if args.strict_new or args.strict_touched:
        if not args.changed:
            flag = "--strict-touched" if args.strict_touched else "--strict-new"
            raise SystemExit(f"{flag} requires --changed BASE HEAD")
        changed_statuses = changed_markdown_statuses(args.changed[0], args.changed[1])
        if args.strict_touched:
            strict_paths = {
                path
                for path in changed_statuses
                if is_event_path(path) or is_session_path(path)
            }
        else:
            strict_paths = {
                path
                for path, status in changed_statuses.items()
                if status == "A" and (is_event_path(path) or is_session_path(path))
            }

    for rel_path in paths:
        rel_path = Path(normalize_path(rel_path.as_posix()))
        if not (is_event_path(rel_path) or is_session_path(rel_path)):
            continue
        path = root / rel_path
        if not path.exists():
            continue

        doc = parse_front_matter(path)
        doc = MarkdownDoc(path=rel_path, meta=doc.meta, body=doc.body)
        if is_event_path(rel_path):
            issues.extend(validate_event(doc, root))
        elif is_session_path(rel_path):
            issues.extend(validate_session(doc))

    if not issues:
        print("CSP lint found no event/session shape warnings.")
        return

    print("CSP lint warnings:")
    for issue in issues:
        print(f"- {normalize_path(issue.path.as_posix())}: {issue.message}")
    print(f"\n{len(issues)} warning(s).")

    if args.strict:
        raise SystemExit(1)

    strict_mode_issues = [issue for issue in issues if issue.path in strict_paths]
    if strict_mode_issues:
        mode_name = "Strict-touched" if args.strict_touched else "Strict-new"
        target_name = (
            "changed event/session files"
            if args.strict_touched
            else "newly added event/session files"
        )
        print(
            f"{mode_name} mode: failing because {len(strict_mode_issues)} warning(s) "
            f"belong to {target_name}."
        )
        raise SystemExit(1)

    if args.strict_new or args.strict_touched:
        if args.strict_touched:
            print("Strict-touched mode: no warnings on changed event/session files.")
        else:
            print("Strict-new mode: no warnings on newly added event/session files.")
        return

    print("Warning mode: not failing. Use --strict or --strict-new to enforce.")


if __name__ == "__main__":
    main()
