from fastapi import FastAPI

from api.routers import health

app = FastAPI(title="FastAPI Template")

app.include_router(health.router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok"}
