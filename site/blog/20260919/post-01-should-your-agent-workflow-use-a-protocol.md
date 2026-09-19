---
title: "Should your agent workflow use a protocol at all?"
date: 2026-09-19
description: "A decision framework for how much process your agent workflow actually needs: score the evidence instead of trusting anyone's complexity claim, make the claim checkable in one direction, and know when to skip all of it. Includes a five-signal rubric you can compute from a diff today."
tags:
  - ai-agents
  - engineering-practices
  - orchestration
  - verification
---

# Should your agent workflow use a protocol at all?

Adding process to an agent workflow is a trade: you pay a known cost in time and attention now, against failures that don't happen later. Both directions of that trade go wrong. Too much process and your agents spend their budget writing status reports; too little and you discover at the end that "done" meant "the agent stopped talking."

![Cover: a task card sits on a balance; on the left pan, a short path through three gates; on the right pan, a long path through eight phases. A teal scoring node with three evidence lines tips the balance toward the short path. Title reads "Should your agent workflow use a protocol at all?"](./images/cover.svg)

**TL;DR** — The decision is usually made by feel — either the agent's feel about its own task, or yours about the size of the diff — and both are unreliable in the same direction. Score the evidence instead: five signals read off a diff (file type, sensitive paths, change size, reverse-reference impact, domain markers) tell you whether a change deserves a light path, a standard one, or the full treatment. Then make the claim checkable in one direction: anyone may ask for *more* rigor than the evidence supports, and asking for less is blocked. The rubric needs nothing from us — you can compute all five signals from `git diff --cached` and a grep, in a spreadsheet, this afternoon. The rest of this post is that rubric, the one-way rule, what the whole thing cost us, and the cases where you should skip it and write a script.

## Complexity claims are unreliable in one direction

The obvious way to size a task is to ask the agent how complex it is. That fails, and not because agents lie: an agent will call a one-line fix "architecturally significant" if that framing sounds like diligence. Self-reported complexity drifts toward whatever the reporter believes is expected.

The human version is subtler and worse. We skip process because the change "looks small" — and size is genuinely easy to eyeball while risk is not. A four-line change to an auth check and a four-line change to a log message are indistinguishable in a diff stat. Both estimates fail the same way: they read the visible surface and miss the connections.

Our own task briefs show the same failure in miniature. When I checked the brief for one of our batches, it cited line numbers for a CI script and a count of evidence files. Both were wrong — the lines had shifted by four, the count was off by five. Nobody was lying and nobody was careless in an obvious way; the numbers had been recalled instead of re-read. If a number in a document you wrote yourself can drift that easily, a complexity estimate produced from memory at planning time is not a basis for deciding how much process to apply.

## Five signals, read off the diff

Score the change on five signals, each computed rather than asserted:

| signal | what it reads | high when |
|---|---|---|
| file-type | staged paths | core/shared code or build/CI config touched |
| sensitive-path | path keywords | security, auth, permission, data-model |
| change-size | count of staged source files | more than five |
| impact | reverse references | a changed module is imported elsewhere in the repo |
| domain-markers | declared domains | annotation only — does not set the level |

The composition rule is deliberately boring and binary: any high signal makes it `full`; all low makes it a `light` candidate; everything else is `standard`. No numeric threshold decides the level, because a threshold just moves the argument to where the line sits.

Every signal is objective, which is what makes this portable — you can run it by hand before deciding, in a pre-commit hook, or in a spreadsheet. And the signals are local: if your repo has a directory that is always dangerous, add it to the sensitive-path list. The rubric is the idea; the keywords are yours.

