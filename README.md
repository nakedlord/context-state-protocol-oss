# Context State Protocol

**Repo-native memory and handoff protocol for long-running AI agent work.**

AI coding agents are getting better at a single task. They are still fragile
across sessions: they forget why a decision was made, where a project lives,
what sources were already processed, and which files they are allowed to touch.

Context State Protocol (CSP) turns that missing memory into source-controlled
project state. Agents read a small map before meaningful work, write append-only
events after work, and leave durable decisions to explicit consolidation.

```text
chat memory is temporary
repo state is durable
agent work needs both
```

## What CSP Gives You

- Project routing: agents can find the right project/repository instead of
  guessing.
- Continuity: every meaningful run leaves an event and a session card.
- Write discipline: ordinary agents append traces; consolidators update shared
  projections.
- Public/private safety: reusable protocol files stay separate from private
  operational state.
- Tooling: small Python scripts lint traces, build runtime views, preview task
  packets, and show status.

## A 2-Minute Example

An agent starts a new session and reads:

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

After work, it writes:

```text
projects/example/events/2026-06-04-codex-example-bootstrap.md
projects/example/sessions/2026-06-04-codex-example-bootstrap.md
```

Then the project runtime can be rebuilt:

```bash
python scripts/build_runtime.py projects/example
python scripts/csp_lint.py --strict
python scripts/csp_status.py --project example
```

See the full walkthrough in
[`examples/agent-continuity-demo`](examples/agent-continuity-demo/README.md).

## When To Use CSP

Use CSP when agent work is:

- long-running across multiple chats or days;
- spread across more than one repository;
- source-backed, such as knowledge ingestion or research;
- sensitive to public/private boundaries;
- affected by decisions, conflicts, roadmaps, or handoffs;
- shared by multiple agents or tools.

You probably do not need CSP for a one-off script, a throwaway prototype, or a
single isolated issue.

## Repository Layout

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

docs/
  architecture.md
  quickstart.md
  task-packet-policy.md
  write-discipline.md
  public-export-safety.md
  launch-kit.md
```

## Quick Start

```bash
git clone https://github.com/nakedlord/context-state-protocol-oss.git
cd context-state-protocol-oss
python scripts/csp_status.py --overview
python scripts/csp_lint.py --strict
python scripts/build_runtime.py projects/example --check
```

Create a project:

```bash
cp -r projects/_template projects/my-project
```

Then update:

- `context/GLOBAL_INDEX.md`
- `context/REPOSITORY_REGISTRY.md`
- `projects/my-project/*.md`

More detail: [`docs/quickstart.md`](docs/quickstart.md).

## Agent Entry Contract

Before meaningful work, tell your agent:

```text
Use Context State Protocol. Read AGENTS.md, context/GLOBAL_INDEX.md,
context/REPOSITORY_REGISTRY.md, context/KNOWLEDGE_ROUTING.md,
context/REPOSITORY_REQUESTS.md, then select the project and read its capsule,
runtime, threads, decisions, conflicts, knowledge sources, and repository
status. After meaningful work, write one event and one session card.
```

The full contract is in [`AGENTS.md`](AGENTS.md).

## Public Export Safety

Do not make a private CSP working repository public directly.

A real CSP repo can contain local paths, private project names, business
context, personal notes, health or financial context, and source-processing
traces. Publish clean exports with new git history and synthetic examples.

See [`docs/public-export-safety.md`](docs/public-export-safety.md).

## Roadmap

This public edition is intentionally small. The next useful layers are:

- richer demo projects;
- stronger privacy scan helpers;
- agent-specific setup examples for Codex, ChatGPT, Claude Code, and local
  coding agents;
- optional repository-local search adapters;
- better consolidation examples;
- launch and grant application materials for maintainers.

## Contributing

Useful contributions include docs, examples, stricter checks, public/private
boundary improvements, and agent-specific setup notes.

Start with [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
