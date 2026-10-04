# Setup Guide

This guide walks you through setting up and running the Autonomous Disaster Response Planner locally.

## Prerequisites

- **Docker & Docker Compose** (version 2+)
- **Git**
- An **IBM watsonx.ai** account (API Key and Project ID)

## Environment Variables

Copy `src/.env.example` to `src/.env` and update it with your real credentials:

```bash
# PostgreSQL Database Configuration
DATABASE_URL=postgresql://disaster_user:disaster_password@db:5432/disaster_db

# watsonx.ai Integration
WATSONX_API_KEY=your_watsonx_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# IBM Bob Integration
IBM_BOB_API_KEY=your_ibm_bob_api_key_here

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000
```

## Installation & Running

1. **Clone the repository:**
   ```bash
   git clone https://github.com/drijesh-ppatel/bob-ai-hackathon-submission-template.git
   cd Disaster_Response_Project
   ```

2. **Navigate to the source directory:**
   ```bash
   cd src
   ```

3. **Build and start the services using Docker Compose:**
   ```bash
   docker-compose up --build -d
   ```

4. **Verify it's working:**
   - **Frontend:** Open your browser and navigate to `http://localhost:5173`. You should see the React dashboard indicating the backend is running.
   - **Backend API Docs:** Navigate to `http://localhost:8000/docs` to see the FastAPI Swagger UI.

## Troubleshooting

| Error | Solution |
|---|---|
| `failed to connect to the docker API` | Ensure Docker Desktop is running before executing `docker-compose`. |
| `Watsonx extraction failed` | Verify your `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` in `src/.env`. Ensure the IBM cloud region in `WATSONX_URL` matches your project. |
| Port conflicts (`5432` or `8000` or `5173`) | Stop other local PostgreSQL instances or processes using these ports, or change the mapped ports in `docker-compose.yml`. |
