import React, { useState, useEffect } from "react";
import { useAuth } from "../AuthContext";

const ReportForm: React.FC = () => {
  const { token, incidentId } = useAuth();
  const [reportText, setReportText] = useState("");
  const [loading, setLoading] = useState(false);
  const [reports, setReports] = useState<any[]>([]);

  const fetchReports = async () => {
    try {
      const res = await fetch("http://localhost:8001/api/reports/", {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Incident-ID": incidentId
        }
      });
      const data = await res.json();
      setReports(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [incidentId, token]);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await fetch("http://localhost:8001/api/reports/", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-Incident-ID": incidentId
        },
        body: JSON.stringify({
          source: "Field Agent UI",
          observed_at: new Date().toISOString(),
          raw_text: reportText
        })
      });
      setReportText("");
      fetchReports();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (id: string, action: string, updates: any = {}) => {
    try {
      await fetch(`http://localhost:8001/api/reports/${id}/review`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-Incident-ID": incidentId
        },
        body: JSON.stringify({ action, ...updates })
      });
      fetchReports();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div className="card">
        <h3>Submit Field Report</h3>
        <textarea 
          rows={4}
          value={reportText}
          onChange={e => setReportText(e.target.value)}
          placeholder="e.g., Flooded bridge on Route 9, need 5 medical kits."
          style={{ width: "100%", padding: "0.5rem" }}
        />
        <button onClick={handleSubmit} disabled={loading} style={{ marginTop: "1rem" }}>
          {loading ? "Extracting..." : "Submit to AI"}
        </button>
      </div>
      
      <div className="card" style={{ marginTop: "1rem" }}>
        <h3>Report Inbox (Needs Review)</h3>
        {reports.filter(r => r.status === "needs_review").map(r => (
          <div key={r.id} style={{ borderBottom: "1px solid #ccc", padding: "1rem 0" }}>
            <p><strong>Raw:</strong> {r.raw_text}</p>
            <pre style={{ fontSize: "0.8rem", background: "#eee", padding: "0.5rem" }}>
              {JSON.stringify(r.structured_data, null, 2)}
            </pre>
            <div style={{ display: "flex", gap: "1rem" }}>
              <button onClick={() => handleReview(r.id, "approve", { 
                need_category: r.structured_data?.category || "rescue",
                need_amount: r.structured_data?.amount || 1,
                need_urgency: r.structured_data?.urgency || 5
              })}>Approve as Need</button>
              <button onClick={() => handleReview(r.id, "reject")} style={{ background: "#dc3545" }}>Reject</button>
            </div>
          </div>
        ))}
        {reports.filter(r => r.status === "needs_review").length === 0 && <p>No pending reports.</p>}
      </div>
      
      <div className="card" style={{ marginTop: "1rem" }}>
        <h3>Approved Reports</h3>
        {reports.filter(r => r.status === "reviewed").map(r => (
          <div key={r.id} style={{ borderBottom: "1px solid #eee", padding: "0.5rem 0" }}>
            <span style={{ color: "green" }}>✓ Approved:</span> {r.raw_text}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ReportForm;

