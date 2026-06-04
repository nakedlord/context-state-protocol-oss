# OSS Grant Packet

Reusable material for grants, credits, and maintainer-support programs.

## Repository

`https://github.com/nakedlord/context-state-protocol-oss`

## Project Summary

Context State Protocol is a repo-native memory and handoff protocol for
long-running AI agent work. It lets agents recover project routing, decisions,
threads, source status, conflicts, repository boundaries, and next actions from
source-controlled state rather than fragile chat memory.

## Why It Matters

AI agent workflows increasingly span many sessions, repositories, and tools.
Without durable state, agents repeat discovery work, overwrite context, mix
private and public data, or lose the rationale behind decisions. CSP addresses
that gap with plain files, append-only traces, generated runtime views, and
explicit producer/consolidator roles.

## Current Stage

- Public clean export published.
- Synthetic example project included.
- Local validation scripts included.
- GitHub Actions CI included.
- Public/private export safety documented.

## What Support Would Enable

- Better examples for real maintainer workflows.
- Stronger privacy and security checks.
- More robust validation scripts.
- Agent-specific setup guides for Codex, ChatGPT, Claude Code, and local coding
  agents.
- Documentation and launch materials for wider OSS use.

## API Credit Use Plan

API credits would be used for:

- testing multi-agent continuity workflows;
- generating and validating task-packet examples;
- stress-testing source ingestion and summarization flows;
- creating security/privacy review passes over synthetic and public examples;
- improving agent-facing documentation and release notes.

Credits would not be used to process private data in the public repository.

## Security Rationale

CSP is not a security scanner, but security is central to the protocol. Durable
agent state can accidentally expose private context or grant unsafe write
authority. CSP therefore emphasizes:

- public/private export boundaries;
- append-only producer traces;
- explicit consolidator role;
- validation scripts;
- no hidden autonomy or mutation runners in the public edition.

## Maintainer Role

The maintainer is developing CSP from real long-running agent workflows, then
publishing a clean public edition with synthetic examples so other maintainers
can adapt the protocol without inheriting private state.
