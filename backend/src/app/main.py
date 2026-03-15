from fastapi import FastAPI
from src.app.router import router

app = FastAPI(
    title="AlphaPilot API",
    description="AI Autonomous Trading System",
    version="0.1.0",
)

app.include_router(router)
