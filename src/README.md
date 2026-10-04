# Source Code

This directory contains the entire source code for the Autonomous Disaster Response Planner.

## Structure

- **`backend/`**: FastAPI application containing the API endpoints, database models, planning engine (OR-Tools CP-SAT), and IBM watsonx.ai integrations.
- **`frontend/`**: React + Vite single-page application for the Coordinator and Responder interfaces.
- **`docker-compose.yml`**: Configuration to run the backend, frontend, and PostgreSQL PostGIS database locally.

## Setup

1. Copy `.env.example` to `.env` and fill in the `WATSONX_API_KEY` and other required credentials.
2. Run `docker-compose up -d --build` to start all services.
3. Access the frontend at `http://localhost:5173` and the API at `http://localhost:8000/docs`.
