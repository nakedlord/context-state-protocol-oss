# Architecture

CSP is a file protocol. It does not require a database, server, or hosted
runtime.

## Layers

1. Global routing files in `context/`.
2. Project state files in `projects/<project>/`.
3. Append-only events in `projects/<project>/events/`.
4. Session cards in `projects/<project>/sessions/`.
5. Scripts that validate and rebuild projections.

## Source Of Truth

Events and sessions are the write log. Curated files such as `THREADS.md`,
`DECISIONS.md`, and `RUNTIME.md` are projections.

This distinction keeps ordinary agent sessions append-safe. A producer can
record what happened without rewriting the shared map. A consolidator can later
merge useful facts into projections.

## Project Files

- `CONTEXT_CAPSULE.md`: one-screen project state for fast orientation.
- `RUNTIME.md`: generated operational view.
- `THREADS.md`: active and historical work threads.
- `DECISIONS.md`: accepted decisions.
- `CONFLICTS.md`: unresolved contradictions and policy conflicts.
- `KNOWLEDGE_SOURCES.md`: source inventory and ingestion status.
- `REPOSITORY_STATUS.md`: repo availability, branch, and write boundaries.

## Agent Roles

- Producer: does work and appends trace records.
- Consolidator: updates shared projections from accepted traces.
- Implementer: changes target product or knowledge repositories.
- Read-only reviewer: inspects state and returns findings without writes.
