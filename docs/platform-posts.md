# Platform Posts

Use these drafts when launching CSP publicly. The goal is feedback and early
users, not a one-day spike.

## Order

1. Hacker News: broad devtool feedback.
2. Reddit `r/ChatGPTCoding`: practical AI-coding workflow angle.
3. Reddit `r/LocalLLaMA`: agent-memory / local workflow angle.
4. Reddit `r/opensource`: maintainer/process angle.
5. X / LinkedIn: concise thread linking to the repo and demo.
6. Newsletters / curated lists after the first feedback loop.

Wait at least a few hours between communities. If feedback reveals confusion,
fix README/docs before the next post.

## Hacker News

HN usually works best as a URL submission.

Title:

```text
Show HN: Context State Protocol - repo-native memory for long-running AI agents
```

URL:

```text
https://github.com/nakedlord/context-state-protocol-oss
```

First comment:

```text
I built CSP after repeatedly running into the same problem with coding agents:
they can do useful work in one session, but continuity across sessions is
fragile. The next session often has to rediscover decisions, repo routing,
source status, and write boundaries.

CSP is a small repo-native protocol: agents read a project map before meaningful
work, write append-only event/session records after work, and leave durable
state updates to explicit consolidation. It is Markdown plus small Python
checks, not a hosted service.

The public repo is a clean export with synthetic examples because real CSP state
can contain private operational context. I am especially looking for feedback
from maintainers using Codex, Claude Code, ChatGPT, or local coding agents
across long-running projects.
```

What to watch:

- Do people understand the problem from the title?
- Do they ask for a demo rather than a protocol?
- Do they object to Markdown/state files as too manual?
- Do they compare it to ADRs, runbooks, memory systems, or agent frameworks?

## Reddit: r/ChatGPTCoding

Title:

```text
I made a repo-native continuity protocol for AI coding agents
```

Body:

```text
I kept running into the same issue with AI coding sessions: the agent can make
progress in one chat, but the next session has to rediscover project routing,
decisions, source status, and what it is allowed to edit.

So I made Context State Protocol (CSP). It is intentionally boring: Markdown
state files plus small Python checks. Agents read a compact project map before
meaningful work, then append event/session records after work. Shared state is
updated only by an explicit consolidation role.

Repo: https://github.com/nakedlord/context-state-protocol-oss
Demo: https://github.com/nakedlord/context-state-protocol-oss/tree/main/examples/agent-continuity-demo

I am looking for feedback from people who use Codex, ChatGPT, Claude Code, or
other coding agents on projects that last more than one session.
```

## Reddit: r/LocalLLaMA

Title:

```text
Repo-native memory for long-running local/AI agent workflows
```

Body:

```text
Most agent memory discussions focus on vector search or chat history. I wanted
something simpler and more auditable for long-running coding/project work:
state that lives in the repository.

Context State Protocol (CSP) is a small file protocol where agents read project
routing/state before work and append event/session records after work. It does
not try to be hidden memory or autonomous execution. It is closer to a durable
handoff layer for agents.

Repo: https://github.com/nakedlord/context-state-protocol-oss

I would be interested in feedback from people running local agents or multi-agent
workflows: where would this be too manual, and where would it save context
recovery time?
```

## Reddit: r/opensource

Title:

```text
Context State Protocol: durable project state for OSS maintainers using AI agents
```

Body:

```text
I published a small OSS protocol for maintainers using AI coding agents across
long-running projects.

The problem: agent work often leaves decisions, routing, and source status in a
chat transcript. The next session can lose context or touch the wrong files.

Context State Protocol keeps that operational state in a repository. Agents read
the project map before meaningful work, append event/session records after work,
and leave durable shared-state updates to explicit consolidation.

Repo: https://github.com/nakedlord/context-state-protocol-oss

It is early and intentionally plain: Markdown, Python checks, CI, and synthetic
examples. I would appreciate feedback on whether this maps to real maintainer
workflows and what examples would make it easier to adopt.
```

## X / Twitter

```text
I published Context State Protocol: repo-native memory + handoff for long-running AI agent work.

Problem: coding agents make progress in one session, then lose decisions, repo routing, source status, and write boundaries in the next.

CSP keeps that state in the repo:
- project maps
- decisions/conflicts
- events + session cards
- generated runtime views
- append-safe write discipline

Repo: https://github.com/nakedlord/context-state-protocol-oss
Demo: https://github.com/nakedlord/context-state-protocol-oss/tree/main/examples/agent-continuity-demo
```

## LinkedIn

```text
I published Context State Protocol, a small open-source protocol for durable AI
agent project state.

AI coding agents are increasingly useful for individual tasks, but long-running
work still breaks at the handoff layer: decisions stay in chat transcripts,
repository routing gets rediscovered, and write boundaries are easy to lose.

CSP stores that operational state in a repository. Agents read a compact project
map before meaningful work, append event/session records after work, and leave
durable state updates to explicit consolidation.

It is intentionally simple: Markdown, small Python checks, CI, synthetic examples,
and a public/private export safety boundary.

Repository: https://github.com/nakedlord/context-state-protocol-oss
```

## Follow-Up Reply

Use this when someone asks why this is not just `README.md` or ADRs:

```text
I see CSP as adjacent to ADRs/runbooks, but more operational. ADRs capture
decisions; CSP also tracks project routing, active threads, source status,
conflicts, repository boundaries, events, and session cards. The goal is not to
replace docs, but to give agents a predictable entry/exit contract for work that
spans sessions.
```

Use this when someone asks why not vector memory:

```text
Vector memory can be useful below CSP, especially inside a large knowledge repo.
But I did not want retrieval to decide source of truth or write authority. CSP is
structured state first; search can be an adapter later.
```

Use this when someone asks whether it is too manual:

```text
Yes, v0 is deliberately manual. The bet is that boring, inspectable state is the
right baseline before adding automation. The current scripts already validate
event/session shape, rebuild runtime views, and preview task packets.
```