We implemented ours as [`agate-risk-score.py`](https://github.com/randomgitsrc/agateon/blob/main/agate/scripts/agate-risk-score.py). Its verbatim output for a recent infrastructure-hardening task (no staged changes at scoring time) looks like this — the evidence lines are in Chinese; the structure is the point:

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

The last line is the part worth copying into any scorer you build. If git can't be read, the tool does not quietly return a friendly default — it reports `git_ok: false` and the consumer treats that as a failure. A score that cannot be computed tells you nothing about risk, so it must not be readable as a low one. The failure mode of a scorer has to be loud, not permissive.

![Illustration: five evidence signals (file-type, sensitive-path, change-size, impact, domain-markers) feed a level decision — light, standard, or full; from there a declaration may ask for more rigor than the score requires, while asking for less is blocked. A bottom band compares the cost (median 21 hours, 13 commits, ~6,700 lines of artifacts) with what it catches (119 gate runs, 3 real blocks).](./images/illustration-scoring.svg)

## Make the claim checkable, one way

Scoring is half the mechanism. The other half is that whoever declares the process level has to declare it *against* the score.

You may always choose *more* rigor than the score requires: declaring `full` on a task scored `light` is your prerogative and costs you only time. Choosing the *light* path when the score says `standard` or `full` is blocked — the check compares the declaration to the computed level, exits 1, and the task does not move. In our implementation the middle case is not enforced yet: declaring `standard` on a task scored `full` passes the check today, so the extra obligations a `full` score implies are not mechanically forced. That gap is real, and naming it matters more than the slogan — "one-way check" is what the code does; "never less" would be claiming more.

The portable version is one sentence: a process-depth claim should be checkable against evidence, and an unverifiable claim should default to more rigor. That is also what ends most process arguments. The disagreement stops being "do we need this?" and becomes "here are the five evidence lines, which one is wrong?"

## What it costs, and how to price your own

You should not adopt process on someone else's numbers, but ours are useful as a scale check. Across 37 tasks in our workspace:

| measure | median | note |
|---|---|---|
| wall-clock span | ~21 hours | first to last commit touching the task |
| commits | 13 | up to 44 |
| phase artifact lines | ~6,700 | across ~37 documents |
| dispatch retries | 19 of 37 tasks | at least one recorded retry |

Read that as a warning rather than a pitch. The span is not the agent's runtime — it is elapsed calendar time, and most of it is waiting for a human to look at something. So the price of process is not compute; it is attention, spent at gates along the way instead of in one review at the end. Nothing here makes an agent faster or a task finish sooner. If your problem is throughput, this is the wrong tool.

To price your own, measure three things for a week before deciding anything:

1. **How long does a task take from first commit to last**, and how much of that is waiting on a human?
2. **How many commits does one task take**, and how many are fixes to something already "done"?
3. **How often does a task come back wrong after you accepted it**, and what did each of those cost?

If the third answer is "rarely, and cheaply," stop here. Process is insurance, and you don't buy insurance against losses you can absorb.

For scale, our append-only event log records 119 gate runs: 115 ended in the pass code for that phase, one passed with a warning, and 3 were real blocks. Two tasks were ever actually stopped by a gate — and the honest denominator is the 14 tasks that have a log at all, since the ledger only arrived partway through the repo's history. A gate that fires rarely is working as intended, but nobody should adopt one expecting dramatic saves. What it covers is the failures you cannot see coming.

## When not to use any of this

- **One-shot scripts and small fixes.** If the whole change fits in one commit you would review in five minutes, a multi-phase pipeline is pure overhead. Write the script, run the tests, ship it.
- **Work with no machine-checkable signal.** The leverage comes from gates reading exit codes and diffs. If your definition of done is "the design doc reads well," there is nothing for a gate to hold onto, and you would be paying ceremony cost for the parts that don't help.
- **Exploration and spikes.** Research tasks have no acceptance criteria to verify against; scoring one produces a level that means nothing. Timebox the spike, throw it away, then run the real task through gates.
- **When you cannot afford the attention.** The cost is human, not compute. If nobody can look at gates this week, they become a queue you skip — and a skipped gate is worse than no gate, since the artifacts still record that verification happened.
- **When you need cross-machine reproducibility.** Our routing and scoring config are deliberately per-machine and opportunistic. If two engineers must get byte-identical pipelines, that design choice is against you.

## Before you decide

Four questions, answerable for your own setup:

1. **What does "done" look like as a machine-checkable signal** — an exit code, a diff, a count? If you cannot name it, no amount of process will save you.
2. **How often does your agent come back wrong now, and how do you know?** If you cannot answer the second half, you are deciding from memory, which is the mistake this whole post is about.
3. **What does one bad output cost you** — a re-run, a broken build, a production incident, a customer-visible lie?
4. **Who reads the gates?** Name the person. If it is "nobody, we trust the green check," you have bought ceremony without verification.

If 1 and 2 have crisp answers and 3 is expensive, process like this earns its keep. If 3 is cheap, or 4 has no name, skip it: a script plus a code review is the right answer for that work.

## If you want the implementation

The rubric above needs nothing from us — five signals, a spreadsheet, and the one-way rule. If you would rather have it as running code, Agateon is MIT-licensed and the scorer is a single script you can read in one sitting: [github.com/randomgitsrc/agateon](https://github.com/randomgitsrc/agateon).

```bash
curl -sSL https://raw.githubusercontent.com/randomgitsrc/agateon/main/install.sh | bash
```

Make your process-depth claims checkable, and make the check fail toward rigor. That part works whether or not you ever install anything.
