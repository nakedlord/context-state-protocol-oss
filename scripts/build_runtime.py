#!/usr/bin/env python3
"""Build a project RUNTIME.md from Context State Protocol events and sessions.

The script intentionally uses only the Python standard library so it can run in
local Codex sessions and GitHub Actions without setup.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path


VALID_STATUSES = {
    "active",
    "paused",
    "merged",
    "obsolete",
    "conflicted",
    "archived",
}

LIVE_STATUSES = {"active", "paused", "conflicted"}


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
                body = "\n".join(lines[index + 1 :]).strip()
                return MarkdownDoc(path=path, meta=meta, body=body)
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip().strip('"')

    return MarkdownDoc(path=path, meta=meta, body=text.strip())


def read_section(body: str, heading: str) -> list[str]:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return []

    start = match.end()
    next_heading = re.search(r"^##\s+", body[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(body)
    section = body[start:end].strip()

    items: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def read_single_section(body: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""

    start = match.end()
    next_heading = re.search(r"^##\s+", body[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(body)
    return body[start:end].strip()


def load_docs(directory: Path) -> list[MarkdownDoc]:
    if not directory.exists():
        return []
    return [
        parse_front_matter(path)
        for path in sorted(directory.glob("*.md"))
        if path.name.upper() != "README.MD"
    ]


def event_sort_key(doc: MarkdownDoc) -> tuple[str, str]:
    return (doc.meta.get("date", ""), doc.meta.get("id", doc.path.name))


def bullet_or_empty(items: list[str], empty: str) -> str:
    deduped = dedupe_preserve_order(items)
    if not deduped:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in deduped)


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def render_latest_events(events: list[MarkdownDoc]) -> str:
    if not events:
        return "- No events recorded."

    lines: list[str] = []
    for event in sorted(events, key=event_sort_key, reverse=True)[:10]:
        date = event.meta.get("date", "unknown-date")
        event_type = event.meta.get("type", "event")
        thread = event.meta.get("thread", "unknown-thread")
        summary = event.meta.get("summary", event.path.stem)
        status = event.meta.get("status", "active")
        lines.append(f"- {date} [{event_type}/{status}] `{thread}`: {summary}")
    return "\n".join(lines)


def render_active_threads(events: list[MarkdownDoc], sessions: list[MarkdownDoc]) -> str:
    lines: list[str] = []

    for session in sorted(sessions, key=lambda doc: doc.meta.get("updated", "")):
        status = session.meta.get("status", "")
        if status not in {"active", "conflicted", "paused"}:
            continue
        session_id = session.meta.get("id", session.path.stem)
        thread = session.meta.get("thread", "unknown-thread")
        agent = session.meta.get("agent", "unknown-agent")
        next_action = read_single_section(session.body, "Next Action").replace("\n", " ")
        suffix = f" Next: {next_action}" if next_action else ""
        lines.append(f"- `{thread}` via {agent} ({status}, `{session_id}`).{suffix}")

    seen_threads = {session.meta.get("thread") for session in sessions}
    for event in sorted(events, key=event_sort_key):
        thread = event.meta.get("thread", "")
        status = event.meta.get("status", "")
        if thread and thread not in seen_threads and status in {"active", "conflicted"}:
            lines.append(f"- `{thread}` from events ({status}).")
            seen_threads.add(thread)

    return "\n".join(lines) if lines else "- No active threads recorded."


def split_markdown_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_markdown_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def parse_markdown_table(path: Path, expected_columns: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []

    doc = parse_front_matter(path)
    rows: list[dict[str, str]] = []
    header: list[str] = []
    expected = [column.lower() for column in expected_columns]

    for line in doc.body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        cells = split_markdown_table_row(stripped)
        normalized_cells = [cell.lower() for cell in cells[: len(expected_columns)]]
        if normalized_cells == expected:
            header = expected_columns
            continue

        if not header or is_markdown_separator_row(cells):
            continue

        if len(cells) < len(header):
            continue

        rows.append(
            {
                column: cells[index]
                for index, column in enumerate(header)
            }
        )

    return rows


def parse_decision_rows(path: Path) -> list[dict[str, str]]:
    return parse_markdown_table(
        path,
        ["Date", "Decision", "Reason", "Impact", "Source Event"],
    )


def parse_thread_rows(path: Path) -> list[dict[str, str]]:
    return parse_markdown_table(
        path,
        ["Thread", "Status", "Owner", "Purpose", "Next Action"],
    )


def render_curated_threads(
    thread_rows: list[dict[str, str]],
    events: list[MarkdownDoc],
    sessions: list[MarkdownDoc],
) -> str:
    live_rows = [
        row for row in thread_rows if row.get("Status", "").lower() in LIVE_STATUSES
    ]
    if not live_rows:
        return render_active_threads(events, sessions)

    lines: list[str] = []
    for row in live_rows:
        thread = row.get("Thread", "unknown-thread")
        status = row.get("Status", "active")
        owner = row.get("Owner", "unknown-owner")
        purpose = row.get("Purpose", "").rstrip(".")
        next_action = row.get("Next Action", "")
        suffix = f" Next: {next_action}" if next_action else ""
        if purpose:
            lines.append(f"- `{thread}` ({status}, {owner}): {purpose}.{suffix}")
        else:
            lines.append(f"- `{thread}` ({status}, {owner}).{suffix}")

    return "\n".join(lines)


def render_curated_decisions(decision_rows: list[dict[str, str]]) -> str:
    if not decision_rows:
        return "- No curated decisions recorded."

    lines: list[str] = []
    for row in decision_rows:
        date = row.get("Date", "unknown-date")
        decision = row.get("Decision", "").rstrip(".")
        source = row.get("Source Event", "").strip("`")
        suffix = f" Source: `{source}`." if source else ""
        if decision:
            lines.append(f"- {date}: {decision}.{suffix}")

    return "\n".join(lines) if lines else "- No curated decisions recorded."


def normalize_decision_candidate(item: str) -> str:
    return re.sub(r"\s+", " ", item).strip().rstrip(".").lower()


def collect_decision_candidates(
    events: list[MarkdownDoc],
    decision_rows: list[dict[str, str]],
    limit: int = 10,
) -> list[str]:
    curated = {
        normalize_decision_candidate(row.get("Decision", ""))
        for row in decision_rows
        if row.get("Decision")
    }
    candidates: list[str] = []
    for item in collect_section_items(events, "Decisions"):
        if normalize_decision_candidate(item) in curated:
            continue
        candidates.append(item)
    return dedupe_preserve_order(candidates)[-limit:]


def runtime_stamp(docs: list[MarkdownDoc | None]) -> str:
    dates: list[str] = []
    for doc in docs:
        if doc is None:
            continue
        for key in ("date", "updated"):
            value = doc.meta.get(key, "")
            match = re.match(r"\d{4}-\d{2}-\d{2}", value)
            if match:
                dates.append(match.group(0))
    return max(dates) if dates else dt.date.today().isoformat()


def collect_section_items(events: list[MarkdownDoc], heading: str) -> list[str]:
    items: list[str] = []
    for event in sorted(events, key=event_sort_key):
        for item in read_section(event.body, heading):
            if is_noise_item(heading, item):
                continue
            items.append(item)
    return items


def collect_session_next_actions(sessions: list[MarkdownDoc]) -> list[str]:
    items: list[str] = []
    for session in sorted(sessions, key=lambda doc: doc.meta.get("updated", "")):
        if session.meta.get("status") not in {"active", "paused", "conflicted"}:
            continue
        next_action = read_single_section(session.body, "Next Action").strip()
        if next_action:
            items.append(next_action.replace("\n", " "))
    return items


def collect_curated_thread_next_actions(thread_rows: list[dict[str, str]]) -> list[str]:
    items: list[str] = []
    for row in thread_rows:
        if row.get("Status", "").lower() not in LIVE_STATUSES:
            continue
        next_action = row.get("Next Action", "").strip()
        if next_action:
            items.append(next_action.replace("\n", " "))
    return items


def collect_next_action_candidates(
    events: list[MarkdownDoc],
    accepted_next_actions: list[str],
    limit: int = 10,
) -> list[str]:
    accepted = {
        normalize_decision_candidate(item)
        for item in accepted_next_actions
    }
    candidates: list[str] = []
    for item in collect_section_items(events, "Next Actions"):
        if normalize_decision_candidate(item) in accepted:
            continue
        candidates.append(item)
    return dedupe_preserve_order(candidates)[-limit:]


def is_noise_item(heading: str, item: str) -> bool:
    lowered = item.lower()
    if heading == "Decisions":
        return lowered.startswith("no new ") or lowered.startswith("no final ")
    return False


def parse_conflict_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 5 or cells[0] == "ID":
            continue
        rows.append(
            {
                "id": cells[0],
                "status": cells[1].lower(),
                "summary": cells[2],
                "threads": cells[3],
                "next": cells[4],
            }
        )
    return rows


def render_conflicts(conflict_rows: list[dict[str, str]]) -> str:
    active_conflicts = get_active_conflicts(conflict_rows)
    if not active_conflicts:
        return "- No conflicts recorded."

    lines: list[str] = []
    for row in active_conflicts:
        lines.append(
            f"- `{row['id']}` ({row['status']}): {row['summary']} Next: {row['next']}"
        )
    return "\n".join(lines)


def get_active_conflicts(conflict_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in conflict_rows if row["status"] in {"active", "conflicted"}]


def render_repository_status(status_doc: MarkdownDoc | None) -> str:
    if status_doc is None:
        return "- No repository status recorded."

    lines: list[str] = []
    product_status = status_doc.meta.get("product_repo_status", "")
    repository_request = status_doc.meta.get("repository_request", "")

    if product_status:
        lines.append(f"- Product/content repo status: `{product_status}`")
    if repository_request:
        lines.append(f"- Repository request: `{repository_request}`")

    for item in read_section(status_doc.body, "Status"):
        normalized = item.lower()
        if normalized.startswith("product/content repo status:"):
            continue
        if normalized.startswith("repository request:"):
            continue
        lines.append(f"- {item}")

    if product_status in {"missing", "partial"}:
        lines.append(
            "- Action required: propose repository creation/structure before remote product-code work."
        )

    return "\n".join(lines) if lines else "- Repository status file is present but empty."


def render_current_state(events: list[MarkdownDoc], sessions: list[MarkdownDoc]) -> str:
    if not events and not sessions:
        return "No events or sessions have been recorded yet."

    latest_event = sorted(events, key=event_sort_key)[-1] if events else None
    active_sessions = [
        session
        for session in sessions
        if session.meta.get("status") in {"active", "paused", "conflicted"}
    ]
    parts: list[str] = []

    if latest_event:
        date = latest_event.meta.get("date", "unknown-date")
        summary = latest_event.meta.get("summary", latest_event.path.stem)
        parts.append(f"Latest event on {date}: {summary}")

    if active_sessions:
        parts.append(f"{len(active_sessions)} active/paused/conflicted session card(s) are tracked.")

    return " ".join(parts)


def build_runtime(project_dir: Path) -> str:
    project = project_dir.name
    events = load_docs(project_dir / "events")
    sessions = load_docs(project_dir / "sessions")
    repository_status = None
    repository_status_path = project_dir / "REPOSITORY_STATUS.md"
    if repository_status_path.exists():
        repository_status = parse_front_matter(repository_status_path)
    decisions_doc = None
    decisions_path = project_dir / "DECISIONS.md"
    if decisions_path.exists():
        decisions_doc = parse_front_matter(decisions_path)
    threads_doc = None
    threads_path = project_dir / "THREADS.md"
    if threads_path.exists():
        threads_doc = parse_front_matter(threads_path)
    conflict_rows = parse_conflict_rows(project_dir / "CONFLICTS.md")
    generated_at = runtime_stamp(
        [*events, *sessions, repository_status, decisions_doc, threads_doc]
    )

    active_conflicts = get_active_conflicts(conflict_rows)
    events_for_next_actions = events
    if not active_conflicts:
        events_for_next_actions = [
            event
            for event in events
            if event.meta.get("type") != "conflict"
            and event.meta.get("status") != "conflicted"
        ]

    events_for_decisions = events
    if not active_conflicts:
        events_for_decisions = [
            event
            for event in events
            if event.meta.get("type") != "conflict"
            and event.meta.get("status") != "conflicted"
        ]

    active_events_for_next_actions = [
        event
        for event in events_for_next_actions
        if event.meta.get("status") in {"active", "paused", "conflicted"}
    ]

    decision_rows = parse_decision_rows(decisions_path)
    thread_rows = parse_thread_rows(threads_path)
    decision_candidates = collect_decision_candidates(events_for_decisions, decision_rows)
    next_actions = collect_curated_thread_next_actions(thread_rows)
    if not next_actions:
        next_actions = collect_session_next_actions(sessions)
    next_action_candidates = collect_next_action_candidates(
        active_events_for_next_actions,
        next_actions,
    )

    return f"""---
