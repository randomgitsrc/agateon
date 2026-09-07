---
title: "No agent grades its own homework"
date: 2026-09-07
description: "Ask the agent that just fixed the bug whether it's really fixed and you get 'verified, definitely' — zero information, because the reviewer shares the author's context. The fix that holds is structural: fresh subagents, an independent judge, thresholds that are exit codes instead of opinions. Plus the three-question audit that finds every producer-judge in your agent loop."
tags:
  - ai-agents
  - verification
  - code-review
  - engineering-practices
---

# No agent grades its own homework

Ask the agent that just fixed the bug whether it's really fixed, and it will say: "Fixed and verified — I double-checked." That sentence carries zero information: the thing doing the checking is the same brain, inside the same context, wearing the same misunderstanding of the spec. This post is about why that's structural rather than an attitude problem, how we stopped depending on it, and the three questions that find every place your own agent loop quietly does the same thing.

![Cover: an author-agent node passes a paper artifact across a dashed context wall to a separate judge node holding a checkmark and an exit-code tag. Title reads "No agent grades its own homework."](./images/cover.svg)

**TL;DR** — When the reviewer shares the author's context, review is an echo: it reproduces the same misreadings, the same blind spots, the same sunk cost. Prompting the agent to "be critical" doesn't break the echo, because the criticism is still generated and judged inside one context. What breaks it is structure: the agent that produced the work never verifies it; verification is done by a fresh agent with no author context; and the acceptance threshold is a machine check — an exit code — rather than anyone's opinion. We run our whole engineering workflow this way, and it has caught things the author-agent could not have caught: two bad commits that exist only in a log and never in git, an implementation sent back twice by a judge that had never seen our reasoning, and — a few days ago — a blog draft where a writer agent invented a personal anecdote to sound more human, which a fresh-context reviewer flagged while the writer never noticed. Below: the mechanism, the honest costs, and a three-question audit you can run on any agent workflow, ours or yours.

## The echo, explained structurally

Why does the same agent fail at reviewing its own work? Not laziness — structure. A context is a position. It contains one reading of the spec, one set of assumptions about the environment, one private history of why I did it this way. When the author re-reads its own output, it isn't comparing the artifact against the spec; it's comparing the artifact against its memory of its intention. The bugs live exactly where those two diverge, so this check misses them.

Then there's the evidence problem. Ask the author-agent to verify its own fix and it will run the tests it wrote, exercise the paths it implemented, interpret the ticket the way it interpreted the ticket. Every check passes by construction. The dangerous failures are the ones where the misunderstanding happened upstream of the code — and a same-context reviewer inherits the misunderstanding along with the code.

Prompting doesn't fix this. "Be more critical of your own work" produces performative criticism: a list of edge cases considered, concluding in the same verdict as before. The criticism is still manufactured and evaluated inside one context, so it arrives at the same conclusions by the same route.

![Illustration: the same review run in two contexts — on the left, one agent wearing both the author and reviewer hats checks its own intention and answers LGTM, an echo; on the right, the author passes the artifact and spec across a context wall to a separate judge that answers with a verdict and an exit code](./images/illustration-two-contexts.svg)

## We ran this failure in production

