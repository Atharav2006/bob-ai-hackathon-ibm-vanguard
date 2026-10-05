import React, { useState } from 'react';

const PlanningView: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<any>(null);

  const generatePlan = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/plans/generate?snapshot_id=snap_123', {
        method: 'POST'
      });
      const data = await response.json();
      setPlan(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const approvePlan = async () => {
    if (!plan) return;
    try {
      const response = await fetch(`http://localhost:8000/api/plans/${plan.id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor: 'Alex Coordinator' })
      });
      const data = await response.json();
      setPlan(data);
      alert("Plan approved and locked atomically in PostgreSQL!");
    } catch (err) {
      alert("Failed to approve plan. Double booking conflict?");
    }
  };

  return (
    <div>
      <div className="card">
        <h3>🧠 OR-Tools Optimizer</h3>
        <p>Run the CP-SAT optimization engine to match resources to needs optimally within a 5-second computation limit.</p>
        <div style={{ display: 'flex', gap: '10px' }}>
            <button className="success" onClick={generatePlan} disabled={loading}>
            {loading ? "Optimizing..." : "Generate Candidate Plan"}
            </button>
            <a 
                href="http://localhost:8000/api/export/assignments" 
                target="_blank"
                rel="noopener noreferrer"
                style={{ background: '#24a148', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '4px', cursor: 'pointer', textDecoration: 'none' }}
            >
                Download Audit CSV
            </a>
        </div>
      </div>

      {plan && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3>Candidate Plan Details</h3>
              <p>
                Status: <span className={`badge ${plan.status === 'approved' ? 'success' : ''}`}>{plan.status.toUpperCase()}</span>
                <span style={{ marginLeft: '1rem' }}>Solver: <strong>{plan.solver_status || 'OPTIMAL'}</strong></span>
              </p>
            </div>
            
            {plan.status === 'candidate' && (
              <button className="danger" onClick={approvePlan}>
                Lock & Approve Plan
              </button>
            )}
          </div>
          <hr />
          <p><em>In a full scenario, a table of assignments (Need → Resource) would be displayed here for the Coordinator's review.</em></p>
          <pre>{JSON.stringify(plan, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default PlanningView;
