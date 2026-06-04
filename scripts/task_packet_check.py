#!/usr/bin/env python3
"""Validate a minimal CSP task packet without creating a new source of truth."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from guard_shared_writes import shared_file_specs
from producer_check import allowed_write_specs as producer_allowed_write_specs


REQUIRED_FIELDS = (
    "request",
    "interpreted_task",
    "target_project",
    "target_repo_alias",
    "target_repo",
    "target_branch",
    "thread",
    "mode",
    "allowed_writes",
    "forbidden_writes",
    "validation_gates",
    "hold_conditions",
    "expected_output",
    "next_handoff_target",
)

LIST_FIELDS = {
    "allowed_writes",
    "forbidden_writes",
    "validation_gates",
    "hold_conditions",
}

ALLOWED_MODES = {"read_only", "producer", "implementer", "consolidator"}
TASK_PACKET_POLICY_DOC = "docs/task-packet-policy.md"


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def parse_markdown_table(path: Path, expected_columns: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []

    rows: list[dict[str, str]] = []
    header: list[str] = []
    expected = [column.lower() for column in expected_columns]
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        cells = split_table_row(stripped)
        normalized = [cell.lower() for cell in cells[: len(expected_columns)]]
        if normalized == expected:
            header = expected_columns
            continue

        if not header or is_separator_row(cells) or len(cells) < len(header):
            continue

        rows.append({column: cells[index] for index, column in enumerate(header)})
    return rows


def clean(value: str) -> str:
    return value.strip().strip("`")


def project_aliases(root: Path) -> set[str]:
    rows = parse_markdown_table(
        root / "context" / "GLOBAL_INDEX.md",
        ["Alias", "Status", "Entry", "Meaning"],
    )
    return {clean(row.get("Alias", "")) for row in rows if row.get("Alias")}


def repo_rows(root: Path) -> list[dict[str, str]]:
    return parse_markdown_table(
        root / "context" / "REPOSITORY_REGISTRY.md",
        ["Alias", "Repository", "Branch", "Role", "Visibility", "Write Target", "Notes"],
    )


def repo_by_alias(root: Path, alias: str) -> dict[str, str] | None:
    for row in repo_rows(root):
        if clean(row.get("Alias", "")) == alias:
            return row
    return None


def project_threads(root: Path, project: str) -> set[str]:
    rows = parse_markdown_table(
        root / "projects" / project / "THREADS.md",
        ["Thread", "Status", "Owner", "Purpose", "Next Action"],
    )
    return {clean(row.get("Thread", "")) for row in rows if row.get("Thread")}


def first_project_thread(root: Path, project: str) -> str:
    threads = sorted(project_threads(root, project))
    return threads[0] if threads else "unknown-thread"


def repo_alias_for_project(root: Path, project: str) -> str:
    if project == "csp-system":
        return "csp"
    for row in repo_rows(root):
        notes = f"{row.get('Write Target', '')} {row.get('Notes', '')}".lower()
        alias = clean(row.get("Alias", ""))
        if project in notes or project == alias:
            return alias
    return "csp"


def strip_markdown_fence(text: str) -> str:
    match = re.search(r"```(?:yaml|yml|json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null"}:
        return ""
    if value in {"[]", "[ ]"}:
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",")]
    return value.strip('"').strip("'")


def parse_yamlish(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        stripped = raw_line.strip()
        if stripped.startswith("- ") and current_key:
            value = stripped[2:].strip()
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(parse_scalar(value))
            continue

        if not raw_line.startswith((" ", "\t")) and ":" in raw_line:
            key, value = raw_line.split(":", 1)
            key = key.strip()
            if value.strip() == "":
                data[key] = []
                current_key = key
            else:
                data[key] = parse_scalar(value)
                current_key = None

    return data


def parse_packet(text: str) -> dict[str, Any]:
    packet_text = strip_markdown_fence(text)
    try:
        parsed = json.loads(packet_text)
    except json.JSONDecodeError:
        parsed = parse_yamlish(packet_text)
    if not isinstance(parsed, dict):
        raise ValueError("task packet must be a mapping/object")
    return parsed


def list_value(packet: dict[str, Any], key: str) -> list[str]:
    value = packet.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in {"", "none", "n/a"}:
            return []
        return [stripped]
    return [str(value).strip()]


def normalize_spec(value: str) -> str:
    return value.strip().replace("\\", "/")


def acceptable_producer_specs(project: str) -> set[str]:
    specs = set(producer_allowed_write_specs(project))
    specs.add(f"projects/{project}/events/*")  # legacy shorthand accepted for existing drafts
    specs.add(f"projects/{project}/sessions/<session-id>.md")
    return specs


def missing_shared_specs(items: list[str]) -> list[str]:
    normalized = {normalize_spec(item) for item in items}
    return [
        spec
        for spec in shared_file_specs()
        if spec not in normalized
    ]


def validate_packet(root: Path, packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in packet:
            errors.append(f"missing required field `{field}`")

    for field in LIST_FIELDS:
        if field in packet and not isinstance(packet[field], list):
            if isinstance(packet[field], str) and packet[field].strip().lower() in {"none", "n/a"}:
                continue
            errors.append(f"`{field}` should be a list")

    project = str(packet.get("target_project", "")).strip()
    repo_alias = clean(str(packet.get("target_repo_alias", "")))
    repo_name = str(packet.get("target_repo", "")).strip()
    branch = str(packet.get("target_branch", "")).strip()
    thread = str(packet.get("thread", "")).strip()
    mode = str(packet.get("mode", "")).strip()

    if project and project not in project_aliases(root):
        errors.append(f"`target_project` `{project}` is not in context/GLOBAL_INDEX.md")

    repo = repo_by_alias(root, repo_alias) if repo_alias else None
    if repo_alias and repo is None:
        errors.append(f"`target_repo_alias` `{repo_alias}` is not in context/REPOSITORY_REGISTRY.md")
    if repo and repo_name and clean(repo.get("Repository", "")) != repo_name:
        errors.append(
            f"`target_repo` `{repo_name}` does not match registry value `{clean(repo.get('Repository', ''))}`"
        )
    if repo and branch and clean(repo.get("Branch", "")) != branch:
        errors.append(
            f"`target_branch` `{branch}` does not match registry value `{clean(repo.get('Branch', ''))}`"
        )

    if project and thread and thread not in project_threads(root, project):
        errors.append(f"`thread` `{thread}` is not listed in projects/{project}/THREADS.md")

    if mode not in ALLOWED_MODES:
        errors.append(f"`mode` must be one of {', '.join(sorted(ALLOWED_MODES))}")

    allowed = list_value(packet, "allowed_writes")
    forbidden = list_value(packet, "forbidden_writes")
    gates = list_value(packet, "validation_gates")

    for key in ("request", "interpreted_task", "expected_output", "next_handoff_target"):
        if key in packet and not str(packet.get(key, "")).strip():
            errors.append(f"`{key}` must not be empty")

    if mode == "read_only" and allowed:
        errors.append("read_only packets should not list allowed writes; use `allowed_writes: []` or `none`")

    if mode == "producer":
        acceptable = acceptable_producer_specs(project)
        extra_allowed = [
            item for item in allowed if normalize_spec(item) not in acceptable
        ]
        if extra_allowed:
            errors.append(
                "producer packets may allow only the producer_check.py write surface: "
                + ", ".join(f"`{item}`" for item in sorted(acceptable))
            )

        required_specs = producer_allowed_write_specs(project)
        for spec in required_specs:
            if spec not in [normalize_spec(item) for item in allowed]:
                errors.append(f"producer packets must allow derived producer write spec `{spec}`")

        missing_specs = missing_shared_specs(forbidden)
        if missing_specs:
            preview = ", ".join(f"`{spec}`" for spec in missing_specs[:4])
            if len(missing_specs) > 4:
                preview += ", ..."
            errors.append(
                "producer packets must explicitly forbid shared projection files "
                f"derived from guard_shared_writes.py; missing {preview}"
            )

        if "producer_check_gate" not in gates:
            errors.append("producer packets must include `producer_check_gate` in `validation_gates`")

    if mode in {"producer", "implementer", "consolidator"}:
        for gate in ("routing_gate", "write_gate"):
            if gate not in gates:
                errors.append(f"`validation_gates` must include `{gate}`")

    if mode == "consolidator" and repo_alias != "csp":
        errors.append("consolidator packets should target the `csp` repository alias")
    if mode == "producer" and repo_alias != "csp":
        errors.append("producer packets should target the `csp` repository alias")

    return errors


def read_packet_arg(packet_arg: str) -> str:
    if packet_arg == "-":
        return sys.stdin.read()
    return Path(packet_arg).read_text(encoding="utf-8")


def write_boundaries_for_mode(project: str, mode: str) -> tuple[list[str], list[str]]:
    if mode == "read_only":
        allowed_writes: list[str] = []
    elif mode == "producer":
        allowed_writes = producer_allowed_write_specs(project)
    elif mode == "consolidator":
        allowed_writes = ["context/*", f"projects/{project}/*", "projects/*/RUNTIME.md"]
    else:
        allowed_writes = ["<target repo paths>"]

    forbidden_writes = shared_file_specs()
    if mode == "consolidator":
        forbidden_writes = ["<out-of-scope product/knowledge repo paths>"]

    return allowed_writes, forbidden_writes


def validation_gates_for_mode(mode: str, self_check: bool = False) -> list[str]:
    gates = [
        "routing_gate",
        "write_gate",
        "verification_gate",
    ]
    if mode == "producer":
        gates.append("producer_check_gate")
    if self_check:
        gates.append("task_packet_check_gate")
    return gates


def repo_alias_for_mode(root: Path, project: str, mode: str, repo_alias: str | None) -> str:
    if repo_alias:
        return repo_alias
    if mode in {"producer", "consolidator"}:
        return "csp"
    return repo_alias_for_project(root, project)


def packet_text(
    root: Path,
    project: str,
    mode: str,
    thread: str | None,
    repo_alias: str | None,
    request: str,
    interpreted_task: str,
    expected_output: str,
    next_handoff_target: str,
    *,
    self_check: bool = False,
) -> str:
    aliases = project_aliases(root)
    if project not in aliases:
        raise SystemExit(f"Unknown project `{project}`.")

    selected_repo_alias = repo_alias_for_mode(root, project, mode, repo_alias)
    repo = repo_by_alias(root, selected_repo_alias)
    if not repo:
        raise SystemExit(f"Unknown repository alias `{selected_repo_alias}`.")

    selected_thread = thread or first_project_thread(root, project)
    allowed_writes, forbidden_writes = write_boundaries_for_mode(project, mode)
    validation_gates = validation_gates_for_mode(mode, self_check=self_check)

    lines = [
        f"request: {request}",
        f"interpreted_task: {interpreted_task}",
        f"target_project: {project}",
        f"target_repo_alias: {selected_repo_alias}",
        f"target_repo: {clean(repo.get('Repository', ''))}",
        f"target_branch: {clean(repo.get('Branch', ''))}",
        f"thread: {selected_thread}",
        f"mode: {mode}",
        "allowed_writes:",
    ]
    lines.extend(f"  - {item}" for item in allowed_writes)
    lines.append("forbidden_writes:")
    lines.extend(f"  - {item}" for item in forbidden_writes)
    lines.extend(
        [
            "validation_gates:",
            *(f"  - {gate}" for gate in validation_gates),
            "hold_conditions:",
            "  - unclear routing",
            "  - dirty unrelated worktree changes",
            f"expected_output: {expected_output}",
            f"next_handoff_target: {next_handoff_target}",
        ]
    )
    return "\n".join(lines)


def example_packet(root: Path, project: str, mode: str, thread: str | None, repo_alias: str | None) -> str:
    return packet_text(
        root,
        project,
        mode,
        thread,
        repo_alias,
        "<user request>",
        "<agent interpretation>",
        "<files, commit, checks, and final response>",
        "<consolidator, producer, user, or none>",
    )


def default_preview_request(project: str, mode: str) -> str:
    return f"Preview a {mode} task packet for {project}"


def default_preview_task(project: str, mode: str, thread: str | None) -> str:
    thread_part = f" on thread {thread}" if thread else ""
    if mode == "read_only":
        return f"Inspect {project}{thread_part} without changing files"
    if mode == "producer":
        return f"Record append-only CSP event and session trace for {project}{thread_part}"
    if mode == "consolidator":
        return f"Consolidate CSP projections for {project}{thread_part} with local guardrails"
    return f"Implement scoped work for {project}{thread_part} and leave a CSP trace"


def default_expected_output(mode: str) -> str:
    if mode == "read_only":
        return "read-only findings and no repository changes"
    if mode == "producer":
        return "append-only event, one session card, producer_check result, and final response"
    if mode == "consolidator":
        return "updated projections, rebuilt runtime, guardrail results, commit or push details, and final response"
    return "changed files, verification results, CSP event or session trace, commit details, and final response"


def default_handoff_target(mode: str) -> str:
    if mode == "producer":
        return "consolidator"
    return "user"


def preview_packet(
    root: Path,
    project: str,
    mode: str,
    thread: str | None,
    repo_alias: str | None,
    request: str | None,
    interpreted_task: str | None,
    expected_output: str | None,
    next_handoff_target: str | None,
) -> str:
    text = packet_text(
        root,
        project,
        mode,
        thread,
        repo_alias,
        request or default_preview_request(project, mode),
        interpreted_task or default_preview_task(project, mode, thread),
        expected_output or default_expected_output(mode),
        next_handoff_target or default_handoff_target(mode),
        self_check=True,
    )
    errors = validate_packet(root, parse_packet(text))
    if errors:
        print("Generated preview failed its own task-packet check:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Validate a minimal CSP task packet. Policy: {TASK_PACKET_POLICY_DOC}."
    )
    parser.add_argument("packet", nargs="?", help="Packet file path, or '-' for stdin.")
    parser.add_argument("--example", action="store_true", help="Print a minimal example packet.")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print a generated, self-checked task packet preview to stdout.",
    )
    parser.add_argument("--project", default="csp-system", help="Project alias for --example/--preview.")
    parser.add_argument(
        "--mode",
        default="producer",
        choices=sorted(ALLOWED_MODES),
        help="Mode for --example/--preview.",
    )
    parser.add_argument("--thread", help="Thread for --example/--preview.")
    parser.add_argument("--repo-alias", help="Repository alias for --example/--preview.")
    parser.add_argument("--request", help="Request text for --preview.")
    parser.add_argument("--interpreted-task", help="Interpreted task text for --preview.")
    parser.add_argument("--expected-output", help="Expected output text for --preview.")
    parser.add_argument("--next-handoff-target", help="Next handoff target for --preview.")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    if not (root / "AGENTS.md").exists() or not (root / "context").exists():
        raise SystemExit("Run this from the CSP repository root.")

    if args.example and args.preview:
        raise SystemExit("Use only one of --example or --preview.")

    if args.example:
        print(example_packet(root, args.project, args.mode, args.thread, args.repo_alias))
        return

    if args.preview:
        print(
            preview_packet(
                root,
                args.project,
                args.mode,
                args.thread,
                args.repo_alias,
                args.request,
                args.interpreted_task,
                args.expected_output,
                args.next_handoff_target,
            )
        )
        return

    if not args.packet:
        raise SystemExit("Provide a task packet path, '-' for stdin, --example, or --preview.")

    try:
        packet = parse_packet(read_packet_arg(args.packet))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Could not read task packet: {exc}") from exc

    errors = validate_packet(root, packet)
    if errors:
        print("Task packet check failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Task packet is valid.")


if __name__ == "__main__":
    main()
