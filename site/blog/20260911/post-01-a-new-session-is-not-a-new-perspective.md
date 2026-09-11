---
title: "A new session isn't a new perspective"
date: 2026-09-11
description: "You moved your agent's code review into a fresh session with no author context — and it still missed what a differently-trained reviewer would have caught, because it runs on the same model as the author. Same training distribution, same systematic blind spots. v0.71.0 ships the fix's missing axis: route any (phase, role) to a different model or a different CLI, with fallback rules that make judge-shopping impossible. Plus the three-question audit for your own pipeline."
tags:
  - ai-agents
  - verification
  - llm
  - engineering-practices
---

# A new session isn't a new perspective

The fix from the last post: put the review in a fresh session, with none of the author's context. So you did — the reviewer has never seen the conversation, the reasoning, or the sunk cost. It still runs on the same model as the author, and a model family's blind spots survive any number of fresh sessions.

![Cover: an author node passes an artifact across a dashed context wall; behind the wall wait two judges — one a ghosted duplicate of the author in the same purple, one a solid teal judge holding a checkmark and an exit-code tag. Title reads "A new session isn't a new perspective."](./images/cover.svg)

**TL;DR** — Role separation buys context independence: the reviewer can't inherit the author's misreadings, reasoning, or sunk cost. What it can still inherit is the model. Two sessions of the same model read with the same trained reflexes, so the failures a whole model family tends to miss are missed by both the producer and the reviewer. Our own [limitation file](https://github.com/randomgitsrc/agateon/blob/main/agate/LIMITATIONS.md) carried this as a known, unfixable gap ("cognitive isolation, not true independence") until this week: v0.71.0 ships a dispatch router that can send any (phase, role) to a different model, or a different CLI entirely. Two invariants keep it honest: candidates fall back only on infrastructure failures, never on a gate FAIL — no shopping for an approving judge — and gates judge the artifact plus exit code, never the producer. The honest costs: a same-vendor model swap is weak mitigation, a cross-CLI subprocess is strong; unconfigured means byte-identical to before; and it's mitigation, not a cure. Below: why the blind spot survives the new session, how the routing works, and a three-question audit for your own pipeline.

## The blind spot follows the model, not the session

Why doesn't a fresh session fix this? Because the session was never where the blind spot lived. A model's reflexes — what looks obviously correct, which edge classes read as out-of-scope, what kind of confident prose papers over a missing case — come from training. Two sessions of the same model bring the same reflexes to the same spec. Role separation removes the shared misreading of *this* task — the reviewer no longer inherits the author's context. What it leaves untouched is the model's shared sense of what probably doesn't matter.

This is in our [LIMITATIONS.md](https://github.com/randomgitsrc/agateon/blob/main/agate/LIMITATIONS.md) as limitation 2, and the wording is careful: role isolation can block "obvious laziness," it cannot block "systematic blind spots" — the boundary cases this model family is bad at are missed by both roles. We shipped role separation knowing that, labeled it partial, and logged the gap as ADR-006: same-origin model isolation is cognitive-level, not true independence. For a while we had no mechanism for it at all. What we had was a name for the residue — and the observation that the residue is exactly the part prompting can't fix — the gap is invisible from inside both sessions.

![Illustration: where the blind spot lives — on the left, author and reviewer are two sessions of the same model, and a dotted ellipse spans both, the same blind spot missed twice; on the right, the reviewer is a different model behind the context wall, so the blind spot stays local to the author while the judge returns a verdict and an exit code](./images/illustration-blind-spot.svg)

## The model axis

v0.71.0 adds the missing dimension. The command is `agate dispatch route <phase> <role>`, and the flow ([protocol §0](https://github.com/randomgitsrc/agateon/blob/main/agate/dispatch-protocol.md)) is deliberately boring: look up `(phase, role)` in the routing config; resolve it to either a tier or an explicit candidate chain of `{cli, model, effort?}` (`effort` being the CLI's reasoning-effort level); dispatch to the first candidate; fall through to the next only on infrastructure signals; if the chain runs out, dispatch like the feature never existed.

The vocabulary has three tiers — `bulk` (high volume, low cost), `deep` (hard judgment: architect, judge, consistency review), and `standard`. `standard` has a special job: it means "inherit the main agent's current model and dispatch natively," and it is the factory default for every phase and role. That makes the strongest guarantee in the whole feature the one you test first: **unconfigured means byte-identical**. There's a dedicated zero-change test asserting it — with no routing config, every dispatch resolves through the identical code path as before, and zero `dispatch_route` events appear in the ledger.

The mitigation strength depends on what you route to, and the protocol says so plainly. `cli: native` — same platform, different model — is *weak* mitigation: same training lineage, so the blind spots mostly overlap; what you buy is cost matching and some failure-mode diversity. A cross-CLI subprocess — say, sending the judge to a different vendor's CLI — is *strong* mitigation: a genuinely different training lineage, which is what "independent perspective" was supposed to mean all along.

## Two invariants that keep it honest

A feature like this has one failure mode that would quietly eat everything: using the fallback chain to escape bad verdicts. Two mechanical rules close that hole.

**Fallback is for broken plumbing, not rejected work.** The candidate chain falls through on exactly three signals — `launch_fail`, `infra_error`, `no_parseable_output`. Once a candidate has produced anything a gate can evaluate, the routing is done and successful, whatever the gate then says. A gate FAIL is a normal phase retry *on the same candidate*; the router does not get another turn. The reason-code enum has no `gate_fail` value, and [our audit script](https://github.com/randomgitsrc/agateon/blob/main/agate/scripts/check-events.py) mechanically rejects any event that tries to smuggle one in. Without this, every rejection would tempt a fallback to a more agreeable model and quietly become permission to try a different judge.

**Producer-agnostic gates.** The protocol states the second premise directly: gates read the output files and the exit code, and they must never learn who produced them — no special-casing for cross-CLI output, now or later. If a gate ever needs to know the producer, routing decisions leak into judgment.

And every fallback leaves a mark: one `dispatch_route` event per route decision — candidates tried, reason codes, final choice — into the [hash-chain ledger](/blog/20260905/post-01-give-your-ai-agent-a-flight-recorder) — the append-only event log where each line is hash-chained to the last. A fallback chain that's too smooth becomes an avoidance exit; the counterweight is the one the protocol already runs on everywhere else — if a fallback writes no event, later audits can't see that it happened.

## The design got reviewed like code

One more thing worth showing, because it's the pattern applying to itself. The routing design document went through two rounds of external independent review, both on the same day. Round one **failed** on two blockers, and both were the same species: evidence strength got flattened in translation. The research report had marked Codex's `spawn_agent` schema as model-self-reported; the design doc cited it as "tested end-to-end," lumping it in with the platform model-passing that really had been tested. The same flattening hit an OpenCode bug where the report had *reasoning* and the doc claimed *reproduction*. The reviewer's demand wasn't "reword it" — it was to split the evidence classes and write down, per claim, what actually backs it: not seeing a field in a model's self-description is not proof the field is absent. Round two **passed**, with one leftover kept visible: an environment-representativeness note on the tmux tests that was judged non-blocking, and the tmux layer accordingly ships behind a flag, default off, until it's re-verified on target environments. That is [the evidence ladder](/blog/20260828/post-01-evidence-ladder) run against our own design doc — and it's why the claims in this post are scoped the way they are.

## What it doesn't fix

Unconfigured stays byte-identical, and our own workspace config ships exactly that way — the [routing file](https://github.com/randomgitsrc/agateon/blob/main/agate-workspace/dispatch-routing.yaml) in this repo contains the commented example and two empty mappings. Turning it on is an operator decision, made per machine, against what's actually installed; the protocol refuses to pretend that choice is reproducible across machines. Same-vendor model swaps share most of their training lineage, so the "weak mitigation" label is not modesty. And even in the strong configuration, the main agent is still the one writing the routing table — which model gets to judge what remains a human-and-main-agent choice, unconstrained from outside, the same single point every other judgment in the system concentrates to. This widens the independence you can have; it doesn't automate the judgment of how much independence you want.

## Audit your loop

Three questions, answerable for any agent pipeline:

1. Which model produced this artifact?
2. Which model reviewed it?
3. Do the two share a training lineage — same family, same vendor, same base?

If 1 and 2 name the same model, your reviewer inherited the producer's systematic blind spots, no matter how fresh the session. The one-line change: route the reviewer role to a different model at minimum; a different CLI is the strong version. Keep the fallback infra-only, and log every fallback.

## Try it

v0.71.0 is tagged and live: `agate dispatch route`, the [tier vocabulary](https://github.com/randomgitsrc/agateon/blob/main/agate/rules/dispatch-tiers.yaml), the project-level routing file, and [a validator](https://github.com/randomgitsrc/agateon/blob/main/agate/scripts/check-dispatch-routing.py) for your config — all MIT, at [github.com/randomgitsrc/agateon](https://github.com/randomgitsrc/agateon):

```bash
curl -sSL https://raw.githubusercontent.com/randomgitsrc/agateon/main/install.sh | bash
```

You already have the session axis; the model axis is one config file away. Use both — context first, lineage second, ledger always.