project: {project}
generated: true
generated_at: {generated_at}
---

# Runtime

This file is generated from curated project files, events, and session cards. Do not use it as the source of truth.

## Current State

{render_current_state(events, sessions)}

## Repository Status

{render_repository_status(repository_status)}

## Latest Events

{render_latest_events(events)}

## Active Threads

{render_curated_threads(thread_rows, events, sessions)}

## Decisions

{render_curated_decisions(decision_rows)}

## Decision Candidates

{bullet_or_empty(decision_candidates, "No event-level decision candidates outside curated decisions.")}

## Conflicts

{render_conflicts(conflict_rows)}

## Next Actions

{bullet_or_empty(next_actions, "No next actions recorded.")}

## Next Action Candidates

{bullet_or_empty(next_action_candidates, "No event-level next action candidates outside curated threads.")}
"""


def validate_project_dir(project_dir: Path) -> None:
    if not project_dir.exists():
        raise SystemExit(f"Project directory does not exist: {project_dir}")
    if not project_dir.is_dir():
        raise SystemExit(f"Project path is not a directory: {project_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Context State Protocol runtime.")
    parser.add_argument("project", help="Project directory, for example projects/example")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write RUNTIME.md; fail if generated output differs.",
    )
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    validate_project_dir(project_dir)

    output = build_runtime(project_dir)
    runtime_path = project_dir / "RUNTIME.md"

    if args.check:
        existing = runtime_path.read_text(encoding="utf-8") if runtime_path.exists() else ""
        if existing != output:
            raise SystemExit(f"RUNTIME.md is stale for {project_dir}")
        print(f"RUNTIME.md is current for {project_dir}")
        return

    runtime_path.write_text(output, encoding="utf-8", newline="\n")
    print(f"Built {runtime_path}")


if __name__ == "__main__":
    main()
