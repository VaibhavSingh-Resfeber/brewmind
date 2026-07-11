from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.chat import router as chat_router
from app.core.database import test_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    test_connection()
    yield


app = FastAPI(
    title="BrewMind",
    description="AI-powered specialty coffee intelligence for Munich",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat_router)


@app.get("/")
def root():
    return {"status": "BrewMind is alive ☕", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
