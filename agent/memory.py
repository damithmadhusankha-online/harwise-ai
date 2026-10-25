

class Memory:
    def __init__(self, system_prompt: str, max_messages: int = 40):
        self.system = {"role": "system", "content": system_prompt}
        self.messages: list[dict] = []
        self.max_messages = max_messages

    def add(self, message: dict) -> None:
        self.messages.append(message)
        self._trim()

    def _trim(self) -> None:
        if len(self.messages) <= self.max_messages:
            return
        trimmed = self.messages[-self.max_messages:]
        
        while trimmed and trimmed[0].get("role") == "tool":
            trimmed.pop(0)
        self.messages = trimmed

    def history(self) -> list[dict]:
        return [self.system] + self.messages

    def clear(self) -> None:
        self.messages = []
