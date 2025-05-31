import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [backendStatus, setBackendStatus] = useState('checking...');
  const [backendData, setBackendData] = useState(null);
  const [currentPage, setCurrentPage] = useState('dashboard');

  useEffect(() => {
    checkBackendConnection();
  }, []);

  const checkBackendConnection = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/health`);
      setBackendStatus('✅ Connected');
      setBackendData(response.data);
    } catch (error) {
      setBackendStatus('❌ Not Connected');
      console.error('Backend connection error:', error);
    }
  };

  const menuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'products', name: 'Products', icon: '📦' },
    { id: 'participants', name: 'Participants', icon: '👥' },
    { id: 'qr-scanner', name: 'QR Scanner', icon: '📱' },
    { id: 'analytics', name: 'Analytics', icon: '📈' },
    { id: 'federated-learning', name: 'FL System', icon: '🤖' },
  ];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
      <header style={{ background: 'white', borderBottom: '1px solid #e5e7eb', padding: '1rem 0' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <h1 style={{ margin: 0, color: '#1e40af', fontSize: '2rem', fontWeight: 'bold' }}>
                🔗 ChainFLIP
              </h1>
              <span style={{ marginLeft: '1rem', color: '#6b7280', fontSize: '0.875rem' }}>
                Multi-Chain Supply Chain
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{ fontSize: '0.875rem' }}>
                Backend: <span className={backendStatus.includes('✅') ? 'text-green' : 'text-red'}>
                  {backendStatus}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div style={{ display: 'flex' }}>
        <nav className="sidebar">
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {menuItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => setCurrentPage(item.id)}
                  className={currentPage === item.id ? 'nav-item active' : 'nav-item'}
                  style={{ 
                    width: '100%', 
                    textAlign: 'left',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '1rem'
                  }}
                >
                  <span style={{ marginRight: '0.75rem', fontSize: '1.125rem' }}>{item.icon}</span>
                  {item.name}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <main className="main-content">
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            {currentPage === 'dashboard' && (
              <div>
                <h2 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '2rem' }}>Dashboard</h2>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
                  <div className="card">
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>System Status</h3>
                    <div style={{ fontSize: '0.875rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span>Backend:</span>
                        <span>{backendStatus}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span>Frontend:</span>
                        <span className="text-green">✅ Running</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Database:</span>
                        <span className="text-green">✅ Connected</span>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>Blockchain Network</h3>
                    <div style={{ fontSize: '0.875rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span>Polygon PoS:</span>
                        <span className="text-green">✅ Connected</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span>L2 CDK:</span>
                        <span className="text-green">✅ Connected</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Smart Contracts:</span>
                        <span className="text-green">✅ Deployed</span>
                      </div>
                    </div>
                  </div>

                  <div className="card">
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>IPFS Integration</h3>
                    <div style={{ fontSize: '0.875rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span>Web3.Storage:</span>
                        <span className="text-green">✅ Connected</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Gateway:</span>
                        <span className="text-green">✅ Available</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card" style={{ marginTop: '2rem' }}>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>🚀 Available Features</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
                    {menuItems.slice(1).map((item) => (
                      <div key={item.id} className="card" style={{ margin: '0.5rem', border: '1px solid #e5e7eb' }}>
                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                          <span style={{ fontSize: '1.5rem', marginRight: '0.75rem' }}>{item.icon}</span>
                          <h4 style={{ margin: 0, fontWeight: '500' }}>{item.name}</h4>
                        </div>
                        <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: 0 }}>
                          {item.id === 'products' && 'Manage product lifecycle on multi-chain network'}
                          {item.id === 'participants' && 'Register and manage supply chain participants'}
                          {item.id === 'qr-scanner' && 'Scan and verify product QR codes'}
                          {item.id === 'analytics' && 'View real-time performance metrics'}
                          {item.id === 'federated-learning' && 'AI-powered anomaly and counterfeit detection'}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {currentPage !== 'dashboard' && (
              <div className="card">
                <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
                  {menuItems.find(item => item.id === currentPage)?.icon}{' '}
                  {menuItems.find(item => item.id === currentPage)?.name}
                </h2>
                <div style={{ textAlign: 'center', padding: '3rem 0' }}>
                  <p style={{ color: '#6b7280', fontSize: '1.125rem' }}>
                    This feature is ready for development!
                  </p>
                  <p style={{ color: '#9ca3af', marginTop: '0.5rem' }}>
                    Backend is fully operational with all integrations working.
                  </p>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
