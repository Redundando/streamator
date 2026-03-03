import asyncio
import uvicorn
import warnings
from fastapi import FastAPI
from streamator import JobLogger, JobEmitter
from streamator.fastapi import add_log_routes, add_job_routes

app = FastAPI()

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    add_log_routes(app)

add_job_routes(app)


@app.post("/start")
async def start():
    logger = JobLogger()

    async def job():
        for i in range(1, 6):
            await asyncio.sleep(1)
            logger.log(f"Step {i} of 5", level="info")
        logger.log("Done", level="success")
        logger.close()

    asyncio.create_task(job())
    return {"log_job_id": logger.job_id}


@app.post("/start-emitter")
async def start_emitter():
    emitter = JobEmitter()

    async def job():
        async with emitter:
            for i in range(1, 6):
                await asyncio.sleep(1)
                emitter.emit({"event": "progress", "current": i, "total": 5})
                emitter.log(f"Step {i} of 5")
            emitter.set_result({"steps_completed": 5})
            emitter.log("Done", level="success")

    task = asyncio.create_task(job())
    emitter.track(task)
    return {"job_id": emitter.job_id}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
