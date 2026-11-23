---
title: "Where does your agent actually spend its time?"
date: 2026-11-23
description: "Three intuitions about agent cost that turn out to be wrong when you measure them on real session logs: a 9.6x context growth with no slowdown per step, tool calls nowhere near the bottleneck, and dispatch counts barely tracking code size. Plus a rule for deciding what to optimize — measure its share first."
tags:
  - ai-agents
  - performance
  - engineering-practices
  - measurement
---

# Where does your agent actually spend its time?

When an agent session feels slow, three explanations come to mind: the context got too long, the tools are slow, or the task was too big — each with an obvious fix, and each worth checking.

We had a chance to check all three against real session logs: 147 sessions, 13,578 steps, one project, from the runtime's own event stream. Two of the three explanations did not survive the measurement, and the third is weaker than it looks.

![Cover: a timeline of one agent session; the bar is almost entirely "model thinking" with a thin sliver labelled "tool calls", while a sidebar shows context growing from small to 9.6x with a flat line for per-step duration next to it. Title reads "Where does your agent actually spend its time?"](./images/cover.svg)

**TL;DR** — Measure before you optimize, because the three most plausible cost explanations are mostly wrong. In our logs, context grew 9.6x across a session while per-step duration stayed flat (correlation with log context: -0.03, i.e. none detectable); tool round-trips accounted for roughly a third of total step time but about 2% of the median step; and dispatch count tracked code size only loosely (r = 0.48 across a 100x range of change size). What follows is how to compute each of those on your own runtime, why the first one is the most counter-intuitive, and a decision rule: **estimate an item's share of total time before you decide to optimize it.** Below a few percent, optimizing it is a hobby, not an engineering decision.

## What the logs contain

An agent runtime that records its own event stream gives you three durations per step without any instrumentation of your own:

- a `step/start` timestamp, before the model begins thinking;
- an `assistant/message` timestamp, when the model's turn ends;
- `tool/call` and `tool/result` pairs inside the step, when the model asks for something and gets it back.

From those you can compute step duration (start to next start), the share of it spent in tool round-trips, and the context size the model saw on each step — most runtimes put a token count on the assistant message.

One caveat that shapes everything below: the numbers here come from **one project, one model, on one machine**. They are enough to show that the three intuitions are not safe defaults. They are not enough to give you your own numbers. The recipes below are for that.

## Intuition one: the context is the bottleneck

This is the most intuitive of the three. A long context means more tokens to attend over, so each step should cost more. Compaction, summarization and "context hygiene" all follow from it.

The measurement says otherwise. Across the 123 sessions long enough to compare, context at the end of a session was a median **9.6x** the context at the start. If length drove latency, per-step duration should have climbed steadily. It did not:

| what we measured | result |
|---|---|
| sessions with enough steps to compare | 123 |
| median context growth, first step → last step | **9.6x** |
| correlation, log₁₀(context) vs step duration | **-0.03** |
| median step duration | 8.5 s |

A correlation of -0.03 is not "context makes things faster." It is what you get when there is nothing to detect. An earlier cut of the same logs, computed differently, gave **+0.085** — also indistinguishable from zero, with the opposite sign. That was not sampling noise: recomputing under five different sample definitions kept the value negative every time. The positive number came from a different pairing and statistic, which is exactly the trap this post is about.

**The disagreement between two computations of the same logs is the finding.** When two defensible ways of measuring the same thing disagree on the sign, neither sign is worth quoting. The defensible statement is: in this sample, per-step duration was not explained by context length.

What does explain it? The data points at the task, not the transcript: duration tracked position in the session far more strongly than context size: later steps took longer not because they saw more text, but because of what they were being asked to do at that point.

**Practical consequence.** Compaction buys headroom against a hard context limit. It should not be expected to buy speed, unless your runtime has a specific pathology ours did not show. If your sessions hit a limit and die, compact — that is a correctness fix. If your sessions are just slow, compaction is the wrong lever, and you will not find that out without measuring.

## Intuition two: the tools are the bottleneck

This one feels obviously true for agent workloads: agents run commands, commands take time, so the commands are the cost.

Measured properly, tool round-trips came to about a third of **total** step time — and roughly two percent of the typical step, because a few heavy cycles carry almost all of it:

| what we measured | result |
|---|---|
| step cycles analysed | 13,281 |
| median step cycle | 8.8 s |
| tool round-trips as a share of **total** step time | **32.7%** |
| tool round-trips as a share of the **median** step | **2.1%** |
| share of all tool time contributed by the top 10% of cycles | **96%** |

The gap between 32.7% and 2.1% is the point of this section, and it is not a definitional quibble — it is the difference between a sum and a typical case.

