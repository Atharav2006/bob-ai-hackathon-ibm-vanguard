import React, { useState, useEffect } from 'react';
import './App.css';
import ReportForm from './components/ReportForm';
import PlanningView from './components/PlanningView';
import { SituationMap } from './components/SituationMap';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'situation' | 'reports' | 'planning'>('planning');

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/api/ws');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === "new_sms_report") {
        alert(`🚨 LIVE ALERT: New Emergency SMS Received!\nFrom: ${data.from}\nMessage: "${data.body}"\n\nIBM Watsonx has already parsed this report and updated the database.`);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div>
      <header className="app-header">
        <h2>🚀 Autonomous Disaster Response Planner</h2>
        <div>Coordinator Mode</div>
      </header>

      <nav className="nav-tabs">
        <button 
          className={`nav-tab ${activeTab === 'situation' ? 'active' : ''}`}
          onClick={() => setActiveTab('situation')}
        >
          Situation Map
        </button>
        <button 
          className={`nav-tab ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          Field Reports (Watsonx)
        </button>
        <button 
          className={`nav-tab ${activeTab === 'planning' ? 'active' : ''}`}
          onClick={() => setActiveTab('planning')}
        >
          Planning & Approval (OR-Tools)
        </button>
      </nav>

      <main className="container">
        {activeTab === 'situation' && (
          <div className="card">
            <h3>Live Situation Overview</h3>
            <p>Real-time view of PostGIS emergency zones and available response units.</p>
            <SituationMap />
          </div>
        )}

        {activeTab === 'reports' && <ReportForm />}
        {activeTab === 'planning' && <PlanningView />}
      </main>
    </div>
  );
};

export default App;
