import React, { useEffect, useState } from 'react';

const App: React.FC = () => {
  const [health, setHealth] = useState<string>("Checking API...");

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then(res => res.json())
      .then(data => setHealth(data.message))
      .catch(err => setHealth('API Error: ' + err.message));
  }, []);

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>🚀 Autonomous Disaster Response Planner</h1>
      <p><strong>Backend Status:</strong> {health}</p>
      
      <div style={{ marginTop: '2rem', display: 'flex', gap: '2rem' }}>
        <div style={{ flex: 1, border: '1px solid #ccc', padding: '1rem' }}>
          <h2>📥 Submit Field Report</h2>
          <textarea 
            placeholder="e.g., We have a flooded bridge on Route 9 and need 5 medical kits urgently."
            style={{ width: '100%', height: '100px', marginBottom: '1rem' }}
          ></textarea>
          <button style={{ background: '#18354A', color: 'white', padding: '0.5rem 1rem' }}>
            Submit to Watsonx.ai
          </button>
        </div>
        
        <div style={{ flex: 1, border: '1px solid #ccc', padding: '1rem' }}>
          <h2>🧠 Planner & Watsonx AI</h2>
          <p>
            The backend is integrated with <strong>watsonx.ai Granite</strong> for report extraction 
            and <strong>OR-Tools CP-SAT</strong> for resource allocation.
          </p>
          <button style={{ background: '#176B54', color: 'white', padding: '0.5rem 1rem' }}>
            Run Optimization (OR-Tools)
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;
