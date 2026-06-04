# Agent Continuity Demo

This demo shows the smallest useful CSP loop:

1. read routing state;
2. select a project;
3. do work;
4. write an event and session card;
5. rebuild runtime.

It uses only synthetic data from `projects/example`.

## Problem

Without CSP, a new agent session often starts like this:

```text
User: Continue the project.
Agent: Which project? What was decided? Where is the repo? What should I not touch?
```

With CSP, the same session starts by reading files:

```text
AGENTS.md
context/GLOBAL_INDEX.md
context/REPOSITORY_REGISTRY.md
context/KNOWLEDGE_ROUTING.md
context/REPOSITORY_REQUESTS.md
projects/example/CONTEXT_CAPSULE.md
projects/example/RUNTIME.md
projects/example/THREADS.md
projects/example/DECISIONS.md
projects/example/CONFLICTS.md
projects/example/KNOWLEDGE_SOURCES.md
projects/example/REPOSITORY_STATUS.md
```

Now the agent knows:

- `example` is the selected project;
- `protocol-bootstrap` is the active thread;
- the project uses synthetic data only;
- there is no real implementation repository;
- the next action is to keep the example lint-clean.

## Simulated User Request

```text
Continue the example project and record what changed.
```

## Simulated Agent Output

The agent appends:

```text
projects/example/events/2026-06-04-codex-example-bootstrap.md
projects/example/sessions/2026-06-04-codex-example-bootstrap.md
```

Then it runs:

```bash
python scripts/csp_lint.py --strict
python scripts/build_runtime.py projects/example
python scripts/csp_status.py --project example
```

## What This Proves

CSP does not make the model smarter. It makes the work surface more durable:

- project selection is explicit;
- decisions have source events;
- active threads have next actions;
- ordinary sessions write append-only traces;
- generated runtime can be checked in CI.

## Try A Task Packet

```bash
python scripts/task_packet_check.py --preview --project example --mode producer
```

The packet is a reviewable preflight contract. It is not a runner and does not
grant execution authority.
