# Project: Malayalam Full-Duplex AI Companion
### Final Architecture & Build Plan

---

## 1. The Core Idea (restated)

Not an assistant that waits for commands. A companion that is continuously co-present — always listening, always watching your screen, able to speak or act without waiting for you to finish, able to interrupt you mid-sentence or mid-action, and able to lead the interaction rather than only respond to it. It should also be able to do the actual work: fill browser forms, run commands, operate your machine.

This requires **native interactivity** (interruption/initiative built into the model's decoding, not faked with a Voice Activity Detector) plus an **agentic execution layer** bolted on top. The two halves are architecturally separate and must stay separate — this is the single most important design decision in the whole project.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 4 — ACTION / EFFECTOR LAYER                                │
│  • Browser automation (Playwright / DOM control) — form autofill │
│  • Screen perception loop (screenshot → OCR/VLM → understanding) │
│  • OS command execution (via MCP servers — see note below)       │
│  • Tiered-trust permission gate (auto-run vs confirm vs block)   │
└───────────────────────────▲────────────────────────────────────────┘
                             │ tool calls out / results in
┌───────────────────────────┴────────────────────────────────────────┐
│  LAYER 3 — BACKGROUND AGENT (async reasoning + tool use)          │
│  • Claude Sonnet / Groq cascade — plans, calls tools, reasons     │
│  • Receives FULL shared conversation context, not a bare query   │
│  • Runs asynchronously — never blocks Layer 2's responsiveness   │
│  • Streams partial/final results back for Layer 2 to weave in    │
└───────────────────────────▲────────────────────────────────────────┘
                             │ delegate task / receive stream
┌───────────────────────────┴────────────────────────────────────────┐
│  LAYER 2 — INTERACTION MODEL (always-on, full-duplex)             │
│  • Fine-tuned Moshi — Malayalam                                  │
│  • Perceives + responds in continuous 200ms micro-turns          │
│  • No VAD, no turn-detector — interruption is native to decoding │
│  • Handles: backchannel, correction, interjection, initiative     │
└───────────────────────────▲────────────────────────────────────────┘
                             │ continuous audio/text micro-turns
┌───────────────────────────┴────────────────────────────────────────┐
│  LAYER 1 — PERCEPTION BUS                                          │
│  • Microphone stream (continuous, not push-to-talk)               │
│  • Screen frames / active-window state                            │
│  • Shared context store both layers read/write to                 │
└──────────────────────────────────────────────────────────────────────┘
```

**Three terms used throughout this doc, defined here since none of this exists yet in your projects:**

- **MCP server** — Model Context Protocol server. A small program that exposes a specific capability (e.g. "control the file system," "control the browser," "send a keystroke") as a set of callable tools that an LLM can invoke. You don't have any built yet — Phase 1 below includes building one or two from scratch (they're small, often under 200 lines each).
- **Model cascade** — instead of sending every request to your most expensive/slowest model, you route by difficulty: try a fast/cheap model (e.g. Groq-hosted Llama) first, and only fall back to a stronger model (Claude Sonnet/Haiku) if the task needs deeper reasoning. This is a routing pattern you'd write yourself (a few dozen lines of logic), not a product that exists off the shelf.
- **Tiered-trust permission model** — a simple rule table you define, e.g.: read-only actions (check screen, read a file) auto-run; medium-risk actions (fill a form, open an app) need a spoken "yes, go ahead"; high-risk actions (send a message, spend money, delete something) are blocked outright or require explicit double-confirmation. This is a policy you write and enforce in code before any tool call executes, not an existing system.

**Why this split, not one big model:** This mirrors how Thinking Machines Lab's own interaction-model system is structured — a fast always-on model handles presence and turn-taking, while a separate async model handles deep reasoning and tool use, sharing context so the fast model can keep talking while the slow one thinks. You cannot get both low-latency conversational presence *and* strong agentic reasoning out of one model at student-hardware scale — you have to split the concerns like TML did, just at a much smaller scale using Moshi instead of a from-scratch frontier model.

---

## 3. Layer-by-Layer: Features & Functions

### Layer 1 — Perception Bus
| Function | Detail |
|---|---|
| Continuous audio capture | No push-to-talk button. Mic is always open while the companion is active. |
| Screen state capture | Periodic screenshots (or window-event triggered) fed to a lightweight vision pass. |
| Shared context store | A single running state object (recent transcript, recent screen state, active task) both Layer 2 and Layer 3 read from — this is what lets Layer 3's results get "woven in" naturally instead of dumped as an interruption. |

### Layer 2 — Interaction Model (the companion's "presence")
| Function | Detail |
|---|---|
| Full-duplex listening+speaking | Fine-tuned Moshi processes input and generates output in the same continuous stream — it can speak while still receiving your audio. |
| Native interruption | Because there's no external turn-detector, the model itself decides when to jump in — this only works if training data explicitly contains interruption/correction examples, not just clean turn-taking. |
| Backchanneling | Short acknowledgents ("mm", "seri", "aah") while you talk, learned from stereo conversational data, not scripted. |
| Delegation trigger | When a request needs real reasoning/tool use, Layer 2 hands off to Layer 3 with full context, then keeps the conversation alive (small talk, clarifying questions) while Layer 3 works. |
| Personality/eagerness tuning | Decoding-time bias on the silence/PAD token controls how proactively it jumps in — tunable without retraining once the base fine-tune exists. |

### Layer 3 — Background Agent (the companion's "competence")
| Function | Detail |
|---|---|
| Task planning | A model cascade (fast/cheap model first, escalate to Claude Sonnet only when needed — see definition above) breaks a delegated task into steps. This cascade needs to be built; it's a routing layer you write around API calls, not existing infrastructure. |
| Tool orchestration | Calls Layer 4 tools (browser, OS, files) as needed, in sequence or parallel. |
| Context-aware reasoning | Gets the *entire* conversation, not just the last sentence — so it understands what you actually meant, including things said before the delegation happened. |
| Streaming results back | Doesn't wait to finish everything before responding — partial results stream back to Layer 2 as they're ready, so the companion can say "found it, one sec" instead of going silent. |

### Layer 4 — Action / Effector Layer (the companion's "hands")
| Function | Detail |
|---|---|
| Browser control | Playwright-driven form filling, navigation, data entry — reuse patterns from any Claude-in-Chrome-style DOM automation. |
| Screen monitoring loop | Screenshot → OCR/VLM → structured understanding → decide if intervention/comment is warranted. |
| OS command execution | MCP servers you build for Windows/WSL control — file ops, app launching, shell commands. Start with one server covering just 3-4 actions (open app, run shell command, read file, write file) and expand from there. |
| Tiered-trust gate | A permission model you define from scratch (see explanation above): some actions auto-execute, some need a spoken confirmation, some are blocked outright. This is a safety-critical piece — don't skip building it just to move fast. |

---

## 4. Step-by-Step Build Plan

### Phase 0 — Scope lock (this week)
Decide explicitly: Phase 1 ships Layers 3+4 only, using text/typed input, no Moshi involved yet. This gives you a **working, demoable agent immediately** and de-risks the whole project — if the Moshi fine-tune stalls, you still have a real deliverable.

### Phase 1 — Agent + Action layer (buildable now, no new ML)
1. Build Layer 3: write the model-cascade routing logic (Groq for fast/cheap calls, Claude Sonnet/Haiku for anything needing deeper reasoning). Your invoice-studio project already gave you experience with Claude + Groq API calls — this is new glue code on top of that, not a new integration from zero.
2. Build Layer 4: set up browser automation (Playwright) + write one MCP server covering a small starting set of OS actions (open app, run shell command, read/write file).
3. Write the tiered-trust confirmation gate as its own module — a simple lookup table mapping action type to trust level, checked before any tool call executes.
4. Test end-to-end: typed command → agent plans → agent fills a form / runs a command → reports back.
5. **Deliverable at this checkpoint:** a working command-and-execute agent. This alone is placement-portfolio-worthy.

### Phase 2 — Malayalam data collection (runs in parallel with Phase 1)
1. Recruit 15–30 pairs of native Malayalam speakers (classmates, dept contacts — you have easy access here).
2. Record **stereo, separate-channel** conversations (this is the single most important data property — it's what let Human-1 learn real turn-taking/overlap instead of guessing at it from a mixed channel).
3. Deliberately elicit non-clean-turn-taking behavior: give speaker pairs prompts designed to produce interruption, self-correction, and overlapping speech — not scripted alternating dialogue. Include natural Malayalam-English code-switching (Manglish), since that's how you'll actually talk to it.
4. Target: even 50–100 hours of good stereo dyadic audio is a realistic, usable starting corpus at your scale — you do not need Human-1's 26,000 hours.
5. Build/adapt a Malayalam SentencePiece tokenizer over the corpus (Malayalam script is distinct from Devanagari, so this is genuinely new tokenizer work, not reuse).

### Phase 3 — Moshi fine-tune (the ambitious research piece)
1. Rent a GPU node (RunPod/Vast.ai, 1–2× A100/H100 — you do not need Human-1's full 8×H100 pretraining run if you skip full pretraining).
2. Skip full from-scratch pretraining; fine-tune directly on top of Moshi's public checkpoint (Moshika/Moshiko), replacing the tokenizer and reinitializing text-vocab-dependent parameters while keeping the pretrained audio components — this is Human-1's core technique, applied at fine-tune-only scale.
3. Two-stage schedule, scaled down: stage 1 short adaptation pass, stage 2 fine-tune on your curated conversational subset with split learning rates (lower for the temporal transformer, higher for the depth transformer, matching Human-1's ratios as a starting point).
4. Evaluate qualitatively first: does it backchannel, does it interrupt appropriately, does it stay quiet when it should. Don't over-index on benchmark numbers at this scale — listen to real conversations.
5. Optional: tune the PAD-token decoding bias to dial "eagerness to interject" up or down without retraining.

### Phase 4 — Integration
1. Wire Layer 2 (fine-tuned Moshi) to the Perception Bus and to Layer 3's delegation interface.
2. Add the "keep talking while Layer 3 works" behavior — this is a prompting/context-management problem, not a training problem, so it's fast to iterate on.
3. Add screen-perception triggers into Layer 2's context so it can proactively comment on what it sees on-screen, not just what it hears.

### Phase 5 — Hardening
1. Long-session context management (this degrades over time in every full-duplex system — plan for it, don't be surprised by it).
2. Safety pass on the tiered-trust gate — anything that touches real money, real messages, or irreversible actions should require explicit confirmation, no exceptions.
3. Latency profiling end-to-end (mic → Layer 2 → Layer 3 → Layer 4 → back).

---

## 5. Honest Risk Register

| Risk | Mitigation |
|---|---|
| Malayalam data is your real bottleneck, not compute | Start recording in Phase 2 immediately, in parallel with Phase 1 — don't wait until Phase 3 to start collecting |
| Full Moshi fine-tune may not converge well on your first pass | Phase 1 deliverable stands on its own regardless — protects your project even if Phase 3 slips |
| Long full-duplex sessions degrade in context quality | Known limitation even in TML's frontier system — budget for periodic context resets, don't treat it as a bug you must fully solve |
| Screen/OS action layer is a real safety surface | Tiered-trust gate is non-negotiable, build it before any autonomous execution goes live |

---

## 6. What to build first

Given everything above, the highest-leverage next step is **Phase 1** — it needs zero new ML, builds on API patterns you've already worked with (Claude + Groq calls from the invoice-studio project), and gives you something to demo within days. Phase 2 (data collection) should start now in parallel since it has the longest lead time of anything in the plan.

