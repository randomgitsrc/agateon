---
title: "Should your agent workflow use a protocol at all?"
date: 2026-09-19
description: "Orchestration protocols add overhead — eight phases, an independent judge, a gate before every advance. Here is the decision framework we use ourselves: objective risk scoring instead of vibes, a rule that makes the ceremony claim checkable in one direction — with the gap in that check named out loud, our real cost numbers (median 21 hours elapsed, 13 commits, ~6,700 lines of artifacts per task), and the honest answer for when you should not use any of this."
tags:
  - ai-agents
  - engineering-practices
  - orchestration
  - verification
---

# Should your agent workflow use a protocol at all?

There are a lot of agent frameworks now, and most of them ask you to adopt something: a runtime, an SDK, a graph, a hosted service. Before you adopt anything, the question worth answering is smaller and harder: does my work actually need an orchestration layer? Getting this wrong is expensive in both directions — too much process and your agents spend their budget writing status reports; too little and you find out at the end that "done" meant "the agent stopped talking."

![Cover: a task card sits on a balance; on the left pan, a short path through three gates; on the right pan, a long path through eight phases. A teal scoring node with three evidence lines tips the balance toward the short path. Title reads "Should your agent workflow use a protocol at all?"](./images/cover.svg)

**TL;DR** — We built Agateon, and the honest answer to "should you use it?" is: not always, and the decision shouldn't be a vibe. Three terms first, since everything below turns on them: a *gate* is a check a phase must pass before the work may advance; *ceremony* is how much of that machinery a task runs through — thin, standard, or full; and *fail-closed* means that when a check cannot decide, it resolves toward blocking rather than allowing. Complexity claims from the agent itself are worthless — an agent will call a one-line fix "architecturally significant" if that sounds like diligence. So the ceremony depth is computed from git evidence instead: five signals (file type, sensitive paths, change size, reverse-reference impact, domain markers) produce a tier, and a gate checks the claim in one direction — you may always ask for *more* ceremony than the score requires; asking for the thin path against a higher score is blocked. Our own numbers, so you can price it: a task here has a median wall-clock span of about 21 hours and 13 commits, and leaves roughly 6,700 lines of phase artifacts behind. What that buys is 119 gate runs, of which 3 were real blocks — and 19 of 37 tasks carry at least one dispatch retry. Below: the scoring mechanism, the real costs, and the cases where you should skip all of it and write a script.

## Deciding by feel is how you get both failure modes

The obvious approach is to ask the agent how complex the task is. It doesn't work, and we have the receipts: the risk score exists because ceremony depth used to be self-reported, and self-reported complexity drifts toward whatever the agent thinks you want to hear. Ask a helpful agent whether a task needs the full eight-phase treatment and you will get a thoughtful, confident, ungrounded yes.

The other failure mode is the human version: skipping process because the change "looks small." Our own task briefs are the evidence. When I checked the brief for the gate-hardening batch, it cited line numbers for the CI backstop script and a count of evidence files; both were wrong — the lines had shifted by four and the count was off by five. Nobody was lying, and nobody was careless in an obvious way. The numbers had been recalled instead of re-read. That works right up until the small change touches an auth path, or the fix lands in a file eleven other modules import. Size and risk are different axes, and the second one is where memory-based estimates fail most often.

## Score the evidence, not the confidence

