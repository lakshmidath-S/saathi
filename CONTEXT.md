Agent Runtime Project — Full Handoff Context
0. READ THIS FIRST

This document is the persistent handoff/context for an ongoing lab project.

The goal is to build a small, reliable local AI agent runtime around a local Ollama model, rather than relying entirely on browser-use's built-in agent loop.

The project started because the browser-use agent was behaving badly on a simple constrained task.

The intended system should eventually:

    use a local LLM such as Qwen through Ollama
    understand a narrowly defined task
    maintain explicit task state
    build controlled context for the model
    allow only explicitly permitted actions
    prevent dangerous/unrequested tools
    execute browser actions
    remember useful observations/state
    verify model actions before execution
    avoid hallucinated tasks
    stop immediately when the requested answer is known
    avoid creating files when the task forbids files
    avoid web search when the task forbids search
    eventually support better memory/context/planning without making the system unnecessarily complicated

This is NOT finished yet.

We are building the runtime incrementally and testing each component.
1. ORIGINAL PROBLEM

The original experiment used:

    browser-use
    Ollama
    Qwen 3 14B

The model was asked to perform a very simple task:

    Open the Wikipedia Raptor Lake page, locate the Intel Core i7-14700 entry, find the total CPU core count, return the single number, do not search the web, do not create or modify files, do not perform any other task, and stop immediately once the answer is known.

Instead, the browser-use agent went completely off-task.

It:

    Navigated to the correct Wikipedia URL.
    Generated summaries about Raptor Lake.
    Wrote raptor_lake_summary.md.
    Repeatedly rewrote that file.
    Started discussing/collecting unrelated papers.
    Wrote papers.md.
    Claimed it was collecting 20 papers.
    Eventually stopped because of the step limit.
    Returned information about papers instead of the CPU core count.

The judge correctly marked the run as FAIL.

The important lesson:

A capable LLM alone is not enough.

The runtime needs deterministic controls around the model.
2. CORE DESIGN IDEA

Instead of:

Task
  ↓
LLM
  ↓
Browser-use agent does whatever it thinks is useful

we want:

                 ┌──────────────────┐
                 │      Task        │
                 │ goal + rules     │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │     Context      │
                 │ controlled prompt│
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │   Local LLM      │
                 │ Ollama / Qwen    │
                 └────────┬─────────┘
                          ↓
                 JSON action only
                          ↓
                 ┌──────────────────┐
                 │    Verifier      │
                 │ policy + task    │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │   Tool Registry  │
                 └────────┬─────────┘
                          ↓
                 Browser / other tool
                          ↓
                 ┌──────────────────┐
                 │     State        │
                 │ history/results  │
                 └────────┬─────────┘
                          ↓
                       Context
                          ↑
                    repeat loop

The LLM proposes.

The runtime decides whether the proposal is legal.

The tools execute.

The state records what happened.
3. CURRENT PROJECT LOCATION

The project is currently:

~/mp

The Python virtual environment is:

~/mp/.venv

Activate it before working:

cd ~/mp
source .venv/bin/activate

Verify:

which python

Expected:

/home/csnn04/mp/.venv/bin/python

4. CURRENT DIRECTORY STRUCTURE

Current intended structure:

agent_runtime/
├── __init__.py
│
├── core/
│   ├── __init__.py
│   ├── state.py
│   ├── task.py
│   └── loop.py
│
├── context/
│   ├── __init__.py
│   ├── manager.py
│   └── builder.py
│
├── memory/
│   ├── __init__.py
│   └── manager.py
│
├── planning/
│   ├── __init__.py
│   ├── planner.py
│   └── verifier.py
│
├── tools/
│   ├── __init__.py
│   ├── registry.py
│   └── browser.py
│
├── policy/
│   ├── __init__.py
│   └── permissions.py
│
└── models/
    ├── __init__.py
    ├── ollama.py
    └── router.py

tests/
├── test_policy.py
├── test_state.py
├── test_ollama.py
├── test_context.py
├── test_loop.py
└── test_verifier.py

Some files are currently implemented only partially or are still empty.

Do NOT assume every file above is complete.
5. TASK MODEL

Current:

from dataclasses import dataclass, field


@dataclass
class Task:
    goal: str
    url: str | None = None
    constraints: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    status: str = "running"

    def can_do(self, action: str) -> bool:
        return action in self.allowed_actions

    def finish(self):
        self.status = "done"

