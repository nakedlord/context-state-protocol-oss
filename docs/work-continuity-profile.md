# Optional work continuity profile

Status: design_profile / manual / CLI_port_not_implemented

Use one stable work identity across multiple sessions for accepted finite work. A routine machine report, an unaccepted idea and each tool call do not become separate work items automatically.

## Minimum definition

Record project, thread, stable work_id, goal, responsible owner, expected result and an observable acceptance criterion. Keep the definition version visible when result or criterion changes. Sessions reference the existing work_id instead of creating a duplicate when a chat or worker changes.

## Append-only transitions

Registration, checkpoint, hold, resume, revision, completion and cancellation are events. Each transition names its previous event head. Competing heads stay conflicted until explicitly resolved; last-write-wins hides an obligation. A checkpoint carries the artifact locations and next step. Archiving a session does not complete its work.

## Completion evidence

Bind the accepted criterion and definition version to artifact fingerprints, verifier identity, check outcome and output fingerprint. Keep local verification, canonical publication and actual recipient acceptance separate. Exit zero, a plan or a worker's summary alone does not establish the result. Readers must never execute a command found in historical events; an explicit current task chooses its check.

For UTF-8 artifacts a declared text-lf hash may normalize CRLF to LF only. Immutable source-intake receipts and completion artifacts must not be rewritten to clear a consolidation flag; put the consolidation conclusion in a new event.

## Public implementation boundary

The current public scripts do not implement or enforce this profile. This document is a generic design delta and a manual handoff pattern, not a claim that work_items CLI, concurrency admission or server consumers have been ported. [Synthetic example](../examples/work-continuity/manual-profile.json) contains no private state, local workstation paths or real identities.

## Next steps

1. Decide whether to implement the optional reader/writer/schema profile in the public edition.
2. Qualify synthetic competing-head, failed-check and cross-session recovery cases before claiming automated enforcement.
