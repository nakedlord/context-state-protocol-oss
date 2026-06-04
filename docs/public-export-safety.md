# Public Export Safety

Do not make a private CSP working repository public directly.

Private CSP history may contain:

- local paths;
- private repository names;
- private project aliases;
- raw chat export fragments;
- business operations;
- personal records;
- health or financial context;
- source-processing traces;
- decisions that were never meant to be public.

## Safe Export Pattern

1. Create a new empty directory.
2. Copy only generic protocol files.
3. Recreate examples with synthetic data.
4. Add a new license and public README.
5. Run a privacy scan.
6. Initialize a new git repository.
7. Publish only the clean repository.

## Suggested Privacy Scan

Tune the patterns to your environment:

```bash
rg -n "<local-path>|<private-repo>|<customer-name>|<credential-pattern>" .
rg --files | rg "__pycache__|\\.pyc|exports?|transcripts?"
```

False positives are normal. The important thing is to read them before
publishing.