Important:

The task is deliberately explicit.

It contains:

    goal
    optional url
    constraints
    allowed_actions
    status

The key security/control function is:

def can_do(self, action: str) -> bool:
    return action in self.allowed_actions

This means the model cannot simply invent an action and expect the runtime to execute it.
6. STATE MODEL

Current:

from dataclasses import dataclass, field
from .task import Task


@dataclass
class AgentState:
    task: Task
    history: list[dict] = field(default_factory=list)
    last_result: str | None = None

    def record(self, action: str, result: str):
        self.history.append({
            "action": action,
            "result": result,
        })
        self.last_result = result

State currently remembers:

task
history
last_result

The record() method records each action and its result.

This is important because eventually context should be constructed from state rather than giving the model uncontrolled access to everything.

Potential future additions:

current_url
observations
step_count
visited_urls
answer
errors
short-term memory

But do not add complexity until needed.
7. POLICY SYSTEM

Current:

from enum import Enum


class TrustLevel(Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    BLOCK = "block"


TOOL_POLICY = {
    "browser.navigate": TrustLevel.ALLOW,
    "browser.find": TrustLevel.ALLOW,
    "browser.scroll": TrustLevel.ALLOW,
    "browser.extract": TrustLevel.ALLOW,

    "browser.search": TrustLevel.BLOCK,

    "filesystem.read": TrustLevel.ALLOW,
    "filesystem.write": TrustLevel.CONFIRM,

    "shell.run": TrustLevel.CONFIRM,
}


def check_permission(tool_name: str) -> TrustLevel:
    return TOOL_POLICY.get(tool_name, TrustLevel.BLOCK)

This is one of the most important pieces.

Unknown tools are blocked by default:

return TOOL_POLICY.get(tool_name, TrustLevel.BLOCK)

Therefore:

unknown tool → BLOCK

This is intentional.

The original browser-use failure demonstrated why this matters.

The task said:

Do not create or modify files.

Yet the agent called file-writing tools.

Our runtime should prevent this independently of what the LLM wants.
8. TOOL REGISTRY

Current:

from typing import Callable, Any

from agent_runtime.policy.permissions import (
    TrustLevel,
    check_permission,
)


class ToolRegistry:

    def __init__(self):
        self.tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, function: Callable[..., Any]):
        self.tools[name] = function

    def execute(self, name, **kwargs):
        permission = check_permission(name)

        if permission == TrustLevel.BLOCK:
            raise PermissionError(
                f"Tool '{name}' is blocked by policy."
            )

        if permission == TrustLevel.CONFIRM:
            raise PermissionError(
                f"Tool '{name}' requires user confirmation."
            )

        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")

        return self.tools[name](**kwargs)

This gives us:

LLM action
   ↓
tool name
   ↓
permission check
   ↓
registered tool
   ↓
execution

The runtime should NEVER blindly execute arbitrary model-generated tools.
9. OLLAMA MODEL

Current:

import json
import requests


class OllamaModel:
    def __init__(
        self,
        model: str = "qwen3:14b",
        host: str = "http://localhost:11434",
    ):
        self.model = model
        self.host = host.rstrip("/")

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()
        return response.json()["response"]

    def generate_action(self, prompt: str) -> dict:
        text = self.generate(prompt)

        text = text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "", 1)
            text = text.replace("```", "")
            text = text.strip()

        return json.loads(text)

This successfully communicates with:

Ollama

using:

qwen3:14b

The integration test passed.

The test took about 40 seconds, which is normal for a local 14B model depending on hardware.
10. MODEL TEST

Current integration test proves that Qwen can return an action.

The important result:

tests/test_ollama.py::test_qwen_returns_action PASSED

Therefore:

Python → Ollama → Qwen → JSON → Python

works.

There is currently a pytest warning because the test uses:

@pytest.mark.integration

without registering the marker.

This is NOT a functional failure.

Later, add a pytest.ini if desired:

[pytest]
markers =
    integration: tests requiring external services such as Ollama

11. CONTEXT BUILDER

Current:

def build_context(task, state):
    return f"""
TASK:
{task.description}

RULES:
- Only work on this task.
- Do not create files.
- Do not search the web unless explicitly allowed.
- Do not invent another task.
- Return exactly one JSON action.

CURRENT URL:
{state.current_url}

ALLOWED ACTIONS:
navigate
find_text
scroll
finish

If you know the answer, immediately use:
{{"action": "finish", "answer": "..."}}
"""

