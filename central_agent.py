import json

import control as ctrl

from instruction import response_instruct
from llm.base import LLM
from llm.gpt4 import GPT4
from model.control_task import TaskSpecs
from subagents.base import subagents_names, subagents_classes

central_agent_prompt = """

You are an expert control engineer tasked with analyzing the provided control task and assigning it to the most suitable task-specific agent, each specializing in designing controllers for specific system types.

First, analyze the dynamic system to identify its type, such as a first-order stable system, second-order unstable system, first-order with time delay, higher-order system, etc. Based on this analysis, assign the task to the corresponding task-specific agent that specializes in the identified system type.

Here are the available task-specific agents:
{}

Ensure the selected agent can effectively tailor the control design process.

""".format("\n".join([f"- **Agent {idx}**: {name}" for idx, name in subagents_names.items()]))

INVALID_AGENT_NUMBER = -1


class AgentNotFoundError(Exception):
    def __init__(self):
        super().__init__(
            "No suitable sub-agent found for this task"
        )


class CentralAgentLLM:

    def __init__(self, llm: LLM = GPT4(engine='gpt-4o-2024-08-06', temperature=0.0, max_tokens=1024)):
        self.llm = llm
        # Define the available sub-agents

    def choose_subagent(self, task_specs: TaskSpecs):
        requirement_summary = """
                    \nDesign the controller to meet the following specifications:
                    Phase margin greater or equal {phase_margin_min} degrees,
                    Settling time greater or equal {settling_time_min} sec,
                    Settling time should also be less or equal to {settling_time_max} sec,
                    Steady state error less or equal {steadystate_error_max}.
                """.format_map(task_specs.dict())

        # Provide the plant transfer function
        plant = ctrl.TransferFunction(task_specs.num, task_specs.den)
        user_request = "\nPlease design the controller for the following system: " + str(plant)
        if task_specs.tau is not None:
            user_request += " with time delay {tau} sec".format(tau=task_specs.tau)
        user_request += requirement_summary

        prompt = "".join([central_agent_prompt, user_request, response_instruct])
        # Parse the LLM response, which follows a strict JSON format.
        response = self.llm.complete(prompt)

        parsed_response = json.loads(response)
        agent_number = int(parsed_response.get("Agent Number"))

        if agent_number in subagents_classes:
            return agent_number, subagents_names[agent_number], parsed_response['Task Requirement']
        else:
            return INVALID_AGENT_NUMBER, "", ""

    def complete_task(self, task_specs: TaskSpecs):
        agent_number, agent_name, task_requirement = self.choose_subagent(task_specs)
        if agent_number in subagents_classes:
            agent = subagents_classes[agent_number](task_specs, task_specs.construct_thresholds(),
                                                    task_requirement, task_specs.scenario)
            result = agent.handle_task()
            return result
        else:
            raise AgentNotFoundError()
