# Context State Protocol

Context State Protocol (CSP) is a repository-native state layer for long-running
AI agent work.

It gives Codex, ChatGPT, Claude Code, and other agents a durable project map:
what exists, what was decided, what changed, what is still active, and where a
new session should write its trace.

The core idea is simple: do not trust chat memory for project state. Put the
state in a repo, make agents read it before meaningful work, and make every
meaningful session leave an append-only event and session card.

## Why CSP

AI work often fails at the edges between sessions:

- the agent forgets project context;
- decisions live only in a chat transcript;
- private work gets mixed with public work;
- different agents overwrite each other's summaries;
- nobody can tell which source has already been processed.

CSP treats context as source-controlled operational state. Agents read a small
set of stable files, write append-only traces, and leave consolidation to an
explicit role.

## What Is In This Repo

```text
context/
  GLOBAL_INDEX.md           Project alias map
  REPOSITORY_REGISTRY.md    Repository routing and visibility
  KNOWLEDGE_ROUTING.md      Source-to-project routing rules
  REPOSITORY_REQUESTS.md    Proposed/missing repository queue
  ROADMAP.md                CSP evolution roadmap

projects/
  _template/                Copyable project skeleton
  csp-system/               Public self-management project
  example/                  Minimal working project

scripts/
  build_runtime.py          Builds project RUNTIME.md from events/sessions
  csp_lint.py               Checks event/session shape
  producer_check.py         Ensures producer writes are append-safe
  task_packet_check.py      Validates scoped task packets
  csp_status.py             Read-only status overview helper

templates/
  EVENT_TEMPLATE.md
  SESSION_CARD_TEMPLATE.md
  PROJECT_TEMPLATE.md

docs/
  architecture.md
  write-discipline.md
  task-packet-policy.md
  public-export-safety.md
```

## Quick Start

1. Clone this repository.
2. Copy `projects/_template` to `projects/<your-project-alias>`.
3. Add the alias to `context/GLOBAL_INDEX.md`.
4. Add repo routing to `context/REPOSITORY_REGISTRY.md`.
5. Ask your agent to follow `AGENTS.md` before meaningful work.
6. After a session, run:

```bash
python scripts/csp_lint.py --strict
python scripts/build_runtime.py projects/<your-project-alias>
python scripts/csp_status.py --overview
```

## Agent Workflow

Before meaningful work, an agent should read:

1. `AGENTS.md`
2. `context/GLOBAL_INDEX.md`
3. `context/REPOSITORY_REGISTRY.md`
4. `context/KNOWLEDGE_ROUTING.md`
5. `context/REPOSITORY_REQUESTS.md`
6. the selected project's `CONTEXT_CAPSULE.md`, `RUNTIME.md`,
   `THREADS.md`, `DECISIONS.md`, `CONFLICTS.md`,
   `KNOWLEDGE_SOURCES.md`, and `REPOSITORY_STATUS.md`

After meaningful work, a normal producer writes only:

- `projects/<project>/events/<event-id>.md`
- `projects/<project>/sessions/<session-id>.md`

Shared projection files such as `RUNTIME.md`, `THREADS.md`, `DECISIONS.md`,
and `GLOBAL_INDEX.md` are updated by a consolidator pass.

## Public Export Safety

Do not make a private CSP repository public directly. A working CSP repo often
contains local paths, private project names, business context, health context,
personal notes, and source processing traces.

For public release, create a clean export with new git history and only generic
examples. See `docs/public-export-safety.md`.

## Current Status

This public edition is intentionally small. It is a working protocol skeleton,
not a hosted product. The next useful layers are:

- richer status and routing tools;
- stricter CI;
- examples for multi-repository knowledge ingestion;
- connectors for agent UIs;
- optional vector/search adapters that keep CSP as the source of truth.

## License

Apache License 2.0. See `LICENSE`.