IMPORTANT:

There may be a mismatch here.

The current Task dataclass has:

task.goal

not:

task.description

Also the current AgentState shown above does not have:

current_url

Therefore this file needs to be reconciled with the current state/task implementation before the real browser test.

The context test passed previously, but the implementation should be checked carefully.

Do not blindly add random fields.
12. AGENT LOOP

The previous loop implementation worked for the simple fake-model test.

Conceptually it did:

for each step:

    build context

    ask model for JSON action

    validate action structure

    check task permission

    if finish:
        save answer
        mark task done
        return answer

    map action → browser tool

    execute tool

    record result

after max steps:
    fail

The previous implementation was roughly:

class AgentLoop:
    def __init__(self, task, model, tools, max_steps=10):
        self.task = task
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    def run(self, state):
        for _ in range(self.max_steps):
            prompt = build_context(self.task, state)

            action = self.model.generate_action(prompt)

            if not isinstance(action, dict):
                raise ValueError("Model must return a JSON object.")

            action_name = action.get("action")

            if not action_name:
                raise ValueError("Model response has no action.")

            if not self.task.can_do(action_name):
                raise PermissionError(
                    f"Action '{action_name}' is not allowed for this task."
                )

            if action_name == "finish":
                answer = action.get("answer")

                if answer is None:
                    raise ValueError("finish action requires an answer.")

                state.record("finish", str(answer))
                self.task.finish()
                return str(answer)

            tool_name = f"browser.{action_name.replace('find_text', 'find')}"

            kwargs = {
                key: value
                for key, value in action.items()
                if key != "action"
            }

            result = self.tools.execute(tool_name, **kwargs)

            state.record(action_name, str(result))

        raise RuntimeError("Maximum agent steps reached.")

A loop test passed:

tests/test_loop.py::test_loop_finishes_with_model_answer PASSED

However, this is NOT yet production-quality.

The action-to-tool mapping is currently simplistic and should eventually become explicit rather than relying on string replacement.
13. VERIFIER

agent_runtime/planning/verifier.py was initially empty.

We added a basic verifier and tests.

Current tests:

tests/test_verifier.py::test_verifier_allows_finish PASSED
tests/test_verifier.py::test_verifier_blocks_unknown_action PASSED
tests/test_verifier.py::test_verifier_blocks_search PASSED

This is important.

The verifier should become the deterministic gate between:

LLM proposal

and

tool execution

Architecture should eventually be:

LLM
 ↓
parse JSON
 ↓
verifier
 ↓
policy
 ↓
tool

NOT:

LLM
 ↓
tool directly

14. CURRENT TEST STATUS

Latest known test results:

5 passed, 1 warning

Specifically:

tests/test_ollama.py::test_qwen_returns_action PASSED
tests/test_policy.py::test_blocked_search PASSED
tests/test_policy.py::test_unknown_tool_blocked PASSED
tests/test_state.py::test_task_blocks_unknown_action PASSED
tests/test_state.py::test_state_records_actions PASSED

Context test:

tests/test_context.py::test_context_contains_task_and_constraints PASSED

Verifier + loop:

tests/test_verifier.py::test_verifier_allows_finish PASSED
tests/test_verifier.py::test_verifier_blocks_unknown_action PASSED
tests/test_verifier.py::test_verifier_blocks_search PASSED
tests/test_loop.py::test_loop_finishes_with_model_answer PASSED

So the basic architecture has already been validated in isolation.
15. PYTHON ENVIRONMENT ISSUE THAT WAS FIXED

Initially:

python -m pytest

failed because the virtual environment had Python but no pip/pytest.

We fixed it using:

python -m ensurepip --upgrade
python -m pip install -U pytest

After that:

python -m pytest

works while the virtual environment is active.

If python suddenly disappears:

source .venv/bin/activate

Then:

which python

should show:

/home/csnn04/mp/.venv/bin/python

16. IMPORTANT DESIGN PRINCIPLES

Do NOT turn this into a giant framework immediately.

The project should prioritize:
Deterministic control

The LLM should not have unrestricted authority.
Explicit task scope

The task defines what actions are allowed.
Default deny

Unknown tools/actions should be blocked.
Minimal context

Give the model the information it needs, not the entire world.
Structured output

The model should return a strict action object such as:

