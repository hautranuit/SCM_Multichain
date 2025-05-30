import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Header } from './components/Layout/Header';
import { Sidebar } from './components/Layout/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Products } from './pages/Products';
import { Participants } from './pages/Participants';
import { FederatedLearning } from './pages/FederatedLearning';
import { Analytics } from './pages/Analytics';
import { QRScanner } from './pages/QRScanner';
import { Settings } from './pages/Settings';
import { BlockchainProvider } from './contexts/BlockchainContext';
import { NotificationProvider } from './contexts/NotificationContext';

function App() {
  return (
    <BlockchainProvider>
      <NotificationProvider>
        <Router>
          <div className="min-h-screen bg-gray-50">
            <Header />
            <div className="flex">
              <Sidebar />
              <main className="flex-1 p-6 ml-64">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/products" element={<Products />} />
                  <Route path="/participants" element={<Participants />} />
                  <Route path="/federated-learning" element={<FederatedLearning />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/qr-scanner" element={<QRScanner />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </main>
            </div>
          </div>
        </Router>
      </NotificationProvider>
    </BlockchainProvider>
  );
}

export default App;
