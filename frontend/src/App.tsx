import React, { useState } from 'react';
import './App.css';
import EmbedTab from './components/EmbedTab';
import VerifyTab from './components/VerifyTab';
import { useTheme } from './hooks/useTheme';
import logoLight from './logo-light.png';
import logoDark from './logo-dark.png';

function App() {
  const [activeTab, setActiveTab] = useState<'embed' | 'verify'>('embed');
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="logo-container">
            <img
              src={theme === 'light' ? logoLight : logoDark}
              alt="TRACE Logo"
              className="app-logo"
            />
          </div>

          <div className="header-center">
            <h1>TRACE</h1>
            <p className="subtitle"><em>Secure Your Pixels</em></p>
          </div>

          <div className="theme-toggle-container">
            <button
              onClick={toggleTheme}
              className="theme-toggle-btn"
              title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
          </div>
        </div>
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
