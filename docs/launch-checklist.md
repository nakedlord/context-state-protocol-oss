# Launch Checklist

Run this before posting CSP to a public community.

## Repository

- [ ] README explains the problem in the first screen.
- [ ] Quickstart works from a fresh clone.
- [ ] Demo link works.
- [ ] CI is green.
- [ ] License, security, contributing, and code of conduct files exist.
- [ ] GitHub description and topics are set.
- [ ] No private project names, local paths, raw exports, or secrets are present.

## Commands

```bash
python scripts/csp_lint.py --strict
python scripts/build_runtime.py projects/csp-system --check
python scripts/build_runtime.py projects/example --check
python scripts/task_packet_check.py --example --project csp-system --mode producer
python scripts/csp_status.py --overview
```

Privacy scan pattern:

```bash
rg -n "<local-path>|<private-repo>|<customer-name>|<credential-pattern>" .
```

## Posting

- [ ] Post one community at a time.
- [ ] Use the platform-specific draft from `docs/platform-posts.md`.
- [ ] Link directly to the demo when useful.
- [ ] Ask for feedback, not stars.
- [ ] Capture useful criticism as issues or follow-up docs.

## First Feedback To Collect

- Was the problem immediately clear?
- Did people understand why this is a protocol rather than an app?
- Did they ask for more examples?
- Did they object to manual files?
- Did they compare CSP to existing tools or patterns worth studying?