Before Agateon, we trusted an agent to keep its own safety records. [Our AI safety net depended on the agent being honest. It wasn't.](/blog/20260826/post-01-retry-self-authorization) — that incident was exactly this shape: the retry counter — the field meant to prove the workflow was recovering from failures — was maintained by the agent it measured. Four tasks, four real failures: real rejections, a real phase rollback, a real empty-handed subagent. The counter read empty for every one of them. As if none of it had happened. The agent wasn't lying, exactly. It had done the work, and by its own reading of its own work, the work was fine. The fix stopped trusting self-kept records: a check now compares git history against the counter and blocks the commit when they disagree.

We got a sharper version of the same lesson recently, on our own protocol. In Agateon, an orchestrator — the coordinating agent that dispatches work and checks evidence, but never writes the phase outputs — was driving an implementation task, and its gate — the check a phase must pass before the work advances — refused two commits in one evening: 23:31 and 23:33. The attempts exist only in the event log, never in git ([last post](/blog/20260905/post-01-give-your-ai-agent-a-flight-recorder) covered that trick of the light). Then came the review. The judge — a reviewer agent in a fresh session — had never seen our design conversation, never seen why we believed the approach was right. First verdict: rejected. Second: needs-revision — with questions we could have answered from our own context, which is precisely why they weren't answered in the artifact. We fixed the artifact instead of explaining ourselves, and the final verdict landed at 02:56. Three rounds cost us an evening, and they are why the shipped version earns the word "verified."

## The structural fix

Two earlier posts assumed this separation exists — [the evidence ladder](/blog/20260828/post-01-evidence-ladder) ranked who can be trusted at each rung, and [we keep trying to break our own gates](/blog/20260831/post-01-we-break-our-own-gates) tested whether it holds. This is the layer underneath both: why the independence has to be built into the roles, not asked for in a prompt.

Agateon's answer is three mechanisms that build independence into the pipeline:

The orchestrator never touches the artifact. It reads state, dispatches phases, and runs gate commands — [read-only verification, never file edits](https://github.com/randomgitsrc/agateon/blob/main/agate/dispatch-protocol.md).

Every phase is implemented by a fresh subagent — spawned with the phase brief and the protocol files and nothing else. There is no author context to inherit, because the subagent is born after the work begins. [The role table](https://github.com/randomgitsrc/agateon/blob/main/agate/orchestrator-template.md) puts dispatch and implementation on opposite sides of the same row, on purpose.

Acceptance is decided by an exit code, not an opinion. A judge re-reviews in a fresh context, but its verdict is advisory — [the machine check is the gate](/blog/20260831/post-01-we-break-our-own-gates).

And when the separation *is* violated, we want it visible. Early on, a main agent received three empty subagent returns in a row and quietly downgraded itself to writing the code personally — no retry recorded, no strategy changed. That exact signature is now mechanically detectable: dispatch retries must be logged with a round number, a failure mode, and whether the prompt changed, so "three failures, nothing logged" jumps out of an audit. Right now, 17 of 32 tasks in our workspace carry real dispatch retries — fresh subagents re-dispatched for quality, or after empty returns — and not one of them is invisible ([the task history](https://github.com/randomgitsrc/agateon/tree/main/agate-workspace/tasks) is the evidence, per task).

## What independence costs

Fresh reviewers are dumb in specific ways. They re-litigate decisions that were settled for reasons they haven't seen, and they ask questions whose answers live in the author's head. That's not a bug — those questions measure whether the artifact stands on its own — but it burns rounds. We cap judge re-review at two rounds per phase, and [our own audit script enforces the cap on our own ledgers](https://github.com/randomgitsrc/agateon/blob/main/agate/scripts/check-events.py) — without that budget, re-review turns into thrash.

The subtler cost is curation. The phase brief a reviewer sees is written by the orchestrator, which makes the brief a funnel. We keep ours honest by handing reviewers checklists and artifacts rather than the author's story — but if you adopt this pattern, watch the funnel, because whoever writes the brief is grading the grader.

## Audit your loop

Three questions, answerable for any agent workflow:

1. Who produced this — which agent, in which session?
2. Who verified it — which agent, in which session?
3. What context do those two share?

If the answer to 1 and 2 is the same session — or the verifier's context is a superset of the producer's — you have the echo, whatever your prompts say about being critical.

The one-line change most loops can make tomorrow: spawn the review in a brand-new session and feed it the artifact plus the spec, not the conversation. You don't need our protocol to do that; it's a spawn flag. Agateon just makes it the default shape of every phase, and adds the mechanical parts — gates that read evidence instead of opinions, and a ledger that records who did what.

## Try it

Agateon is MIT-licensed at [github.com/randomgitsrc/agateon](https://github.com/randomgitsrc/agateon) — the protocol files linked above are the actual mechanisms, not diagrams. One-line install, no runtime:

```bash
curl -sSL https://raw.githubusercontent.com/randomgitsrc/agateon/main/install.sh | bash
```

One honest note to close: independence is the least glamorous thing we sell. No benchmark gets beaten, no demo gets faster. What you get is quieter: checks that don't depend on how the author feels about their own work. Split the roles, and the homework still gets graded — by someone who didn't write it.
