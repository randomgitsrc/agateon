---
title: "When is the review done? A stopping rule for LLM review loops"
date: 2026-11-04
description: "LLM reviewers are samplers, not validators: ask again and the same artifact usually yields a different batch of findings. That makes \"keep reviewing until nothing new comes up\" a criterion with no terminating guarantee. Here is a stopping rule built on severity classes instead of round counts — plus our own review logs showing why the distinction matters."
tags:
  - ai-agents
  - code-review
  - engineering-practices
  - verification
---

# When is the review done? A stopping rule for LLM review loops

If you route work through an LLM reviewer, you have probably hit this: the first round finds real problems, you fix them, the second round finds more, you fix those, and the third finds more again — none of them wrong, and the loop never saying "clean." So the question stops being "is the work good?" and becomes "how many rounds do we pay for?", which most teams answer with an inherited number — two rounds, three rounds — and then treat whatever the last round said as the verdict.

![Cover: the same unchanged artifact reviewed three times, each pass returning a different small batch of cosmetic findings. On the right, two trays — "critical" reads 0 and is labelled "was cleared in pass 1", while "cosmetic" reads n and is labelled "cap it, don't clear it".](./images/cover.svg)

**TL;DR** — An LLM reviewer is a sampler, not a validator: run it twice on the same unchanged artifact and you usually get a different set of findings, because each run samples a different slice of what it could notice. That makes "review until nothing new appears" a criterion with no terminating guarantee — there is usually another sample. The fix is not a better prompt or a higher round cap; it is to stop counting rounds and start classifying findings. Critical and important findings form a small, enumerable set: when that set is empty, you can ship. Cosmetic findings are effectively unbounded and vary per run: cap them, don't clear them. Below: why the two classes behave differently, a stopping rule you can write into your own process, and our own review logs as a worked example — including the round where the only remaining findings were ones we had already decided not to block on.

## A sampler, not a validator

A test runner is a validator. Barring flakiness, it returns the same verdict on the same code every time. That reproducibility is what makes "all tests pass" a usable gate.

An LLM reviewer does not have that property. Give it the identical artifact twice and you will usually get different findings: it may notice a stale cross-reference on one pass and a missing definition on another, and neither pass is wrong. The findings are real; the set is just not stable. Two consequences follow, and both are quietly load-bearing for how you run the loop.

**First, "nothing new" has no terminating guarantee.** Any process that says "keep reviewing until a round comes back empty" is describing a sampling process and asking it to stop sampling. On a large enough artifact you will usually get a round that samples *something*; a round does occasionally come back empty (especially on small artifacts), but that is a round that happened to sample nothing, which is a different claim and a much weaker one.

**Second, round count is the wrong variable.** Rounds are a proxy for the thing you actually care about — how much risk is left — and the proxy is bad in both directions. Three rounds can leave a critical defect untouched if each round sampled around it. One round can be enough if the artifact is small and the class of risk is narrow.

This is not an argument against LLM review. Sampling is exactly why it works: a fresh context notices things the author's context was blind to. The point is that a sampler needs a different stopping rule than a validator does.

## Two classes of finding, and only one of them converges

Look closely at what comes back from a review round and it splits into two populations that behave nothing alike.

| | critical / important | cosmetic |
|---|---|---|
| **size of the set** | small and enumerable | effectively unbounded |
| **what it means** | the artifact is wrong or unusable | the artifact is fine but could read better |
| **does another round help?** | yes — this is what you're buying | barely — you get a different sample, not a cleaner artifact |
| **stopping test** | set is empty | count under a cap |
| **examples** | a cited claim that is false, a link that 404s, a section that contradicts another, an image referenced but never inserted | a word used twice, a heading that could be tighter, a tag list ordered differently, a count in a caption that says "five" where the figure has three |

![Illustration: two populations of findings side by side — critical/important, a small set that converges from three to zero across rounds; and cosmetic, effectively unbounded, where each round surfaces a different three. Fixing a critical finding removes it from the population; fixing a cosmetic one swaps the instance.](./images/illustration-two-populations.svg)

The important asymmetry: fixing a critical finding *removes it from the population*. Fixing a cosmetic finding also removes that instance, but the population is large enough that the next sample surfaces a neighbour. That is why a loop that mixes them can run indefinitely while still appearing to make progress, and the progress it makes is on the class that does not need it. So the rule is not to review less; it is to stop asking one question of both classes.

## A stopping rule you can write down

Four lines, and none of them mention a round number:

