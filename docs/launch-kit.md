# Launch Kit

Use this file when presenting CSP on GitHub, Hacker News, Reddit, newsletters,
grant forms, or maintainer programs.

## One-Line Pitch

Context State Protocol is a repo-native memory and handoff protocol for
long-running AI agent work.

## Short Pitch

AI agents are good at isolated tasks but fragile across sessions. They forget
decisions, project routing, source status, and write boundaries. CSP stores that
operational state in a repository: agents read a small map before meaningful
work, write append-only events after work, and leave durable decisions to
explicit consolidation.

## Who It Is For

- OSS maintainers using Codex, ChatGPT, Claude Code, or local coding agents.
- Teams with multiple repositories and long-running agent sessions.
- People ingesting source-backed knowledge into durable project archives.
- Maintainers who need a clear public/private boundary for agent memory.

## Core Claims

- CSP is a protocol skeleton, not a hosted SaaS.
- It uses plain Markdown and small Python scripts.
- It is designed for auditability and handoff, not hidden agent autonomy.
- Private working state should not be published directly; clean exports should
  use new git history and synthetic examples.

## Hacker News Draft

```text
Show HN: Context State Protocol - repo-native memory for long-running AI agents

I built CSP after repeatedly running into the same problem with coding agents:
they can do useful work in one session, but continuity across sessions is
fragile. They forget decisions, routing, source status, and write boundaries.

CSP is a small repo-native protocol: agents read a project map before meaningful
work, write append-only event/session records after work, and leave durable
state updates to explicit consolidation.

It is just Markdown plus small Python checks. No server, no database, no hidden
memory. The public repo is a clean export with synthetic examples because real
CSP state can contain private operational context.

Repo: https://github.com/nakedlord/context-state-protocol-oss
```

## Reddit Draft

```text
I made a repo-native continuity protocol for AI coding agents

The problem: AI agents are useful for individual tasks, but long-running work
gets messy. The next session often has to rediscover project routing, decisions,
source status, and what it is allowed to edit.

Context State Protocol stores that state in a repo. Agents read a compact map
before meaningful work, then append event/session records after work. Shared
state is updated only by an explicit consolidation role.

It is intentionally boring: Markdown files, small Python scripts, CI checks,
synthetic examples, and a public/private export boundary.

Repo: https://github.com/nakedlord/context-state-protocol-oss
```

## Grant / Program Pitch

```text
Context State Protocol is an open-source protocol and toolset for durable AI
agent project state. It helps maintainers preserve routing, decisions, events,
sessions, source status, and safe write boundaries across long-running Codex and
multi-agent workflows. Support would be used to harden the public protocol,
improve examples and validation scripts, run security/privacy reviews, and make
the project useful for other OSS maintainers.
```

## Launch Checklist

- README has a clear first-screen promise.
- Quickstart works from a fresh clone.
- Demo explains the continuity loop.
- CI is green.
- License and contribution files exist.
- Security and public export boundaries are documented.
- GitHub topics are set.
- First issues are beginner-friendly.
- Launch posts link to a specific demo, not only the repo root.
