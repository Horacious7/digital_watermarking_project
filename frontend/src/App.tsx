import React, { useState } from 'react';
import './App.css';
import EmbedTab from './components/EmbedTab';
import VerifyTab from './components/VerifyTab';
import { useTheme } from './hooks/useTheme';
import logoLight from './logo-light.png';
import logoDark from './logo-dark.png';
import { Toaster } from 'react-hot-toast';
import { ImagePenIcon, SearchIcon, SunIcon, MoonIcon } from './components/Icons';

function App() {
  const [activeTab, setActiveTab] = useState<'embed' | 'verify'>('embed');
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="App">
      {/* Toast Notifications Container */}
      <Toaster
        position="top-right"
        reverseOrder={false}
        toastOptions={{
          // Default options
          duration: 4000,
          style: {
            background: theme === 'dark' ? '#273469' : '#FAFAFF',
            color: theme === 'dark' ? '#FAFAFF' : '#30343F',
            border: `2px solid ${theme === 'dark' ? '#D6C6FF' : '#273469'}`,
            borderRadius: '8px',
            padding: '16px',
            fontSize: '14px',
            fontWeight: '600',
          },
          // Success
          success: {
            iconTheme: {
              primary: '#28a745',
              secondary: '#FFFAEE',
            },
          },
          // Error
          error: {
            iconTheme: {
              primary: '#dc3545',
              secondary: '#FFFAEE',
            },
          },
          // Loading
          loading: {
            iconTheme: {
              primary: theme === 'dark' ? '#D6C6FF' : '#273469',
              secondary: '#FFFAEE',
            },
          },
        }}
      />

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
              {theme === 'light' ? <MoonIcon size={20} /> : <SunIcon size={20} />}
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
            <ImagePenIcon size={18} /> Embed Watermark
          </button>
          <button
            className={`tab ${activeTab === 'verify' ? 'active' : ''}`}
            onClick={() => setActiveTab('verify')}
          >
            <SearchIcon size={18} /> Verify Watermark
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'embed' ? <EmbedTab /> : <VerifyTab />}
        </div>
      </div>

      <footer className="App-footer">
        <p>© 2025 TRACE - Digital Watermarking System | Made by Maier Horațiu-Gabriel</p>
        <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', opacity: 0.8 }}>All Rights Reserved</p>
      </footer>
    </div>
  );
}

export default App;