{
  "action": "find_text",
  "text": "Intel Core i7-14700"
}

or:

{
  "action": "finish",
  "answer": "20"
}

Immediate stopping

If the model knows the answer:

{
  "action": "finish",
  "answer": "20"
}

The runtime should stop immediately.
No hidden task expansion

If the task is:

Find CPU core count.

the model must not decide:

I'll summarize the whole article.

No unauthorized side effects

If the task says:

Do not create files.

then filesystem writing must be unavailable/blocked.
17. WHAT WE ARE NOT DOING YET

Do not prematurely integrate every popular AI-agent repository.

Ideas discussed include things like:

    LangChain
    LangGraph
    Mem0
    LlamaIndex
    context engines
    vector databases
    search engines
    browser-use
    agent memory systems
    planning frameworks
    RAG systems

These may eventually be useful.

But the immediate objective is NOT to recreate all of them.

We first need a tiny runtime that reliably completes:

Wikipedia → find target text → extract answer → finish

Once that works, components can be added where they solve a demonstrated problem.
18. WHY NOT JUST USE BROWSER-USE?

Browser-use is useful for browser interaction.

The problem is not necessarily that browser-use cannot browse.

The problem observed was:

LLM had too much freedom
+
weak task enforcement
+
unexpected tool behavior
+
poor stopping behavior

Therefore a better architecture is potentially:

Our Agent Runtime
       ↓
Browser Tool Adapter
       ↓
browser-use/browser automation
       ↓
actual browser

rather than letting browser-use own the entire reasoning loop.

Browser-use can become an execution layer.

Our runtime becomes the control layer.
19. TARGET FIRST END-TO-END TASK

The first real benchmark should be the original task:

Open:

https://en.wikipedia.org/wiki/Raptor_Lake

Find:

Intel Core i7-14700

Return:

total CPU core count

Constraints:

- Do not search the web.
- Do not create files.
- Do not modify files.
- Do not perform another task.
- Once the answer is known, immediately stop.
- Final answer should be a single number.

Expected answer:

20

The runtime should demonstrate that it can do this without:

file writes
web search
unrelated research
task expansion
unnecessary browsing
hallucinated work

20. NEXT ARCHITECTURE TO BUILD

The next clean version should be:

Task
  |
  v
AgentState
  |
  v
ContextBuilder
  |
  v
Ollama/Qwen
  |
  v
ActionParser
  |
  v
Verifier
  |
  +---- reject → ask model again / fail safely
  |
  v
ToolRegistry
  |
  v
Browser
  |
  v
State.record()
  |
  +---- answer known → finish
  |
  +---- otherwise → next context

21. EXPLICIT ACTION SCHEMA

Prefer a small fixed action vocabulary.

For example:

navigate
find_text
scroll
extract
finish

Example:

{
  "action": "navigate",
  "url": "https://en.wikipedia.org/wiki/Raptor_Lake"
}

Example:

{
  "action": "find_text",
  "text": "Intel Core i7-14700"
}

Example:

{
  "action": "scroll",
  "amount": 700
}

Example:

{
  "action": "extract",
  "instruction": "Return the total number of CPU cores for Intel Core i7-14700."
}

Example:

{
  "action": "finish",
  "answer": "20"
}

The runtime should reject anything outside the schema.
22. DO NOT LET THE MODEL INVENT TOOLS

Bad:

{
  "action": "write_file"
}

If write_file is not allowed:

REJECT

Bad:

{
  "action": "search_google"
}

If search is prohibited:

REJECT

Bad:

{
  "action": "research_papers"
}

Not part of the task:

REJECT

23. MEMORY STRATEGY

Eventually we can add memory.

But distinguish:
Working memory

Things needed during the current task:

current URL
important observations
last tool result
what has already been tried
answer candidates

Long-term memory

Information useful across future tasks.

Example:

Wikipedia pages often expose relevant table rows directly.

But long-term memory should NOT automatically be dumped into every prompt.

That can make hallucination worse.

A better future architecture:

Task
 ↓
memory retrieval
 ↓
relevance filter
 ↓
small context
 ↓
LLM

Memory is an optional source of context, not authority.
24. CONTEXT STRATEGY

The model should receive:

TASK
CONSTRAINTS
ALLOWED ACTIONS
CURRENT STATE
RECENT OBSERVATIONS
LAST TOOL RESULT

