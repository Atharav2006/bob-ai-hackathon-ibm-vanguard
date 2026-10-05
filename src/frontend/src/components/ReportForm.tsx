import React, { useState } from 'react';

const ReportForm: React.FC = () => {
  const [reportText, setReportText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);
    try {
      // Calling our FastAPI backend
      const response = await fetch('http://localhost:8000/api/reports/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: "Field Agent UI",
          observed_at: new Date().toISOString(),
          raw_text: reportText
        })
      });
      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setResult({ error: "Failed to submit report" });
    } finally {
      setLoading(false);
    }
  };

  const [listening, setListening] = useState(false);
  
  const handleDictate = () => {
    // @ts-ignore
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support Speech Recognition.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onstart = () => setListening(true);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setReportText((prev) => prev + (prev ? " " : "") + transcript);
    };
    recognition.onend = () => setListening(false);
    recognition.start();
  };

  return (
    <div className="card">
      <h3>📥 Submit Field Report</h3>
      <p>Enter unstructured intelligence from the field. <strong>watsonx.ai Granite</strong> will structure it automatically.</p>
      
      <textarea 
        rows={4}
        value={reportText}
        onChange={e => setReportText(e.target.value)}
        placeholder="e.g., We have a flooded bridge on Route 9 and need 5 medical kits urgently."
      />
      
      <div style={{ display: 'flex', gap: '10px' }}>
        <button onClick={handleDictate} disabled={listening} style={{ background: '#f1c21b', color: 'black' }}>
          {listening ? "🔴 Listening..." : "🎤 Dictate with Voice"}
        </button>
        <button onClick={handleSubmit} disabled={loading || listening}>
          {loading ? "Extracting..." : "Submit to Watsonx.ai"}
        </button>
      </div>

      {result && (
        <div style={{ marginTop: '2rem', background: '#f8f9fa', padding: '1rem', border: '1px solid #ddd' }}>
          <h4>Structured Result</h4>
          <pre>{JSON.stringify(result.structured_data || result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default ReportForm;
