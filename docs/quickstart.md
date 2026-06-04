# Quickstart

This guide creates a new CSP project and validates it locally.

## 1. Clone

```bash
git clone https://github.com/nakedlord/context-state-protocol-oss.git
cd context-state-protocol-oss
```

## 2. Inspect Current State

```bash
python scripts/csp_status.py --overview
python scripts/csp_status.py --project example
```

## 3. Create A Project

```bash
cp -r projects/_template projects/my-project
```

Replace placeholder values in:

- `projects/my-project/CONTEXT_CAPSULE.md`
- `projects/my-project/THREADS.md`
- `projects/my-project/DECISIONS.md`
- `projects/my-project/CONFLICTS.md`
- `projects/my-project/KNOWLEDGE_SOURCES.md`
- `projects/my-project/REPOSITORY_STATUS.md`

Add the project alias to:

- `context/GLOBAL_INDEX.md`
- `context/REPOSITORY_REGISTRY.md`
- `context/KNOWLEDGE_ROUTING.md`, if source routing is needed

## 4. Add The First Event

Create:

```text
projects/my-project/events/YYYY-MM-DD-agent-short-title.md
projects/my-project/sessions/YYYY-MM-DD-agent-short-title.md
```

Use:

- `templates/EVENT_TEMPLATE.md`
- `templates/SESSION_CARD_TEMPLATE.md`

## 5. Rebuild Runtime

```bash
python scripts/build_runtime.py projects/my-project
```

## 6. Validate

```bash
python scripts/csp_lint.py --strict
python scripts/csp_status.py --project my-project
```

For ordinary producer sessions:

```bash
python scripts/producer_check.py --project my-project --session-id YYYY-MM-DD-agent-short-title
```

## 7. Give Agents The Entry Contract

Use this prompt:

```text
Use Context State Protocol. Read AGENTS.md, context/GLOBAL_INDEX.md,
context/REPOSITORY_REGISTRY.md, context/KNOWLEDGE_ROUTING.md,
context/REPOSITORY_REQUESTS.md, then select the project and read its capsule,
runtime, threads, decisions, conflicts, knowledge sources, and repository
status. After meaningful work, write one event and one session card.
```
