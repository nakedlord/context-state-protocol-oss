# Contributing

Thanks for helping improve Context State Protocol.

This repository is intentionally small and text-first. Contributions are most
useful when they improve the protocol, examples, validation scripts, or safety
boundaries without adding heavy runtime dependencies.

## Good First Contributions

- clearer docs;
- more example projects;
- stricter lint checks;
- task packet examples;
- agent-specific setup notes;
- privacy and public export checks.

## Development Checks

Run from the repository root:

```bash
python scripts/csp_lint.py --strict
python scripts/build_runtime.py projects/example --check
python scripts/build_runtime.py projects/csp-system --check
python scripts/task_packet_check.py --example --project csp-system --mode producer
python scripts/csp_status.py --overview
```

## Pull Request Notes

Please include:

- what changed;
- why it matters;
- checks run;
- whether the change affects agent write boundaries.

Do not include private project context, local paths, secrets, customer data,
health data, personal records, or exported chat transcripts.
