import asyncio

from central_agent import CentralAgentLLM, AgentNotFoundError
from model.control_task import FinalTaskDesignResult
from model.control_task import TaskSpecs
from pydantic import BaseModel, Field


class CompleteTaskResp(BaseModel):
    is_success: bool = Field(..., description="task completed successfully or not")
    msg: str = Field(..., description="execution message")
    final_result: FinalTaskDesignResult


async def complete_task(specs: TaskSpecs, _async: bool = False, result_queue: asyncio.Queue = None) -> CompleteTaskResp:
    central_agent = CentralAgentLLM()
    try:
        result = await central_agent.complete_task(specs, _async, result_queue)
    except AgentNotFoundError as e:
        return CompleteTaskResp(
            is_success=False,
            msg=str(e),
            final_result=None
        )
    else:
        return CompleteTaskResp(
            is_success=result.is_success,
            msg="Successfully completed task",
            final_result=result
        )