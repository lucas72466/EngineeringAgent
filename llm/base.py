from abc import ABC


class LLM(ABC):
    def __init__(self):
        pass

    def complete(self, prompt: str) -> str:
        raise NotImplementedError