When you sum every tool round-trip and divide by the sum of every step, a small number of heavy cycles dominate the numerator. In our logs the top 10% of cycles accounted for **96%** of all tool time. The median step spent about two percent of its duration in tools; the average-weighted total says about a third. Both are true statements about the same data, and they license opposite decisions.

**How sensitive is the first number?** More than we expected, and that is worth showing rather than hiding. The same logs give **1.5%**, **32.7%** or **23.7%** for the pooled share depending on how you treat long steps:

| filter | pooled | median |
|---|---|---|
| drop every step over 5 min | 23.7% | 2.1% |
| drop only steps with no tool activity and a long gap (idle) | **32.7%** | **2.1%** |
| no filtering at all | 1.5% | 2.1% |

The 276 steps over five minutes total **2,028 hours** — the longest is **1,022 hours**, with zero tool time. Those are suspended gaps between sessions, not work, and including them inflates the denominator until the pooled share collapses to 1.5%. But the blunt five-minute cut also throws away **90 real long tool calls** (686 minutes of tool time), which is why it reads low.

The median barely moves across all three (2.04%–2.14%). **That asymmetry is the actual finding**: a statistic built from sums is hostage to how you bound the tails, and a per-step median is not. If you only take one number from this section, take the median — and report the filter you used alongside the pooled one.

Which one matters depends on the question:

- **"Would a faster tool make my sessions faster?"** Then the pooled share bounds the win — 32.7% is the ceiling, and it is only reachable if you speed up the heavy tail, which is where the time actually is.
- **"Why did this particular step take eight seconds?"** Then the median share is the honest answer: it spent about 2% of that time in tools.

A single tool call runs in well under a second. Optimizing that inside an 8-second step can be worth doing for other reasons — fewer tokens, less risk, cleaner logs — but the time is in the model thinking, and no subprocess rewiring touches it.

## Intuition three: bigger tasks mean more dispatch

The third intuition is about process rather than latency: a small change should need less ceremony, so dispatch counts should track change size.

They track it, but far more weakly than "should" implies:

| what we measured | result |
|---|---|
| tasks with at least one dispatch | 40 |
| correlation, log₁₀(production lines changed) vs dispatch count | **+0.48** |
| median dispatch count per task | 18 |

Across a range where the change size spans roughly 100x, dispatch counts spanned about 2.7x. A task with a hundred lines of production code and a task with ten thousand differ far less in process overhead than in size.

That is a comfortable finding if you believe process should be roughly constant per task. It is an uncomfortable one if you assume small tasks are cheap, because it means the fixed cost of the workflow does not scale down with the work. The practical read: if you are trying to make small changes cheap, the lever is not "the process automatically shrinks" — it is an explicit cheap path, chosen on purpose.

## The rule this suggests

All three intuitions failed the same way: they name a plausible cost, and no one checked its **share**.

So here is the rule, and it is the only thing in this post I would insist on:

> **Before optimizing an item, measure its share of total time. Below a few percent, optimizing it is a hobby. Above a third, it is the job. In between, the share alone does not decide — the shape of the distribution does.**

Applying it to the three cases:

| candidate | its share, measured | verdict |
|---|---|---|
| faster tools | 32.7% pooled, 2.1% median | worth it only if you can speed up the heavy tail |
| compaction for speed | not detectable in our data | hobby, unless you are dying at a context limit |
| fewer dispatches per small task | fixed cost does not scale down | worth an explicit cheap path, not a tweak |

