# 🚀 Autonomous Disaster Response Planner

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | IBM Vanguard |
| **Track** | AI |
| **Team Lead** | Alex Coordinator — alex@example.com |
| **Members** | Sam Responder, Taylor Logistics |

---

## 🎯 Problem Statement

Disaster coordinators must distribute scarce teams, medical support, vehicles, and supplies across affected zones while information changes rapidly in the first 72 hours. Current solutions result in scattered reports and opaque decisions, causing delayed response times.

---

## 💡 Solution

A web application that ingests unstructured field reports using watsonx.ai to generate structured needs, and uses OR-Tools to propose optimal resource allocations. An integrated IBM Bob assistant allows coordinators to intuitively interrogate plans and execute approvals conversationally.

---

## ✨ Key Features

- **Feature 1:** Unstructured report parsing into structured Needs using watsonx.ai Granite
- **Feature 2:** Conversational plan interrogation and approval via IBM Bob MCP Server
- **Feature 3:** Deterministic baseline vs. CP-SAT optimized resource allocation
- **Feature 4:** Dynamic replanning triggered by network graph closure events
- **Feature 5:** Atomic transactional approval workflow preventing double-bookings

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python, TypeScript |
| **Frameworks** | FastAPI, React, Vite |
| **IBM Technologies** | watsonx.ai Granite 3.0, IBM Bob |
| **Databases** | PostgreSQL, PostGIS |
| **Other** | OR-Tools, NetworkX, Leaflet, Docker, GitHub Actions |

---

## 📁 Repository Structure

```
├── src/                  # All source code
├── docs/                 # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                 # Demo artifacts
│   ├── screenshots/      # App screenshots
│   └── demo-video-link.txt  # Link to demo video
├── presentation/         # Slide deck
└── submission.yaml       # Structured submission metadata
```

---

## ⚡ How to Run

> **Copy these exact steps from your [`docs/setup-guide.md`](docs/setup-guide.md)**

```bash
# 1. Clone the repo
git clone https://github.com/drijesh-ppatel/bob-ai-hackathon-submission-template.git
cd Disaster_Response_Project

# 2. Install dependencies (Using Docker Compose for all services)
cd src
docker-compose build

# 3. Configure environment
cp .env.example .env
# Edit .env with your watsonx.ai API key if needed

# 4. Run the project
docker-compose up -d
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |

---

## ⚠️ Known Limitations

- Multi-stop vehicle routing is not yet supported; single-destination task bundles are used.
- The map relies on simulated seeded graph data rather than a live external GIS feed.
- Currently does not support offline PWA synchronization for field clients.

---

## 🏅 What We're Most Proud Of

The tight integration of IBM Bob. Instead of a simple chatbot, Bob is deeply integrated via MCP to read the live PostgreSQL incident state, interrogate the CP-SAT solver outputs, and execute atomic plan approvals on behalf of the coordinator.

---
