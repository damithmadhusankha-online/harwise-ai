import json

import ollama

from agent.memory import Memory
from agent.prompts import SYSTEM_PROMPT
from tools.registry import TOOL_SCHEMAS, run_tool
from utils.logger import get_logger

log = get_logger("harwise.agent")

MAX_STEPS = 8 


class HarwiseAgent:
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        self.memory = Memory(SYSTEM_PROMPT)

    def ask(self, user_text: str) -> str:
        user_text = (user_text or "").strip()
        if not user_text:
            return "Please type a question."
        if len(user_text) > 2000:
            return "That message is too long. Please keep it under 2000 characters."

        self.memory.add({"role": "user", "content": user_text})
        log.info("USER: %s", user_text)

        for step in range(1, MAX_STEPS + 1):
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=self.memory.history(),
                    tools=TOOL_SCHEMAS,
                )
            except ollama.ResponseError as e:
                log.error("ollama error: %s", e)
                return f"The model returned an error ({e}). Is '{self.model}' pulled? Try: ollama pull {self.model}"
            except Exception as e:
                log.error("cannot reach ollama: %s", e)
                return "I can't reach Ollama. Make sure it is running (try: ollama serve) and try again."

            message = response.message
            self.memory.add({
                "role": "assistant",
                "content": message.content or "",
                **({"tool_calls": [
                    {"function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in message.tool_calls
                ]} if message.tool_calls else {}),
            })

            if not message.tool_calls:
                log.info("ASSISTANT: %s", message.content)
                return message.content or "(no answer)"

            for call in message.tool_calls:
                log.info("step %d: model called %s", step, call.function.name)
                result = run_tool(call.function.name, call.function.arguments)
                self.memory.add({
                    "role": "tool",
                    "tool_name": call.function.name,
                    "content": json.dumps(result, default=str),
                })

        log.warning("hit MAX_STEPS without a final answer")
        return "I couldn't finish that in a reasonable number of steps. Please try a simpler question."