1. **Block on: any critical finding.** Critical means the artifact is wrong or unusable — a false claim, a broken path a reader will follow, a missing piece the piece depends on. This set is enumerable, so "zero" is a meaningful target.
2. **Block on: any important finding.** Important means a reader would be misled or would have to do work to recover — a number stated without its denominator, an unstated assumption that changes the conclusion, a claim whose evidence is in a different repository.
3. **Do not block on cosmetic findings; cap them.** Pick a number you are willing to fix per round (we use "whatever is cheap," operationally a handful) and stop when the remaining ones are all cosmetic. Write down the cap so the next round doesn't relitigate it.
4. **Write an escalation clause.** A cosmetic finding becomes important if the accumulation starts to affect credibility. One typo is cosmetic. Twelve wrong numbers in a document about number discipline is not — at some point the reader stops trusting the rest, and that is a critical failure wearing cosmetic clothes.

The clause matters more than it looks. Without it, "cosmetic" becomes a place to put anything inconvenient, and the rule degrades into "ship whatever the author feels like shipping." With it, the rule has a failure mode you can argue about in advance.

There is also a direction the clause does not cover, and it is the dangerous one: an important finding misclassified as cosmetic passes silently, because nothing downstream will ask about it again. The cheap guard is to keep the list of findings you chose not to block, per artifact. A list you have to write down is harder to fill with things you would rather forget.

## What our logs show

I keep a log of what each review round found, because after the third round of one piece I could not remember which findings had blocked it and which I had merely tolerated. That log is where the two examples below come from — it lives in the repository as the [publish checklist](https://github.com/randomgitsrc/agateon/blob/main/site/guides/publish-checklist.md), one entry per published piece.

**One piece went: FAIL → FAIL → PASS.** The first round found three things — an illustration referenced in prose but never inserted (a reader would see no image), a fifth quotable one-liner against our own cap of two, and a term used before it was defined. The second round found one sentence still over the aphorism cap, and the third round passed.

That first round is the interesting one. Three findings, three different severities: one would have produced a visibly broken page, one was a style quota, one was a comprehension problem. All three arrived as the same word — FAIL — because the reviewer had no way to say "this one blocks and these two are taste."

**Another piece went: FAIL (five blocking items) → FAIL (four, all newly introduced) → PASS.** The second round is worth dwelling on: those four were introduced *by the fixes from round one*. The reviewer was not finding deeper problems; it was finding the damage done by the previous repair. A round cap would have shipped them, because round two was "the fix round."

Neither of those sequences says the reviewer was too strict. They say the reviewer had one output channel for two different things, and we were reading the channel rather than the content.

### The part where the reviewer is also a sampler about itself

The sharpest evidence is not from the blog. It is from an [internal assessment document](https://github.com/randomgitsrc/agateon/blob/main/docs/research/agateon-value-assessment-20260929.md) that we put through the same loop, three versions deep. The first version contained ten errors that the reviewer reported, and the document is explicit that this is a reported subset rather than a total, so the error rate is unknown. The second version fixed them and introduced new ones. The third version found three more — including, of all things, a misclassification of which of its own claims were machine-checkable.

The document about verification discipline had a verification error in its own checkability labels. That is the sampler property in its purest form: same author, same standards, third pass, new class of miss. A round count would not have predicted it, and would not have stopped it.

## What this does not solve

**It does not tell you the classes are objective.** "Critical" and "cosmetic" are judgments, and two reasonable engineers will disagree at the boundary. The rule does not remove that judgment; it forces it to happen once, explicitly, instead of being re-litigated every round by whoever is holding the FAIL.

**It does not make critical findings enumerable in practice.** The set is enumerable in principle. In practice you will discover a new category of critical finding on some future artifact, and the rule will have had no slot for it. That is fine as long as you add the slot rather than letting it sit in cosmetic.

**It does not transfer a number.** Our reviewer, our artifact sizes, our tolerance — none of that is your setup. What transfers is the shape of the rule, not the numbers in it.

**And it does not say review is cheap.** The rule makes the cost predictable rather than small. If your critical class is empty and you keep reviewing anyway, you are buying samples of the cosmetic population at full price.

## Do this on your next review loop

1. **Before the first round, write the two lists.** What would make this artifact wrong or unusable? What is merely taste? If you cannot fill the first list, you do not yet know what you are shipping.
2. **Have the reviewer label each finding.** Not a score — a class. If your reviewer cannot classify, you classify, once, at triage.
3. **Stop when the first list is empty.** Not when the findings are gone; when the *blocking* findings are gone.
4. **Write the cosmetic cap down,** and the escalation clause next to it.
5. **Log the classification per round.** That log is what tells you, after a few artifacts, whether your critical list is complete — the only way this rule improves.

The rule is not a way to ship faster. It is a way to know what you are shipping, which is the thing a never-terminating loop was hiding from you.
