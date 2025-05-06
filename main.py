import asyncio
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from starlette.websockets import WebSocket, WebSocketDisconnect

from api.task import CompleteTaskResp, complete_task
from model.control_task import TaskSpecs, TaskDesignResult

load_dotenv()

app = FastAPI(title="ControlAgent Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this down to your vercel domain in production
    allow_credentials=True,
    allow_headers=["*"],
)


@app.post("/api/complete_task", response_model=CompleteTaskResp)
async def handle_complete_task(specs: TaskSpecs):
    return await complete_task(specs)


async def _queue_iter(q: asyncio.Queue):
    while True:
        item = await q.get()
        yield item
        q.task_done()


@app.websocket("/api/complete_task")
async def handle_complete_task_websocket(websocket: WebSocket):
    await websocket.accept()
    task_spec_data = await websocket.receive_json()
    task_spec = TaskSpecs.parse_obj(task_spec_data)
    print("Received task spec:", task_spec)

    result_chan: asyncio.Queue[TaskDesignResult] = asyncio.Queue()
    design_task = asyncio.create_task(complete_task(task_spec, _async=True, result_queue=result_chan))
    print("start design task")

    async def forward_to_client():
        try:
            async for cur_result in _queue_iter(result_chan):
                print("Send result to client:", cur_result)
                await websocket.send_json(cur_result.model_dump(mode="json"))
                if cur_result.conversation_round == -1:
                    await websocket.close(code=1000, reason="Task completed")
                    break
        except asyncio.CancelledError:
            return

    forward_task = asyncio.create_task(forward_to_client())
    print("start forwarding task")

    try:
        await asyncio.gather(design_task, forward_task)
        print("Finished task")
        # receive further instruction from FE
        # while True:
        #     await websocket.receive_json()
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print("Encountered an exception:", e)
        traceback.print_exc()
        await websocket.close(code=1011, reason=str(e))
    finally:
        print("request exit")
        design_task.cancel()
        forward_task.cancel()
