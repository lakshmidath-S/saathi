# Saathi — a guarded local agent runtime for web forms

Saathi is my final-year project. The goal is an offline, privacy-first assistant that keeps your details on your own machine and fills government web forms for you. It is meant to work on messy, inconsistent sites without per-site scripts, and to stop and ask you when it needs an OTP or information it doesn't have.

This repo holds the **agent runtime** that the assistant is built on. It is a work in progress.

## Why a custom runtime

I started with `browser-use` and Qwen3-14B (via Ollama) on a deliberately simple task:

> Open the Wikipedia *Raptor Lake* page, find the Intel Core i7-14700, return its total core count. Don't search the web, don't write files, stop as soon as you know the answer.

The agent went to the right page, then wandered off. It wrote summary files, kept rewriting them, started "collecting 20 papers", and hit the step limit without answering.

My takeaway: **a capable model is not enough. The runtime around it needs deterministic controls.** So in Saathi, the model only *proposes* actions, and the runtime decides whether each one is allowed.

## How it works

```
Task (goal + constraints + allowed actions)
        │
        ▼
Context builder ──► Local LLM (Ollama / Qwen)
        ▲                   │
        │            JSON action only
        │                   ▼
   Agent state  ◄──  Verifier (policy + task rules)
  (history,                 │
   results)                 ▼
        └──────────  Tool registry ──► Browser (Patchright)
```

- **Task:** the goal, the constraints, and a whitelist of allowed actions.
- **Context builder:** builds a controlled prompt from the task and the current state, instead of dumping the whole history into the model.
- **Model:** must return a single JSON action. Anything else is rejected.
- **Verifier:** blocks unknown actions, forbidden actions (for example search or file writes), and anything outside the task. Rejections are recorded.
- **Tool registry:** only registered tools can run, for example `browser.navigate`, `browser.find`, `browser.scroll` and `browser.extract`.
- **State:** records every step, so the loop can stop once the answer is known.

## Project layout

```
agent_runtime/
├── core/        # Task, AgentState, AgentLoop
├── context/     # context building / management
├── memory/      # memory manager (early)
├── planning/    # planner (early)
├── models/      # Ollama model adapter
└── tools/       # tool registry, browser adapter (Patchright)
tests/           # pytest suite for the safety boundary and loop
run_parivahan.py # live run against a real browser with a local model
```

## Status

- [x] Task, state, context builder, verifier, tool registry
- [x] Tests: unknown and forbidden actions blocked, permitted actions accepted, state records execution, loop finishes
- [x] Real browser adapter and live runs with `qwen3:14b`
- [ ] Reliable completion of the Wikipedia acceptance task end to end
- [ ] Vision model for reading pages, plus a separate reasoning model
- [ ] Local encrypted store for user details and documents
- [ ] Human-in-the-loop pauses (OTP, missing fields)
- [ ] Real government form flows

## Running it

Needs Python 3.10+, [Ollama](https://ollama.com) with `qwen3:14b` pulled, and [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) (a Playwright fork).

```bash
python -m venv .venv && source .venv/bin/activate
pip install patchright pytest requests
patchright install chromium
ollama pull qwen3:14b

python -m pytest -m "not integration" -v   # unit tests
python run_parivahan.py                     # live run (prints every model call and step)
```

## Team

Final-year major project, CSE, Mar Athanasius College of Engineering (KTU) — Group 16.
