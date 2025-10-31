import React, { useState } from 'react';
import './App.css';
import EmbedTab from './components/EmbedTab';
import VerifyTab from './components/VerifyTab';

function App() {
  const [activeTab, setActiveTab] = useState<'embed' | 'verify'>('embed');

  return (
    <div className="App">
      <header className="App-header">
        <h1>🖼️ Digital Watermarking for Historical Photos</h1>
        <p className="subtitle">Secure authentication with cryptographic signatures</p>
      </header>

      <div className="tab-container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'embed' ? 'active' : ''}`}
            onClick={() => setActiveTab('embed')}
          >
            📝 Embed Watermark
          </button>
          <button
            className={`tab ${activeTab === 'verify' ? 'active' : ''}`}
            onClick={() => setActiveTab('verify')}
          >
            🔍 Verify Watermark
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'embed' ? <EmbedTab /> : <VerifyTab />}
        </div>
      </div>

      <footer className="App-footer">
        <p>Digital Watermarking System with RSA Signatures</p>
      </footer>
    </div>
  );
}

export default App;
