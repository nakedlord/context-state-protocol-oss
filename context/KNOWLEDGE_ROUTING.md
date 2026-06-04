# Knowledge Routing

Use this file to decide where source material belongs.

| Source Type | Route To | Default Mode | Notes |
|---|---|---|---|
| CSP protocol idea | `csp-system` | producer | Record as event/session, then consolidate if accepted. |
| CSP script or guardrail change | `csp-system` | implementer | Update repository files and leave a trace. |
| Synthetic demo source | `example` | producer | Keep examples free of private or real customer data. |
| Unknown durable source | routing question | read_only | Do not force it into a nearby project. |

## Rules

- Prefer explicit project aliases over fuzzy routing.
- If no alias fits, create a routing question.
- Do not import raw private data into public examples.
