import asyncio
import json

from DesignMemory import design_memory
from instruction import overall_instruction_PI, response_format_PI
from llm.base import LLM
from llm.gpt4 import GPT4
from model.control_task import TaskDesignResult, FinalTaskDesignResult
from subagents.base import AbstractSubAgent
from util import check_stability, loop_shaping, feedback_prompt


class first_ord_stable_Design(AbstractSubAgent):
    agent_name = "First-order stable system"

    def __init__(self, system, thresholds, task_requirement, scenario,
                 llm: LLM = GPT4(engine='gpt-4o-2024-08-06', temperature=0.0, max_tokens=1024)):
        super().__init__(system, thresholds, task_requirement, scenario)
        self.llm = llm
        self.max_attempts = 10
        self.design_memory = design_memory()

        # new added attrs
        self.system = system
        self.thresholds = thresholds
        self.task_requirement = task_requirement
        self.scenario = scenario
        self.num_attempt = 1
        self.prompt = overall_instruction_PI  #
        self.new_problem = "Now consider the following design task:" + self.task_requirement
        self.problem_statement = self.prompt + self.new_problem + response_format_PI
        self.conversation_log = []
        self.is_success = False

    async def handle_task(self, result_chan: asyncio.Queue = None) -> FinalTaskDesignResult:
        while self.num_attempt < self.max_attempts:
            print("attempt {}".format(self.num_attempt))
            success, cur_result = self.handle_one_iter_design()
            if result_chan is not None:
                await result_chan.put(cur_result)
                await result_chan.join()
                print("put result to queue", cur_result)
            if success:
                if result_chan is not None:
                    await result_chan.put(TaskDesignResult(success=True, parameters={}, performance={},
                                                           conversation_round=-1))
                break
        return self.construct_final_result()

    def handle_one_iter_design(self):
        # Construct the design prompt
        # Call LLM to complete the prompt
        response = self.llm.complete(self.problem_statement)
        self.conversation_log.append({
            "Problem Statement": self.problem_statement,
            "Response": response
        })

        data = json.loads(response)

        # parameters for plant transfer function
        num = [self.system['num'][0]]
        den = self.system['den']

        # Extract the list of parameters
        parameters = data['parameter']
        omega_L = parameters[0]
        beta_b = parameters[1]
        is_stable = check_stability(omega_L, beta_b, num, den)
        if is_stable:
            _, phase_margin, _, settlingtime, _, sse = loop_shaping(omega_L, beta_b, num, den)
            self.design_memory.add_design(
                parameters={'omega_L': omega_L, 'beta_b': beta_b},
                performance={'phase_margin': phase_margin, 'settling_time_min': settlingtime,
                             'settling_time_max': settlingtime, 'steadystate_error': sse}
            )
            design = self.design_memory.get_latest_design()
            is_succ = True  # Assume success unless a metric fails
            for metric, specs in self.thresholds.items():
                value = design['performance'].get(metric)
                if value is not None:
                    if 'min' in specs and value < specs['min']:
                        is_succ = False  # Set success to False if any metric fails
                    elif 'max' in specs and value > specs['max']:
                        is_succ = False  # Set success to False if any metric fails
            if is_succ:
                print("The current design satisfies the requirement.")
                print(f"Phase Margin is {phase_margin}")
                print(f"Settling Time is {settlingtime}")
                print(f"Steady-state error is {sse}")

                self.is_success = True

                # Save success information and final design to the log
                self.conversation_log.append({
                    "Design Success": True,
                    "Final Design Parameters": design['parameters'],
                    "Final Design Performance": design['performance']
                })
                cur_iter_result = TaskDesignResult(
                    success=True,
                    parameters=design['parameters'],
                    performance=design['performance'],
                    conversation_round=self.num_attempt + 1
                )
                return True, cur_iter_result
            else:
                # abaltion 1: with or without feedback
                feedback = feedback_prompt(self.design_memory, self.thresholds)
                self.problem_statement = self.prompt + self.new_problem + "\n\n" + feedback + response_format_PI
        else:  # not stable
            self.design_memory.add_design(
                parameters={'omega_L': omega_L, 'beta_b': beta_b},
                performance={'phase_margin': 'unstable', 'settling_time': 'unstable', 'steadystate_error': 'unstable'}
            )
            # Save unstable design information to the log
            self.conversation_log.append({
                "Design Success": False,
                "Failed Design Parameters": self.design_memory.get_latest_design()['parameters'],
                "Failed Design Performance": self.design_memory.get_latest_design()['performance']
            })
            # Save unstable design information to the log
            feedback = feedback_prompt(self.design_memory, self.thresholds)
            self.problem_statement = self.prompt + self.new_problem + "\n\n" + feedback + response_format_PI
        self.num_attempt += 1
        design = self.design_memory.get_latest_design()
        cur_iter_result = TaskDesignResult(
            success=False,
            parameters=design['parameters'],
            performance=design['performance'],
            conversation_round=self.num_attempt + 1
        )
        return False, cur_iter_result

    def construct_final_result(self):
        history_result = []
        for idx, design in enumerate(self.design_memory.get_all_designs()):
            history_result.append(
                TaskDesignResult(
                    success=False if idx != len(self.design_memory.get_all_designs()) else self.is_success,
                    parameters=design['parameters'],
                    performance=design['performance'],
                    conversation_round=idx + 1
                )
            )
        res = FinalTaskDesignResult(
            used_agent=self.agent_name,
            is_success=self.is_success,
            design_history=history_result,
        )
        return res
