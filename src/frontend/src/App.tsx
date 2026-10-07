import React, { useState, useEffect } from "react";
import "./App.css";
import ReportForm from "./components/ReportForm";
import PlanningView from "./components/PlanningView";
import { SituationMap } from "./components/SituationMap";
import { useAuth } from "./AuthContext";
import Login from "./components/Login";
import IncidentSelect from "./components/IncidentSelect";

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"situation" | "reports" | "planning">("planning");
  const { token, incidentId, logout } = useAuth();

  useEffect(() => {
    if (!token || !incidentId) return;
    const ws = new WebSocket("ws://localhost:8001/api/ws");
    
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "authenticate", token, incident_id: incidentId }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === "new_sms_report") {
        const lang = data.ai_analysis?.original_language || "Unknown";
        const trans = data.ai_analysis?.english_translation || data.body;
        const sent = data.ai_analysis?.sentiment || "Unknown";
        alert(`LIVE ALERT: New Emergency SMS Received!\nFrom: ${data.from}\nLanguage: ${lang.toUpperCase()}\nRaw Text: "${data.body}"\n\nAI Translation: "${trans}"\nSentiment: ${sent}`);
      }
    };
    return () => ws.close();
  }, [token, incidentId]);

  if (!token) return <Login />;
  if (!incidentId) return (
    <div>
      <div style={{ padding: "1rem", display: "flex", justifyContent: "space-between" }}>
        <span>Logged in</span>
        <button onClick={logout}>Logout</button>
      </div>
      <IncidentSelect />
    </div>
  );

  return (
    <div>
      <header className="app-header">
        <h2>Autonomous Disaster Response Planner</h2>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <span>Coordinator Mode</span>
          <button onClick={logout} style={{ fontSize: "0.8rem", padding: "0.25rem 0.5rem" }}>Logout</button>
        </div>
      </header>

      <nav className="nav-tabs">
        <button 
          className={`nav-tab ${activeTab === "situation" ? "active" : ""}`}
          onClick={() => setActiveTab("situation")}
        >
          Situation Map
        </button>
        <button 
          className={`nav-tab ${activeTab === "reports" ? "active" : ""}`}
          onClick={() => setActiveTab("reports")}
        >
          Field Reports
        </button>
        <button 
          className={`nav-tab ${activeTab === "planning" ? "active" : ""}`}
          onClick={() => setActiveTab("planning")}
        >
          Planning & Approval
        </button>
      </nav>

      <main className="container">
        {activeTab === "situation" && (
          <div className="card">
            <h3>Live Situation Overview</h3>
            <p>Real-time view of PostGIS emergency zones and available response units.</p>
            <SituationMap />
          </div>
        )}

        {activeTab === "reports" && <ReportForm />}
        {activeTab === "planning" && <PlanningView />}
      </main>
    </div>
  );
};

export default App;

