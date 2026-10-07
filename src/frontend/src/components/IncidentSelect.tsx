import React, { useEffect, useState } from "react";
import { useAuth } from "../AuthContext";

const IncidentSelect: React.FC = () => {
  const { token, selectIncident } = useAuth();
  const [incidents, setIncidents] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://localhost:8001/api/incidents/", {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setIncidents)
      .catch(console.error);
  }, [token]);

  return (
    <div className="card" style={{ maxWidth: 600, margin: "2rem auto", padding: "2rem" }}>
      <h2>Select Incident</h2>
      <p>Choose an operational or simulation incident to manage.</p>
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {incidents.map(inc => (
          <button key={inc.id} onClick={() => selectIncident(inc.id)} style={{ padding: "1rem", textAlign: "left" }}>
            <strong>{inc.name}</strong> - <em>{inc.mode}</em> (Rev: {inc.revision})
          </button>
        ))}
        {incidents.length === 0 && <p>No incidents available. Ensure the database is seeded.</p>}
      </div>
    </div>
  );
};

export default IncidentSelect;

