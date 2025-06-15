import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Auth Components
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginForm from './components/Auth/LoginForm';
import RegisterForm from './components/Auth/RegisterForm';
import AdminDashboard from './components/Auth/AdminDashboard';
import ProtectedRoute from './components/Auth/ProtectedRoute';

// Main App Components
import Dashboard from './components/Dashboard';
import ProductManagement from './components/ProductManagement';
import ParticipantManagement from './components/ParticipantManagement';
import EnhancedConsensusDemo from './components/EnhancedConsensusDemo';
import Analytics from './components/Analytics';
import ConsensusManagement from './components/ConsensusManagement';
import TokenBridge from './components/TokenBridge';
import TransporterRegistration from './components/TransporterRegistration';

// Auth Pages
const LoginPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (credentials) => {
    setIsLoading(true);
    setError('');
    
    try {
      const authService = (await import('./services/authService')).default;
      await authService.login(credentials);
      window.location.href = '/dashboard';
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      {error && (
        <div className="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50">
          {error}
        </div>
      )}
      <LoginForm onLogin={handleLogin} isLoading={isLoading} />
    </div>
  );
};

const RegisterPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleRegister = async (userData) => {
    setIsLoading(true);
    setError('');
    setSuccess('');
    
    try {
      // If registering as transporter, show the transporter registration form
      if (userData.role === 'transporter') {
        // Redirect to transporter registration with pre-filled data
        sessionStorage.setItem('transporterRegistrationData', JSON.stringify(userData));
        window.location.href = '/transporter-registration';
        return;
      }

      const authService = (await import('./services/authService')).default;
      await authService.register(userData);
      setSuccess('Registration successful! Please wait for admin approval. You will receive an email once approved.');
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        window.location.href = '/login';
      }, 3000);
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      {error && (
        <div className="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50">
          {error}
        </div>
      )}
      {success && (
        <div className="fixed top-4 right-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded z-50 max-w-md">
          {success}
        </div>
      )}
      <RegisterForm onRegister={handleRegister} isLoading={isLoading} />
    </div>
  );
};

const AdminPage = () => {
  const authService = require('./services/authService').default;
  return (
    <ProtectedRoute requireAdmin={true}>
      <AdminDashboard authService={authService} />
    </ProtectedRoute>
  );
};

function App() {
  const [backendStatus, setBackendStatus] = useState('checking...');

  useEffect(() => {
    checkBackendConnection();
  }, []);

  const checkBackendConnection = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/health`);
      setBackendStatus('✅ Connected');
    } catch (error) {
      setBackendStatus('❌ Not Connected');
      console.error('Backend connection error:', error);
    }
  };

  return (
    <AuthProvider>
      <Router>
        <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Special route for transporter registration (part of signup flow) */}
            <Route path="/transporter-registration" element={<TransporterRegistration />} />
            
            {/* Protected Admin Routes */}
            <Route path="/admin" element={<AdminPage />} />
            
            {/* Protected App Routes */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <AppLayout backendStatus={backendStatus}>
                    <Dashboard backendStatus={backendStatus} />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/products" 
              element={
                <ProtectedRoute>
                  <AppLayout backendStatus={backendStatus}>
                    <ProductManagement />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/participants" 
              element={
                <ProtectedRoute>
                  <AppLayout backendStatus={backendStatus}>
                    <ParticipantManagement />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/enhanced-consensus" 
              element={
                <ProtectedRoute>
                  <AppLayout backendStatus={backendStatus}>
                    <EnhancedConsensusDemo />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/analytics" 
              element={
                <ProtectedRoute>
                  <AppLayout backendStatus={backendStatus}>
                    <Analytics />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/consensus" 
              element={
                <ProtectedRoute>
                  <AppLayout backendStatus={backendStatus}>
                    <ConsensusManagement />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/token-bridge" 
              element={
                <ProtectedRoute>
                  <AppLayout backendStatus={backendStatus}>
                    <TokenBridge />
                  </AppLayout>
                </ProtectedRoute>
              } 
            />
            
            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

// App Layout Component for authenticated pages
const AppLayout = ({ children, backendStatus }) => {
  const { userRole } = useAuth();
  
  const getRoleBasedMenuItems = () => {
    const baseItems = [
      { id: 'dashboard', name: 'Dashboard', icon: '📊', path: '/dashboard' },
    ];

    // Role-specific product menu item
    const productMenuItem = (() => {
      switch (userRole) {
        case 'manufacturer':
          return { id: 'products', name: 'Create Product NFT', icon: '📦', path: '/products' };
        case 'transporter':
          return { id: 'products', name: 'Shipping Process', icon: '🚛', path: '/products' };
        case 'buyer':
          return { id: 'products', name: 'Market', icon: '🛒', path: '/products' };
        default:
          return { id: 'products', name: 'Products', icon: '📦', path: '/products' };
      }
    })();

    // Role-specific menu items
    const roleSpecificItems = [];
    
    // Common items for all roles
    const commonItems = [
      { id: 'participants', name: 'Participants', icon: '👥', path: '/participants' },
      { id: 'enhanced-consensus', name: 'Enhanced Consensus', icon: '📱', path: '/enhanced-consensus' },
    ];

    // Role-specific additional items - SUPPLY CHAIN FUNCTIONALITY INTEGRATED INTO PRODUCTS
    if (userRole === 'manufacturer') {
      roleSpecificItems.push(
        { id: 'token-bridge', name: 'Token Bridge', icon: '🌉', path: '/token-bridge' }
      );
    } else if (userRole === 'buyer') {
      // Buyer gets integrated supply chain in products tab
    } else if (userRole === 'transporter') {
      // Transporter gets integrated supply chain in products tab
    } else {
      // Admin or default - show all including consensus
      roleSpecificItems.push(
        { id: 'token-bridge', name: 'Token Bridge', icon: '🌉', path: '/token-bridge' },
        { id: 'consensus', name: 'Consensus System', icon: '⚡', path: '/consensus' }
      );
    }

    // Analytics - role-specific
    const analyticsItem = { id: 'analytics', name: 'Analytics', icon: '📈', path: '/analytics' };

    return [...baseItems, productMenuItem, ...commonItems, ...roleSpecificItems, analyticsItem];
  };

  const menuItems = getRoleBasedMenuItems();

  const handleLogout = async () => {
    try {
      const authService = (await import('./services/authService')).default;
      await authService.logout();
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
      window.location.href = '/login';
    }
  };

  return (
    <>
      <header style={{ background: 'white', borderBottom: '1px solid #e5e7eb', padding: '1rem 0' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <h1 style={{ margin: 0, color: '#1e40af', fontSize: '2rem', fontWeight: 'bold' }}>
                🔗 ChainFLIP
              </h1>
              <span style={{ marginLeft: '1rem', color: '#6b7280', fontSize: '0.875rem' }}>
                Multi-Chain Supply Chain Management
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ fontSize: '0.875rem' }}>
                Role: <span className="font-medium text-blue-600 capitalize">{userRole}</span>
              </div>
              <div style={{ fontSize: '0.875rem' }}>
                Backend: <span className={backendStatus.includes('✅') ? 'text-green' : 'text-red'}>
                  {backendStatus}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="text-red-600 hover:text-red-800 text-sm font-medium"
              >
                Sign Out
              </button>
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
                  onClick={() => window.location.href = item.path}
                  className={window.location.pathname === item.path ? 'nav-item active' : 'nav-item'}
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
          <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
            {children}
          </div>
        </main>
      </div>
    </>
  );
};

export default App;