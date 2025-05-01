import abc
import importlib
import inspect
import pkgutil
from abc import ABC

from typing import List, Dict

from llm.base import LLM
from llm.gpt4 import GPT4
from model.control_task import TaskDesignResult, FinalTaskDesignResult


class AbstractSubAgent(ABC):
    agent_name = "AbstractSubAgent"

    def __init__(self, system, thresholds, task_requirement, scenario,
                 llm: LLM = GPT4(engine='gpt-4o-2024-08-06', temperature=0.0, max_tokens=1024)):
        pass

    @abc.abstractmethod
    def handle_task(self) -> FinalTaskDesignResult:
        # used for try as much as possible until success or reach max attempts
        raise NotImplementedError

    @abc.abstractmethod
    def handle_one_iter_design(self):
        # used for chat-style interactions
        raise NotImplementedError


def get_all_available_subagents() -> (List[type], Dict[int, str]):
    classes = {}
    names = {}
    count = 1
    for finder, module_name, is_pkg in pkgutil.iter_modules(['subagents']):
        if module_name == "base":
            continue
        module = importlib.import_module(f"subagents.{module_name}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, AbstractSubAgent) and cls is not AbstractSubAgent:
                if not hasattr(cls, "agent_name"):
                    raise Exception("No agent name for cls {}".format(cls.__name__))
                classes[count] = cls
                names[count] = cls.agent_name
    return classes, names


subagents_classes, subagents_names = get_all_available_subagents()
