# Write Discipline

CSP is useful only if write ownership stays boring and predictable.

## Producer Writes

A producer may write:

- `projects/<project>/events/*.md`
- `projects/<project>/sessions/<session-id>.md`

It must not edit shared projections directly.

Use:

```bash
python scripts/producer_check.py --project <project> --session-id <session-id>
```

## Shared Projection Writes

Shared files are maintained by consolidation:

- `context/*.md`
- `projects/<project>/RUNTIME.md`
- `projects/<project>/THREADS.md`
- `projects/<project>/DECISIONS.md`
- `projects/<project>/CONFLICTS.md`
- `projects/<project>/KNOWLEDGE_SOURCES.md`
- `projects/<project>/REPOSITORY_STATUS.md`

When a producer sees that one of these files needs an update, it records
`needs_consolidation` in the event or session body.

## Repository Writes

If the task changes a product or knowledge repository, the event should include:

- repository alias;
- branch;
- changed paths;
- commit hash, when available;
- checks run.
