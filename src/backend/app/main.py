from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Autonomous Disaster Response Planner API",
    description="API for managing disaster response scenarios, parsing field reports, and generating optimized resource allocations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Disaster Response API is running."}

# Future endpoints will include:
# /api/incidents
# /api/reports (with watsonx.ai extraction)
# /api/plans (triggering OR-Tools worker)
# /api/resources
