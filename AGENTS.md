# Agent Instructions

Use Context State Protocol for durable project work: code, theories, processes,
decisions, repository routing, source ingestion, and continuation of prior
sessions.

Do not rely on chat memory as the source of truth.

## Before Meaningful Work

Read these files:

1. `AGENTS.md`
2. `context/GLOBAL_INDEX.md`
3. `context/REPOSITORY_REGISTRY.md`
4. `context/KNOWLEDGE_ROUTING.md`
5. `context/REPOSITORY_REQUESTS.md`

Then choose a target project from `GLOBAL_INDEX.md`.

If the project does not exist, do not place work into an unrelated alias.
Propose a new CSP alias and a repository request instead.

For the selected project, read:

1. `projects/<project>/CONTEXT_CAPSULE.md`
2. `projects/<project>/RUNTIME.md`
3. `projects/<project>/THREADS.md`
4. `projects/<project>/DECISIONS.md`
5. `projects/<project>/CONFLICTS.md`
6. `projects/<project>/KNOWLEDGE_SOURCES.md`
7. `projects/<project>/REPOSITORY_STATUS.md`

For app, tool, operating system, automation, memory, interface, or product
questions, use CSP as a cross-project map first. Scan `GLOBAL_INDEX.md`,
`KNOWLEDGE_ROUTING.md`, and `REPOSITORY_REGISTRY.md` before selecting a target.

## Roles

### Producer

A normal agent session is a producer. Producers may do project work, then append
trace records.

Producer write surface:

- `projects/<project>/events/*.md`
- `projects/<project>/sessions/<session-id>.md`

Producers do not edit:

- `context/GLOBAL_INDEX.md`
- `context/REPOSITORY_REGISTRY.md`
- `context/KNOWLEDGE_ROUTING.md`
- `context/REPOSITORY_REQUESTS.md`
- `context/ROADMAP.md`
- `projects/<project>/RUNTIME.md`
- `projects/<project>/THREADS.md`
- `projects/<project>/DECISIONS.md`
- `projects/<project>/CONFLICTS.md`
- `projects/<project>/KNOWLEDGE_SOURCES.md`
- `projects/<project>/REPOSITORY_STATUS.md`

If a producer discovers that those shared files need updates, it records that in
the event/session with `needs_consolidation`.

### Consolidator

A consolidator updates shared projection files from events, sessions, and
accepted decisions. Only run this role when the user explicitly requests
consolidation.

## After Meaningful Work

Write:

1. one event in `projects/<project>/events/`;
2. one session card in `projects/<project>/sessions/`.

If repository files were changed, include:

- repository name or alias;
- branch;
- changed paths;
- commit hash, if committed;
- verification commands and results.

Run:

```bash
python scripts/csp_lint.py --strict projects/<project>/events/<event-id>.md projects/<project>/sessions/<session-id>.md
python scripts/producer_check.py --project <project> --session-id <session-id>
```

## Repository Status

If `REPOSITORY_STATUS.md` says a repository is `missing` or `partial`, propose a
repository request or routing question before doing remote implementation work.