![Illustration: three intuitions in a table — context is the bottleneck (context ×9.6, step duration flat, r = −0.03), tools are the bottleneck (32.7% pooled / 2.1% median), bigger tasks mean more dispatch (size spans ~100x, dispatch spans 2.7x). A footer states the rule: measure an item's share before optimizing it.](./images/illustration-three-intuitions.svg)

The middle band is not a cop-out: it is where the tools case landed (32.7% pooled, 2.1% median), and the deciding evidence was the distribution — a heavy tail you would have to speed up, versus a typical step that spends almost nothing there.

The rule also explains why these intuitions persist. Each is derived from a real cost: context does grow, tools are slower than no tools, big tasks do carry more process. What goes wrong is not the observation but the jump from observation to fix.

## Two ways to read a number wrong

I hit both of these while writing this post: the first version of the tool-share number went into a draft with the pooled figure described as "each step," and I only caught it when I laid the two numbers side by side on the same page and could not make them agree. Both mistakes are cheap to avoid.

**Reading the sign of a near-zero correlation.** Our first cut gave +0.085; the second gave -0.03; both are noise. If a correlation is small enough that the sign flips between samples, the only conclusion is "no detectable relationship." Quoting "+0.085, so context makes it slower" is how a null result becomes a folklore.

**Reporting a pooled share as if it described a typical case.** "Tools are 32.7% of the time" and "the median step spends 2.1% in tools" are both true, and quoting either without saying which is which turns a measurement into an argument. When a distribution is this skewed, the pooled number describes the *aggregate bill* and the median describes the *typical step*. Say which one you mean, every time.

## Measure your own in an afternoon

1. **Find the event stream.** Most agent runtimes log step boundaries and tool calls somewhere. If yours does not, that is the first thing to fix — an unlogged cost cannot be optimized, only guessed at.
2. **Compute step cycles.** Pair each step start with the next one; discard gaps over a few minutes (those are idle time, not work).
3. **Compute the tool share two ways.** Once pooled (sum of tool time over sum of step time — the aggregate bill) and once as the per-step share, then take the median (the typical step). Report both, because they answer different questions.
4. **Compute context growth and correlate it with step duration.** Use log tokens, not raw counts, or a few huge sessions will dominate. If the correlation is within ±0.2, treat it as no relationship.
5. **Rank your candidates by share before you touch any of them.** Then look at the top of that list, which is probably not the thing you were about to optimize.

The core of steps 2–3 is about twenty-five lines. The one detail that matters is pairing each result to its own call — agent runtimes issue parallel tool calls, so a plain stack will mispair them and inflate the numbers:

```python
events = [json.loads(line) for line in open(log_path)]

def call_id(event):                      # adjust to your runtime's shape
    data = event["data"]
    return data.get("callId") or (data.get("message") or {}).get("source", {}).get("callId")

marks = [(e["time"], e["type"], call_id(e)) for e in events
         if e["type"] in ("step/start", "tool/call", "tool/result")]
marks.sort()

starts = [i for i, (_, kind, _) in enumerate(marks) if kind == "step/start"]
cycles, tool_spans, shares = [], [], []
for a, b in zip(starts, starts[1:]):
    dur = (marks[b][0] - marks[a][0]) / 1000
    if dur <= 0:
        continue
    open_calls, in_tool = {}, 0.0
    for t, kind, cid in marks[a:b]:
        if kind == "tool/call" and cid:
            open_calls[cid] = t
        elif kind == "tool/result" and cid in open_calls:
            in_tool += (t - open_calls.pop(cid)) / 1000
    # Drop only genuine idle gaps: a long step with no tool activity.
    # A long step WITH tool activity is a real slow call, not an idle gap —
    # dropping it was a bug in the first version of this post.
    if dur >= 300 and in_tool < 60:
        continue
    cycles.append(dur)
    tool_spans.append(in_tool)
    shares.append(in_tool / dur)          # per-step share, not a cross-list zip

print("pooled:", sum(tool_spans) / sum(cycles))     # the aggregate bill  → 32.7%
print("median:", sorted(shares)[len(shares) // 2])  # the typical step    → 2.1%
```

The two lines at the bottom are the whole point: they compute the two numbers this post keeps distinguishing, from the same events, and they will disagree on any skewed workload.

The uncomfortable version of this advice: the largest cost in the cycle is the model thinking, and that is not something a plumbing change fixes. It responds to better task decomposition, better prompts, and smaller units of work — or to accepting the cost.

## What this does not tell you

**It does not generalize across models.** A model with different attention behaviour, or a runtime that re-reads the whole context per step instead of caching it, could show exactly the correlation our data lacks. The method transfers; the numbers do not.

**It does not say context never matters.** It says context length did not explain per-step duration in this sample. Context still matters for correctness — what the model can see, what it forgets, how much room is left.

**It does not measure cost.** We measured wall-clock duration. Token spend is a different axis, and it grows much faster than time: in the same logs, the median session read about 65 cache tokens for every output token it produced. Time and money are separate budgets; everything here is about time.

**And it is one project.** One codebase, one language, one model, one machine. The sample is large in steps and small in everything else. Treat it as a demonstration of a method that happened to contradict the folklore, not as a benchmark of your stack.

---

## Correction (2026-11-23)

The first published version capped every step at five minutes to discard idle gaps between sessions. That filter also discarded **90 genuine long tool calls** worth 686 minutes of tool activity, and it changed the pooled tool share. Corrected figures, with the sensitivity table above: pooled **32.7%** (not 23.7%), median **2.1%** (unchanged), top-10% concentration **96%** (not 94%).

The bug was found by a reader who noticed that a five-minute cut cannot distinguish a stalled session from a slow tool. They were right, and the asymmetry this exposed — pooled moves by 20 points across filters, median by 0.1 — turned out to be a better argument than the one the post originally made.

The demo code above now drops a step only when it has no tool activity *and* a long gap.

---

The productive version of all this is not "stop optimizing." It is: your intuition about where time goes is probably a claim about a cost's *existence*, not its *share*. Those are different claims, and only one of them is worth an engineering decision.
