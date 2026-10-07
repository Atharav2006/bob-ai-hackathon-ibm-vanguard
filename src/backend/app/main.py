from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .api.routes import router

# Run Alembic migrations on startup
import os
from alembic.config import Config
from alembic import command
alembic_cfg = Config("alembic.ini")
# Ensure the path is correct if running from different directory
if not os.path.exists("alembic.ini"):
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
try:
    command.upgrade(alembic_cfg, "head")
except Exception as e:
    print(f"Migration failed or skipped: {e}")
    # Fallback for dev environments without alembic setup
    Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager
from .seed import seed_database
from .database import SessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run on startup
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="Autonomous Disaster Response Planner API",
    description="API for managing disaster response scenarios, parsing field reports, and generating optimized resource allocations.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

from .auth_routes import add_auth_routes
add_auth_routes(app)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Disaster Response API is running."}