It should NOT receive huge irrelevant histories forever.

Eventually implement something like:

short-term memory:
last N events

important facts:
explicit extracted facts

task state:
current URL / completion status

long-term memory:
only relevant retrieved memories

This reduces context bloat and confusion.
25. PLANNING STRATEGY

Do not initially create a giant autonomous planner.

For a simple task, planning can be implicit:

navigate
→ find
→ inspect
→ finish

A planner becomes useful when tasks become multi-step.

Potential future planner output:

{
  "plan": [
    "Open target page",
    "Locate CPU model",
    "Read core count",
    "Finish"
  ]
}

But the executor should still verify every action.

Plan ≠ permission.
26. VERIFICATION STRATEGY

The verifier should eventually check several things:
Structural validity

Is it valid JSON?
Action validity

Is the action known?
Task validity

Is the action allowed by this task?
Policy validity

Is the corresponding tool allowed?
Argument validity

Are required parameters present?
Constraint validity

Does the action violate a task constraint?
Goal relevance

Does the action plausibly advance the current goal?

For example:

Task:
Find CPU core count.

Action:
write_file

→ reject

Task:
Find CPU core count.

Action:
browser.search

→ reject

Task:
Find CPU core count.

Action:
browser.navigate

→ allow

27. IMPORTANT DIFFERENCE: POLICY VS TASK

These are separate.

Task permission:

What is allowed for THIS task?

Policy:

What is allowed by the runtime/system?

An action should execute only if BOTH allow it.

Conceptually:

if not task.can_do(action):
    reject

if policy_blocks(tool):
    reject

execute()

This is stronger than either layer alone.
28. ERROR HANDLING

Eventually the loop should handle model errors safely.

Examples:

invalid JSON
missing action
unknown action
bad arguments
blocked tool
tool failure
browser failure
timeout
max steps

Do NOT silently continue after serious errors.

Prefer:

reject → explain internally → retry with constrained feedback

or:

fail safely

29. STEP BUDGET

The original browser-use run had a step budget of 5 and wasted all of it.

Our runtime should have an explicit budget.

Example:

max_steps = 10

But the model should not consume steps doing irrelevant work.

For this simple task, a reasonable sequence might be:

1. navigate
2. find_text
3. extract/read
4. finish

Potentially even fewer depending on browser observations.
30. FUTURE BROWSER ADAPTER

agent_runtime/tools/browser.py should eventually expose a small interface.

For example:

navigate(url)
find(text)
scroll(amount)
extract(...)

The rest of the runtime should not care whether the underlying implementation uses:

browser-use
Playwright
Selenium
CDP
custom browser automation

This is an adapter boundary.
31. FUTURE MODEL ROUTER

agent_runtime/models/router.py exists as a placeholder.

Eventually this could route between:

Qwen local
another local model
remote model
small model
large model

Example idea:

simple extraction → small/fast model
complex planning → larger model
verification → deterministic code or small model

But don't implement this until the single-model runtime works.
32. FUTURE MEMORY MANAGER

agent_runtime/memory/manager.py exists as a placeholder.

A future memory manager could provide:

remember(...)
search(...)
retrieve_relevant(...)
forget(...)

But avoid making the system dependent on an external memory service immediately.

Start with plain Python structures.

Only introduce Mem0 or a vector database when there is a concrete memory requirement.
33. POSSIBLE EXTERNAL COMPONENTS LATER

Potential technologies that may become useful:

Ollama
Qwen
browser-use
Playwright
LangGraph
LangChain
Mem0
LlamaIndex
vector databases
embedding models
RAG
search APIs

The selection principle should be:

    Add a component because it solves a measured problem, not because it is popular.

For this project, custom lightweight code is currently preferable to a giant dependency stack.
34. CURRENT PROJECT STATUS
Working

    Python virtual environment
    pytest
    Ollama connection
    Qwen 3 14B inference
    structured JSON action parsing
    Task object
    AgentState
    basic policy
    tool registry
    task action restriction
    verifier tests
    basic agent loop
    context builder test

Partially working

    context/state integration
    browser tool layer
    real browser execution
    full verifier integration
    planner
    memory
    model router

Not yet completed

    real end-to-end Wikipedia task
    reliable browser observation extraction
    robust action schema
    retry strategy
    final-answer verification
    complete constraint enforcement
    production-grade error handling

35. CURRENT BIGGEST PRIORITY

