from agent_runtime.core.task import Task
from agent_runtime.core.state import AgentState
from agent_runtime.core.loop import AgentLoop
from agent_runtime.tools.registry import ToolRegistry
from agent_runtime.tools.browser import BrowserAdapter
from agent_runtime.models.ollama import OllamaModel
import time

# Wrap the model to add debug logging
class DebugModel:
    def __init__(self, model):
        self.model = model
        self.call_count = 0

    def generate_action(self, prompt):
        self.call_count += 1
        print(f"\n[MODEL CALL #{self.call_count}] Sending prompt ({len(prompt)} chars)...")
        start = time.time()
        try:
            result = self.model.generate_action(prompt)
            elapsed = time.time() - start
            print(f"[MODEL CALL #{self.call_count}] Got response in {elapsed:.1f}s: {result}")
            return result
        except Exception as e:
            elapsed = time.time() - start
            print(f"[MODEL CALL #{self.call_count}] FAILED in {elapsed:.1f}s: {type(e).__name__}: {e}")
            # Try to get raw text for debugging
            try:
                raw = self.model.generate(prompt)
                print(f"[DEBUG] Raw model output: [{raw[:300]}]")
            except Exception:
                pass
            raise

browser = BrowserAdapter()
browser.start()
print("Browser started.")

tools = ToolRegistry()
tools.register("browser.navigate", browser.navigate)
tools.register("browser.find", browser.find)
tools.register("browser.scroll", browser.scroll)
tools.register("browser.extract", browser.extract)

task = Task(
    goal="Navigate to https://en.wikipedia.org/wiki/Raptor_Lake, locate the Intel Core i7-14700 entry, and extract its total CPU core count.",
    url="https://en.wikipedia.org/wiki/Raptor_Lake",
    constraints=["Do not search the web.", "Do not create files.", "Return only a single number."],
    allowed_actions=["navigate", "find_text", "scroll", "extract", "finish"],
)

state = AgentState(task)
model = DebugModel(OllamaModel(model="qwen3:14b"))
loop = AgentLoop(task=task, model=model, tools=tools)

start_time = time.time()
try:
    answer = loop.run(state)
    print(f"\nFINAL ANSWER: {answer}")
except Exception as e:
    print(f"\nLOOP FAILED: {type(e).__name__}: {e}")
finally:
    elapsed = time.time() - start_time
    print(f"\n--- WALL CLOCK TIME: {elapsed:.1f}s ---")
    print(f"--- TOTAL STEPS IN HISTORY: {len(state.history)} ---")
    rejections = sum(1 for h in state.history if h['action'] == 'rejected')
    print(f"--- REJECTIONS: {rejections} ---")
    print(f"\n--- FULL ACTION HISTORY ---")
    for i, entry in enumerate(state.history, 1):
        print(f"Step {i}: {entry}")
    browser.stop()
