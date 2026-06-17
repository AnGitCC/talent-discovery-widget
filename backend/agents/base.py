"""Base Agent class with shared LLM invocation logic."""
import json
import re
from llm.backend import get_llm


class Agent:
    """Base class for all agents. Provides LLM chat and JSON extraction."""

    def __init__(self, name: str, system_prompt: str = ""):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = get_llm()

    def ask(self, user_message: str, system_override: str = "", **kwargs) -> str:
        """Send a message to LLM, return text response."""
        system = system_override or self.system_prompt
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_message})
        return self.llm.chat(messages, **kwargs)

    def ask_json(self, user_message: str, system_override: str = "", **kwargs) -> dict:
        """Send message and parse JSON response."""
        text = self.ask(user_message, system_override, **kwargs)
        return self._extract_json(text)

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from LLM text response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {}
