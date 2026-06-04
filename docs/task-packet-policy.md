# Task Packet Policy

A task packet is a small handoff contract. It states what the agent should do,
where it should write, and when it should stop.

Task packets are not a new source of truth. They are generated from CSP routing
files and checked against them.

## Required Fields

- `request`
- `interpreted_task`
- `target_project`
- `target_repo_alias`
- `target_repo`
- `target_branch`
- `thread`
- `mode`
- `allowed_writes`
- `forbidden_writes`
- `validation_gates`
- `hold_conditions`
- `expected_output`
- `next_handoff_target`

## Modes

- `read_only`: inspect and report, no writes.
- `producer`: append event/session records only.
- `implementer`: change scoped target repository paths.
- `consolidator`: update shared CSP projections.

## Preview

```bash
python scripts/task_packet_check.py --preview --project csp-system --mode producer
```

## Validate

```bash
python scripts/task_packet_check.py path/to/packet.yml
```
