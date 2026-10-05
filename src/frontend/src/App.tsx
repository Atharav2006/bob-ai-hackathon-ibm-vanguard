import React, { useState } from 'react';
import './App.css';
import ReportForm from './components/ReportForm';
import PlanningView from './components/PlanningView';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'situation' | 'reports' | 'planning'>('planning');

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
            <h3>Situation Overview</h3>
            <p>Map component will render here...</p>
            <div style={{ height: '400px', background: '#e0e0e0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              Leaflet Map Placeholder
            </div>
          </div>
        )}

        {activeTab === 'reports' && <ReportForm />}
        {activeTab === 'planning' && <PlanningView />}
      </main>
    </div>
  );
};

export default App;