DO NOT spend the next session adding:

LangChain
Mem0
RAG
vector DB
multi-agent architecture
search engine
complex planner

until this works:

python test_agent.py

and the runtime reliably returns:

20

for the original Wikipedia task.

The smallest successful system is more valuable than a large architecture that still fails the basic benchmark.
36. NEXT SESSION — FIRST COMMANDS

Start with:

cd ~/mp
source .venv/bin/activate

Then:

which python
python --version

Then inspect:

find agent_runtime tests -type f | sort

Then run everything:

python -m pytest -v

Then inspect the actual files before changing anything:

cat agent_runtime/core/task.py
cat agent_runtime/core/state.py
cat agent_runtime/context/builder.py
cat agent_runtime/core/loop.py
cat agent_runtime/planning/verifier.py
cat agent_runtime/tools/registry.py
cat agent_runtime/policy/permissions.py
cat agent_runtime/models/ollama.py

Do NOT overwrite files blindly.
37. IMPORTANT: LOOP.PY WAS RECENTLY DELETED/RECREATED

At one point:

rm agent_runtime/core/loop.py

was executed because we were replacing the implementation.

Therefore the next session MUST inspect:

cat agent_runtime/core/loop.py

before assuming it contains the previously shown implementation.

If it is empty or incomplete, rebuild it carefully.
38. HOW TO CLEAR A FILE FROM SHELL

If you want to completely empty a file:

> filename

Example:

> agent_runtime/planning/verifier.py

Then edit:

nano agent_runtime/planning/verifier.py

Another option:

truncate -s 0 filename

39. HOW TO CONTINUE SAFELY

Before changing architecture:

    Run tests.
    Read current files.
    Change one component.
    Add/update its test.
    Run the relevant test.
    Run the complete test suite.
    Only then move to the next component.

Use:

python -m pytest -v

as the regression check.
40. SUCCESS CRITERIA

The project should eventually pass this test:

INPUT:
Open Raptor Lake Wikipedia page.
Find Intel Core i7-14700.
Return total CPU core count.
No search.
No file writes.
No unrelated work.
Stop immediately.

EXPECTED:
20

And the execution trace should look approximately like:

Task created
    ↓
navigate
    ↓
browser result
    ↓
find_text
    ↓
browser result
    ↓
extract/read
    ↓
finish("20")
    ↓
Task.status = done

There should NOT be:

write_file
search
research papers
summarization
unrelated browsing

41. THE BIGGER VISION

The long-term goal is a reusable local agent runtime where the LLM is treated as a reasoning component, not as an unrestricted operating system controller.

The desired philosophy is:

LLM = propose
Runtime = enforce
Verifier = judge legality
Tools = execute
State = remember
Context = inform
Memory = retrieve useful prior knowledge
Policy = limit authority

This should produce an agent that is:

    more predictable
    less hallucination-prone
    less likely to go off-task
    safer
    easier to debug
    easier to test
    easier to extend

The architecture should remain understandable.
42. HANDOFF TO ANOTHER AI

If another AI is given this file, tell it:

    This is an ongoing local AI-agent runtime project. Read CONTEXT.md completely before proposing changes. Do not restart the architecture from scratch. Inspect the current repository because some files may differ from the historical versions described here. Preserve working tests. The immediate goal is to finish a minimal deterministic end-to-end browser agent that uses Ollama/Qwen and completes the original Wikipedia CPU-core task without searching, writing files, or going off-task. Do not add large frameworks unless there is a demonstrated need. Work incrementally and provide exact shell commands and complete file contents when changing files.

The next AI should first run:

cd ~/mp
source .venv/bin/activate
python -m pytest -v

and inspect the repository.
43. FINAL REMINDER

The project is NOT about making Qwen magically smarter.

It is about putting a reliable runtime around the model.

The original failure proves why:

smart model
+
unrestricted agent loop
=
can still behave stupidly

The intended solution is:

smart model
+
tight context
+
explicit task
+
action schema
+
verifier
+
policy
+
controlled tools
+
state
+
bounded loop
=
much more reliable agent

Start simple.

Make the Wikipedia benchmark pass.

Then expand.

That gives you a single source-of-truth handoff rather than relying on this chat history.

One important thing: don't delete anything else tonight. Your next session should begin by reading CONTEXT.md, activating .venv, running the full tests, and inspecting the current loop.py because that file was recently deleted/recreated.