So the tier is computed. [`agate-risk-score.py`](https://github.com/randomgitsrc/agateon/blob/main/agate/scripts/agate-risk-score.py) reads the staged diff and scores five signals, each emitting its own evidence line rather than a bare number:

| signal | what it reads | high when |
|---|---|---|
| file-type | staged paths | protocol body or gate scripts touched |
| sensitive-path | path keywords | security, auth, permission, data-model |
| change-size | count of staged source files | more than five |
| impact | reverse references | a changed module is imported elsewhere in the repo |
| domain-markers | P1 declared domains | annotation only — does not set the tier |

The composition rule is deliberately boring and binary: any high signal makes it `full`; all low makes it a `thin` candidate; everything else is `standard`. No numeric threshold decides the tier — a threshold would just move the argument to where the line sits. Here is the verbatim output for a recent protocol-hardening task, with no staged changes at scoring time (the tool's evidence lines are in Chinese; the numbers are the point):

```text
risk_score: 6
tier: thin
file-type: low (无暂存改动)
sensitive-path: low (无暂存改动)
change-size: low (source files=0 <= 5)
impact: low (无反向引用)
domain-markers: [backend]
git_ok: true
```

![Illustration: five evidence signals (file-type, sensitive-path, change-size, impact, domain-markers) feed a tier decision — thin, standard, or full; from there a declaration may ask for more ceremony than the score requires, while asking for less is blocked, and the thin path still keeps P5 and P6. A bottom band compares the cost (median 21 hours, 13 commits, ~6,700 lines of artifacts) with what it catches (119 gate runs, 3 real blocks).](./images/illustration-scoring.svg)

Note the last line. If git can't be read, the tool does not quietly return a friendly default — it reports `git_ok: false`, and the consumer treats that as a failure. A score that cannot be computed tells you nothing about risk, so the tool refuses to let it be read as a low one.

## The claim is one-way

The scoring is only half the mechanism. The other half is that the declaration is checked against it — and here is exactly how far that check goes, including where it currently stops. You may always choose *more* ceremony than the score requires: declaring `full` on a task scored `thin` is your prerogative, and it just costs you time. Choosing the *thin* path when the score says `standard` or `full` is blocked — a gate compares the declaration to the computed tier, exits 1, and the task does not move. What is *not* enforced yet is the middle case: declaring `standard` on a task scored `full` passes the routing check today, so the extra obligations a `full` score implies are not mechanically forced. That gap is real, and naming it matters more than the slogan — "one-way check" is what the code does; "never less" would be claiming more.

Declaring thin is not a shortcut around verification, either. The declaration must arrive with four things at once: the explicit claim, a per-signal coupling checklist, a statement of what risk the skip introduces, and a phase list that still contains P5 and P6. Miss any one and the gate exits 1 and you silently fall back to standard. The thin path thins the ceremony — it never thins the verification.

This is the part worth stealing even if you never touch Agateon. The general property is simple: **a process-depth claim should be checkable against evidence, and an unverifiable claim should default to more rigor.** Most process debates die here: the disagreement stops being "do we need this?" and becomes "here are the five evidence lines, which one is wrong?"

## What it actually costs

Now the number that matters, measured from our own workspace rather than estimated. Across 37 tasks in `agate-workspace/tasks/`:

| measure | median | note |
|---|---|---|
| wall-clock span | ~21 hours | first to last commit touching the task |
| commits | 13 | up to 44 |
| phase artifact lines | ~6,700 | across ~37 `P*.md` files |
| dispatch retries | 19 of 37 tasks | at least one non-empty retry record |

That span is not the agent's runtime. It is elapsed calendar time, and most of it is waiting for a human to look at something. So the real price of the protocol is not compute — it is your attention, spent at gates along the way instead of in one review at the end. If your task is a two-hour change you would have reviewed once anyway, that trade is a straight loss.

The value side, from the append-only ledger, is smaller and stranger than a pitch would suggest. Of 119 gate runs recorded, **115 ended in the pass code for that phase** (exit 2 for most phases, exit 0 for P4/P7/P6.5), one passed with a warning, and **3 exited 1 — real blocks**. Exit 2 deserves a note: for most phases it *is* the pass code, not a skip. Two tasks were ever actually stopped by a gate — and the honest denominator is the 14 tasks that have a ledger at all, since the append-only event log only arrived partway through this repo's history. We wrote about that ratio before, and the picture has not changed: a gate that fires rarely is working as intended, but nobody should buy this expecting dramatic saves. What you are buying is coverage of the failures you cannot see coming — the self-reported counter that reads empty, the phase that quietly downgrades itself, the reviewer that shares the author's blind spot.

## When not to use any of this

- **One-shot scripts and small fixes.** If the whole change fits in one commit you would review in five minutes, an eight-phase pipeline is pure overhead. Write the script, run the tests, ship it.
- **Work with no machine-checkable signal.** The protocol's leverage comes from gates reading exit codes and diffs. If your task's definition of done is "the design doc reads well," there is nothing here for the gates to hold onto — you are paying the ceremony cost for the parts that don't help.
- **Exploration and spikes.** Research tasks have no acceptance criteria to verify against; scoring them produces a tier that means nothing. Timebox the spike, throw it away, then run the real task through gates.
- **When you cannot afford the attention.** The cost is human, not compute. If nobody can look at gates this week, the gates become a queue you skip — and a skipped gate is worse than no gate, since the artifacts still record that verification happened.
- **When you need cross-machine reproducibility.** The routing and scoring config are deliberately per-machine and opportunistic. If your requirement is that two engineers get byte-identical pipelines, this design choice is against you.

## The five-question checklist

Answer these before adopting anything, ours or otherwise:

1. **What does "done" look like as a machine-checkable signal** — an exit code, a diff, a count? If you can't name it, no protocol will save you.
2. **How often does your agent currently come back wrong**, and how do you know? If you can't answer the second half, you're deciding from memory — the same mistake the scoring exists to prevent.
3. **What is the cost of one bad output** in your context: a re-run, a broken build, a production incident, a customer-visible lie?
4. **Who reads the gates?** Name the person. If it's "nobody, we'll trust the green check," you've bought ceremony without verification.
5. **What would you have to delete** to adopt this? If the honest answer is "our existing test suite," stop — the gates amplify whatever signals you already have; they do not create new ones.

If questions 1 and 2 have crisp answers and 3 is expensive, a protocol like this pays for itself. If 3 is cheap, or 4 has no name, skip it: a script plus a code review is the right answer for that work.

## Try it

Agateon is MIT-licensed, and the scoring tool is a single script you can read in one sitting — [github.com/randomgitsrc/agateon](https://github.com/randomgitsrc/agateon):

```bash
curl -sSL https://raw.githubusercontent.com/randomgitsrc/agateon/main/install.sh | bash
```

If you only take one thing: make your process-depth claims checkable, and make the check fail toward rigor. That part works whether or not you ever install anything.
