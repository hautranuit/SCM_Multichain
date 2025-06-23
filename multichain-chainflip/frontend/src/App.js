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

// New Modern Components
import LandingPage from './components/LandingPage';
import ModernDashboard from './components/ModernDashboard';
import EnhancedAuthenticity from './components/EnhancedAuthenticity';
import Marketplace from './components/Marketplace';

// Main App Components
import Dashboard from './components/Dashboard';
import ProductManagement from './components/ProductManagement';
import ParticipantManagement from './components/ParticipantManagement';
import Analytics from './components/Analytics';
import TokenBridge from './components/TokenBridge';
import TransporterRegistration from './components/TransporterRegistration';
import QRScanner from './components/QRScanner';
import TransporterLocationUpdate from './components/TransporterLocationUpdate';
import BuyerProductView from './components/BuyerProductView';

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
        <div className="min-h-screen bg-gray-50">
          <Routes>
            {/* Public Landing Page */}
            <Route path="/" element={<LandingPage />} />
            
            {/* Auth Routes */}
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
                  <ModernAppLayout backendStatus={backendStatus}>
                    <ModernDashboard backendStatus={backendStatus} />
                  </ModernAppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/products" 
              element={
                <ProtectedRoute>
                  <ModernAppLayout backendStatus={backendStatus}>
                    <ProductManagement />
                  </ModernAppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/participants" 
              element={
                <ProtectedRoute>
                  <ModernAppLayout backendStatus={backendStatus}>
                    <ParticipantManagement />
                  </ModernAppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/analytics" 
              element={
                <ProtectedRoute>
                  <ModernAppLayout backendStatus={backendStatus}>
                    <Analytics />
                  </ModernAppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/token-bridge" 
              element={
                <ProtectedRoute>
                  <ModernAppLayout backendStatus={backendStatus}>
                    <TokenBridge />
                  </ModernAppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/qr-scanner" 
              element={
                <ProtectedRoute>
                  <ModernAppLayout backendStatus={backendStatus}>
                    <QRScanner />
                  </ModernAppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/enhanced-authenticity" 
              element={
                <ProtectedRoute>
                  <ModernAppLayout backendStatus={backendStatus}>
                    <EnhancedAuthenticity />
                  </ModernAppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/marketplace" 
              element={
                <ProtectedRoute>
                  <ModernAppLayout backendStatus={backendStatus}>
                    <Marketplace />
                  </ModernAppLayout>
                </ProtectedRoute>
              } 
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

// Modern App Layout Component for authenticated pages
const ModernAppLayout = ({ children, backendStatus }) => {
  const { userRole, user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const getRoleBasedMenuItems = () => {
    const baseItems = [
      { id: 'dashboard', name: 'Dashboard', icon: '📊', path: '/dashboard' },
    ];

    // Role-specific product menu item
    const productMenuItem = (() => {
      switch (userRole) {
        case 'manufacturer':
          return { id: 'products', name: 'Product Lifecycle', icon: '🏭', path: '/products' };
        case 'transporter':
          return { id: 'products', name: 'Delivery Management', icon: '🚛', path: '/products' };
        case 'buyer':
          return { id: 'products', name: 'Product Browser', icon: '🛒', path: '/products' };
        default:
          return { id: 'products', name: 'Products', icon: '📦', path: '/products' };
      }
    })();

    // Core platform features - available to all with role-specific restrictions applied in components
    const platformFeatures = [];
    
    // Enhanced Verification - Available to all roles with different purposes
    if (userRole === 'admin' || userRole === 'manufacturer') {
      platformFeatures.push({ id: 'enhanced-authenticity', name: 'Product Verification', icon: '🔐', path: '/enhanced-authenticity' });
    } else if (userRole === 'buyer') {
      platformFeatures.push({ id: 'enhanced-authenticity', name: 'Authenticity Check', icon: '🔍', path: '/enhanced-authenticity' });
    } else if (userRole === 'transporter') {
      platformFeatures.push({ id: 'enhanced-authenticity', name: 'Cargo Verification', icon: '📋', path: '/enhanced-authenticity' });
    }

    // Marketplace - Only for buyers (integrated into product lifecycle)
    if (userRole === 'buyer') {
      // Note: Marketplace is integrated into products page for buyers, not separate tab
    }

    // Common items for all roles
    const networkItems = [];
    if (userRole === 'admin') {
      networkItems.push({ id: 'participants', name: 'Admin Panel', icon: '👥', path: '/participants' });
    } else {
      networkItems.push({ id: 'participants', name: 'Network Status', icon: '🌐', path: '/participants' });
    }

    // QR Scanner with role-specific functionality
    const qrScannerItem = (() => {
      switch (userRole) {
        case 'admin':
          return { id: 'qr-scanner', name: 'IPFS Scanner', icon: '📱', path: '/qr-scanner' };
        case 'transporter':
          return { id: 'qr-scanner', name: 'Delivery Update', icon: '📱', path: '/qr-scanner' };
        case 'buyer':
          return { id: 'qr-scanner', name: 'Receipt Confirm', icon: '📱', path: '/qr-scanner' };
        default:
          return { id: 'qr-scanner', name: 'QR Scanner', icon: '📱', path: '/qr-scanner' };
      }
    })();

    // Role-specific additional features
    const roleSpecificItems = [];
    if (userRole === 'manufacturer' || userRole === 'admin') {
      roleSpecificItems.push(
        { id: 'token-bridge', name: 'Token Bridge', icon: '🌉', path: '/token-bridge' }
      );
    }

    // Analytics for all
    const analyticsItem = { id: 'analytics', name: 'Analytics', icon: '📈', path: '/analytics' };

    return [...baseItems, productMenuItem, ...platformFeatures, ...networkItems, qrScannerItem, ...roleSpecificItems, analyticsItem];
  };

  const menuItems = getRoleBasedMenuItems();

  const handleLogout = async () => {
    try {
      const authService = (await import('./services/authService')).default;
      await authService.logout();
      window.location.href = '/';
    } catch (error) {
      console.error('Logout error:', error);
      window.location.href = '/';
    }
  };

  return (
    <>
      {/* Modern Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              >
                ☰
              </button>
              <div className="flex items-center space-x-3">
                <div className="text-2xl font-bold text-blue-600">ChainFLIP</div>
                <div className="hidden md:block text-sm text-gray-500">
                  Blockchain Supply Chain Management
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="hidden md:flex items-center space-x-4 text-sm">
                <div className="flex items-center space-x-2">
                  <span className="text-gray-600">Role:</span>
                  <span className="font-semibold text-blue-600 capitalize">{userRole}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gray-600">Status:</span>
                  <span className={`font-semibold ${backendStatus.includes('✅') ? 'text-green-600' : 'text-red-600'}`}>
                    {backendStatus}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="text-sm font-medium text-gray-700">{user?.username}</div>
                <button
                  onClick={handleLogout}
                  className="text-red-600 hover:text-red-800 text-sm font-medium"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Modern Sidebar */}
        <nav className={`sidebar ${sidebarOpen ? 'open' : ''} md:block`}>
          <div className="p-6">
            <ul className="space-y-2">
              {menuItems.map((item) => (
                <li key={item.id}>
                  <button
                    onClick={() => {
                      window.location.href = item.path;
                      setSidebarOpen(false);
                    }}
                    className={`nav-item w-full text-left ${window.location.pathname === item.path ? 'active' : ''}`}
                  >
                    <span className="text-xl mr-3">{item.icon}</span>
                    {item.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </nav>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="main-content flex-1">
          {children}
        </main>
      </div>
    </>
  );
};

export default App;