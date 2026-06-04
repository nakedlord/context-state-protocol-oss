#!/usr/bin/env python3
"""Read-only status helper for Context State Protocol repositories."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MarkdownDoc:
    path: Path
    meta: dict[str, str]
    body: str


def parse_front_matter(path: Path) -> MarkdownDoc:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    meta: dict[str, str] = {}

    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return MarkdownDoc(path, meta, "\n".join(lines[index + 1 :]).strip())
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip().strip('"')

    return MarkdownDoc(path, meta, text.strip())


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def parse_table(path: Path, expected: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []

    rows: list[dict[str, str]] = []
    header: list[str] = []
    expected_lower = [column.lower() for column in expected]

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = split_table_row(stripped)
        if [cell.lower() for cell in cells[: len(expected)]] == expected_lower:
            header = expected
            continue
        if not header or is_separator(cells) or len(cells) < len(header):
            continue
        rows.append({column: cells[index] for index, column in enumerate(header)})

    return rows


def clean(value: str) -> str:
    return value.strip().strip("`")


def latest_docs(directory: Path, limit: int) -> list[MarkdownDoc]:
    if not directory.exists():
        return []
    docs = [parse_front_matter(path) for path in directory.glob("*.md")]
    return sorted(
        docs,
        key=lambda doc: (
            doc.meta.get("date", doc.meta.get("updated", "")),
            doc.meta.get("id", doc.path.stem),
        ),
        reverse=True,
    )[:limit]


def read_section(body: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", body, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", body[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(body)
    return body[start:end].strip()


def project_aliases(root: Path) -> list[dict[str, str]]:
    return parse_table(
        root / "context" / "GLOBAL_INDEX.md",
        ["Alias", "Status", "Entry", "Meaning"],
    )


def thread_rows(root: Path, project: str) -> list[dict[str, str]]:
    return parse_table(
        root / "projects" / project / "THREADS.md",
        ["Thread", "Status", "Owner", "Purpose", "Next Action"],
    )


def repo_rows(root: Path) -> list[dict[str, str]]:
    return parse_table(
        root / "context" / "REPOSITORY_REGISTRY.md",
        ["Alias", "Repository", "Branch", "Role", "Visibility", "Write Target", "Notes"],
    )


def format_project_overview(root: Path, project: str, limit: int) -> str:
    project_dir = root / "projects" / project
    if not project_dir.exists():
        raise SystemExit(f"Unknown project: {project}")

    capsule = parse_front_matter(project_dir / "CONTEXT_CAPSULE.md")
    latest = latest_docs(project_dir / "events", limit)
    threads = [row for row in thread_rows(root, project) if clean(row.get("Status", "")) == "active"]
    next_actions = [
        f"- `{clean(row.get('Thread', ''))}`: {row.get('Next Action', '')}"
        for row in threads
        if row.get("Next Action")
    ]

    lines = [
        f"# CSP Status: {project}",
        "",
        read_section(capsule.body, "One-Screen State") or "No capsule summary.",
        "",
        "## Active Threads",
    ]
    lines.extend(
        f"- `{clean(row.get('Thread', ''))}`: {row.get('Purpose', '')}"
        for row in threads
    )
    if not threads:
        lines.append("- No active threads.")

    lines.extend(["", "## Latest Events"])
    lines.extend(
        f"- {doc.meta.get('date', 'unknown-date')}: {doc.meta.get('summary', doc.path.stem)}"
        for doc in latest
    )
    if not latest:
        lines.append("- No events.")

    lines.extend(["", "## Next Actions"])
    lines.extend(next_actions or ["- No next actions."])
    return "\n".join(lines)


def format_overview(root: Path, limit: int) -> str:
    aliases = project_aliases(root)
    repos = repo_rows(root)
    lines = [
        "# CSP Overview",
        "",
        "## Projects",
    ]
    for row in aliases:
        alias = clean(row.get("Alias", ""))
        status = row.get("Status", "")
        meaning = row.get("Meaning", "")
        lines.append(f"- `{alias}` ({status}): {meaning}")
    if not aliases:
        lines.append("- No projects listed.")

    lines.extend(["", "## Repositories"])
    for row in repos:
        alias = clean(row.get("Alias", ""))
        repo = clean(row.get("Repository", ""))
        branch = clean(row.get("Branch", ""))
        visibility = row.get("Visibility", "")
        lines.append(f"- `{alias}` -> `{repo}` on `{branch}` ({visibility})")
    if not repos:
        lines.append("- No repositories listed.")

    lines.extend(["", "## Recent Events"])
    events: list[MarkdownDoc] = []
    for row in aliases:
        alias = clean(row.get("Alias", ""))
        events.extend(latest_docs(root / "projects" / alias / "events", limit))
    for doc in sorted(events, key=lambda item: item.meta.get("date", ""), reverse=True)[:limit]:
        project = doc.meta.get("project", "unknown")
        lines.append(f"- `{project}` {doc.meta.get('date', '')}: {doc.meta.get('summary', doc.path.stem)}")
    if not events:
        lines.append("- No events.")

    return "\n".join(lines)


def route_query(root: Path, query: str) -> str:
    rows = project_aliases(root)
    haystack = query.lower()
    scores: list[tuple[int, str, str]] = []
    for row in rows:
        alias = clean(row.get("Alias", ""))
        meaning = row.get("Meaning", "")
        score = 0
        for token in re.findall(r"[a-z0-9_-]+", f"{alias} {meaning}".lower()):
            if token and token in haystack:
                score += 1
        scores.append((score, alias, meaning))

    scores.sort(reverse=True)
    best = [item for item in scores if item[0] > 0]
    if not best:
        return "No confident route. Record a routing question instead of guessing."
    return "\n".join(f"- `{alias}`: {meaning}" for _, alias, meaning in best[:3])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overview", action="store_true", help="Show global overview.")
    parser.add_argument("--project", help="Show one project.")
    parser.add_argument("--route", help="Suggest project aliases for a query.")
    parser.add_argument("--recent", type=int, default=5, help="Number of recent events.")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    if not (root / "context").exists() or not (root / "projects").exists():
        raise SystemExit("Run from the CSP repository root.")

    if args.route:
        print(route_query(root, args.route))
        return

    if args.project:
        print(format_project_overview(root, args.project, args.recent))
        return

    print(format_overview(root, args.recent))


if __name__ == "__main__":
    main()
