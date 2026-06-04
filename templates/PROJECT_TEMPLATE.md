# New CSP Project

1. Copy `projects/_template` to `projects/<project-alias>`.
2. Replace placeholder values in every file.
3. Add the alias to `context/GLOBAL_INDEX.md`.
4. Add repository routing to `context/REPOSITORY_REGISTRY.md`.
5. Add source routing to `context/KNOWLEDGE_ROUTING.md` when needed.
6. Record the first event/session pair.
7. Run:

```bash
python scripts/csp_lint.py --strict
python scripts/build_runtime.py projects/<project-alias>
python scripts/csp_status.py --project <project-alias>
```
