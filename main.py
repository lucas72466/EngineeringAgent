from fastapi import FastAPI

from api.task import CompleteTaskResp, complete_task
from model.control_task import TaskSpecs

app = FastAPI()


@app.post("/api/complete_task", response_model=CompleteTaskResp)
def handle_complete_task(specs: TaskSpecs):
    return complete_task(specs)
