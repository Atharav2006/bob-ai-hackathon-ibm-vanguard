---
theme: default
---

# Autonomous Disaster Response Planner
### Team: IBM Vanguard
**Track:** Open Innovation / AI

An AI-powered incident management system utilizing **IBM watsonx** and **Google OR-Tools** to optimize disaster resource allocation.

---

# 1. The Problem
**Chaos in Crises:** During natural disasters, information flows in raw, unstructured formats (radio transcripts, frantic texts, social media).

**Inefficient Deployment:** Dispatchers struggle to parse requests manually, leading to overlapping assignments or unfulfilled critical needs.

**Why it matters:** In emergency response, seconds lost in logistics cost lives.

---

# 2. Our Solution
**Intelligent Ingestion:** Uses IBM watsonx.ai Granite 3.0 to automatically extract structured data (urgency, location, need type) from messy field reports.

**Mathematical Optimization:** Employs a Constraint Programming solver (OR-Tools) to mathematically guarantee the optimal deployment of ambulances, trucks, and rescue boats.

**Concurrency Control:** Utilizes PostgreSQL row-level locking to ensure atomic dispatches, preventing double-booking even under massive load.

---

# 3. Architecture
- **Frontend:** React + Vite (TypeScript) for the interactive dispatcher dashboard.
- **Backend:** Python FastAPI for high-performance API routing.
- **AI Engine:** `ibm-watson-machine-learning` SDK hooked to Granite 3.0 models.
- **Optimizer:** Google OR-Tools `CP-SAT` Solver.
- **Database:** PostgreSQL with PostGIS for geospatial zone routing.
- **Orchestration:** Docker Compose.

---

# 4. Key IBM Technology Used
**IBM watsonx.ai:** Leveraged the `ibm-watson-machine-learning` SDK to parse raw incoming field reports.

By prompting the **Granite 3.0** model, we bridged the gap between unstructured emergency chatter and strictly typed database records (`Needs`).

---

# 5. Results & Impact
**Speed:** Reduces dispatcher cognitive load and time-to-deployment from minutes to milliseconds.

**Efficiency:** The OR-Tools allocator prevents dispatching a small rescue boat to a massive flood zone if a heavy boat is available.

**Scalability:** Dockerized and ready to deploy to IBM Cloud or AWS.
