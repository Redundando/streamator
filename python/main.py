import asyncio
import uvicorn
from fastapi import FastAPI
from streamator import JobLogger
from streamator.fastapi import add_log_routes

app = FastAPI() #
add_log_routes(app)


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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
