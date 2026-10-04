# Solution Overview

## Core Mechanism

The Autonomous Disaster Response Planner is a web application designed for the first 72 hours of an emergency. It operates on two main AI-driven mechanisms:
1. **Intelligence Structuring:** Unstructured field reports are ingested via FastAPI and processed by **watsonx.ai Granite 3.0** to extract structured `Needs` (category, quantity, urgency).
2. **Resource Optimization:** An **OR-Tools CP-SAT** planner engine computes constrained allocations (task bundles) matching available teams/vehicles to the most urgent needs, strictly respecting real-time graph connectivity (e.g., bridge closures).

## What Makes It Different

Unlike naive "first-come-first-served" dispatch systems, our solution employs constraint programming to mathematically prove that no resource is double-booked and that routes are actually feasible based on the latest access updates. It features **IBM Bob** integrated via MCP to allow coordinators to interrogate the mathematical constraints conversationally before atomic transaction approval.

## Key Design Decisions

- **Deterministic Fallback vs. Optimization:** We maintain a baseline allocator alongside the CP-SAT engine to ensure the system can always produce a viable plan within a 5-second computation limit, even if complex constraints fail.
- **Strict Data Provenance:** Every report retains its raw text and structured derivation. Plans are immutable snapshots; approvals are atomic transactional locks in PostgreSQL to prevent double-booking.
- **Load-bearing AI:** We did not just add a chatbot. IBM Bob is given MCP access to the PostgreSQL incident state, acting as a true copilot for the coordinator's operational decisions.

## User Experience

- **Coordinators** see a Situation Overview map (Leaflet) highlighting zones by urgency. They can prompt IBM Bob to explain the latest CP-SAT plan and approve it.
- **Field Responders** use a mobile-optimized form to submit brief reports which are instantly converted to structured demand.
