import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const ParticipantManagement = () => {
  const { userRole, user } = useAuth();

  // Real participants data from database - hardcoded for demo purposes
  const [participants, setParticipants] = useState([
    {
      _id: '685e7b167cb831390cdc035a',
      address: '0x90F79bf6EB2c4f870365E785982E1f101E93b906',
      name: 'Alice Smith (Manufacturer)',
      company: 'Alice Smith Manufacturing',
      role: 'manufacturer',
      participant_type: 'manufacturer',
      email: 'manufacturer1@chainflip.com',
      phone: '+1-555-0101',
      location: 'Detroit, MI',
      description: 'Leading automotive parts manufacturer',
      chain_id: 84532,
      status: 'active',
      created_at: '2024-12-25T04:38:30.736Z'
    },
    {
      _id: '685e7b2a7cb831390cdc035b',
      address: '0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65',
      name: 'Bob Johnson (Manufacturer)',
      company: 'Bob Johnson Manufacturing',
      role: 'manufacturer',
      participant_type: 'manufacturer',
      email: 'manufacturer2@chainflip.com',
      phone: '+1-555-0102',
      location: 'Chicago, IL',
      description: 'Advanced electronics manufacturer',
      chain_id: 84532,
      status: 'active',
      created_at: '2024-12-25T04:38:50.509Z'
    },
    {
      _id: '685e7b3c7cb831390cdc035c',
      address: '0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc',
      name: 'Carol Brown (Manufacturer)',
      company: 'Carol Brown Manufacturing',
      role: 'manufacturer',
      participant_type: 'manufacturer',
      email: 'manufacturer3@chainflip.com',
      phone: '+1-555-0103',
      location: 'New York, NY',
      description: 'Sustainable goods manufacturer',
      chain_id: 84532,
      status: 'active',
      created_at: '2024-12-25T04:39:08.582Z'
    },
    {
      _id: '685e7b4f7cb831390cdc035d',
      address: '0x976EA74026E726554dB657fA54763abd0C3a0aa9',
      name: 'David Wilson (Transporter)',
      company: 'David Wilson Logistics',
      role: 'transporter',
      participant_type: 'transporter',
      email: 'transporter1@chainflip.com',
      phone: '+1-555-0104',
      location: 'Los Angeles, CA',
      description: 'Cross-chain shipping and logistics',
      chain_id: 421614,
      status: 'active',
      created_at: '2024-12-25T04:39:27.705Z'
    },
    {
      _id: '685e7b617cb831390cdc035e',
      address: '0x14dC79964da2C08b23698B3D3cc7Ca32193d9955',
      name: 'Eve Davis (Buyer)',
      company: 'Eve Davis Retail',
      role: 'buyer',
      participant_type: 'buyer',
      email: 'buyer1@chainflip.com',
      phone: '+1-555-0105',
      location: 'Miami, FL',
      description: 'Major retail procurement',
      chain_id: 11155420,
      status: 'active',
      created_at: '2024-12-25T04:39:45.984Z'
    }
  ]);
  
  // Real pending users data from database - hardcoded for demo purposes
  const [pendingUsers, setPendingUsers] = useState([
    {
      _id: '685e7b0c7cb831390cdc0359',
      username: 'Test Transporter',
      name: 'Test Transporter',
      email: 'test-transporter@chainflip.com',
      role: 'transporter',
      participant_type: 'transporter',
      company: 'Test Transporter Co',
      wallet_address: '0x7ca2dF29b5ea3BB9Ef3b4245D8b7c41a03318Fc1',
      address: '0x7ca2dF29b5ea3BB9Ef3b4245D8b7c41a03318Fc1',
      phone: '+1-555-0106',
      location: 'Seattle, WA',
      description: 'Express logistics services',
      chain_id: 421614,
      created_at: '2024-12-25T04:37:48.469Z'
    }
  ]);
  
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedParticipant, setSelectedParticipant] = useState(null);
  const [activeTab, setActiveTab] = useState('participants');
  const [notification, setNotification] = useState(null);
  const [recentlyApproved, setRecentlyApproved] = useState(new Set());
  
  // Dynamic stats based on current state
  const stats = {
    totalParticipants: participants.length,
    pendingApprovals: pendingUsers.length,
    activeUsers: participants.length + 1, // +1 for admin
    totalTransactions: 8542
  };

  const [newParticipant, setNewParticipant] = useState({
    address: '',
    name: '',
    company: '',
    role: '',
    participantType: '',
    email: '',
    phone: '',
    location: '',
    description: '',
    chainId: '80002'
  });

  // Simulate data loading for demo purposes
  const fetchData = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 500);
  };

  // Mock functions for demo purposes
  const fetchParticipants = () => {
    // Data is already hardcoded above
    console.log('Participants data loaded (hardcoded for demo)');
  };

  const fetchPendingUsers = () => {
    // Data is already hardcoded above
    console.log('Pending users data loaded (hardcoded for demo)');
  };

  const fetchNetworkStats = () => {
    // Stats are already hardcoded above
    console.log('Network stats loaded (hardcoded for demo)');
  };

  const approveUser = (userId) => {
    setLoading(true);
    
    // Find the user to approve
    const userToApprove = pendingUsers.find(user => user._id === userId);
    
    if (userToApprove) {
      setTimeout(() => {
        // Convert pending user to participant format
        const newParticipant = {
          _id: userToApprove._id,
          address: userToApprove.wallet_address || userToApprove.address,
          name: userToApprove.name || userToApprove.username,
          company: userToApprove.company,
          role: userToApprove.role,
          participant_type: userToApprove.participant_type || userToApprove.role,
          email: userToApprove.email,
          phone: userToApprove.phone || '+1-555-0000',
          location: userToApprove.location || 'Unknown',
          description: userToApprove.description || `${userToApprove.role} services`,
          chain_id: userToApprove.chain_id || (userToApprove.role === 'transporter' ? 421614 : 84532),
          status: 'active',
          created_at: userToApprove.created_at
        };

        // Add to participants list
        setParticipants(prev => [...prev, newParticipant]);
        
        // Remove from pending list
        setPendingUsers(prev => prev.filter(user => user._id !== userId));
        
        // Mark as recently approved
        setRecentlyApproved(prev => new Set([...prev, userId]));
        
        // Switch to participants tab to show the approved user
        setActiveTab('participants');
        
        setLoading(false);
        
        // Show success notification
        setNotification({
          type: 'success',
          message: `✅ ${userToApprove.name || userToApprove.username} has been approved and moved to participants!`
        });
        
        // Clear notification and highlight after 5 seconds
        setTimeout(() => {
          setNotification(null);
          setRecentlyApproved(prev => {
            const newSet = new Set(prev);
            newSet.delete(userId);
            return newSet;
          });
        }, 5000);
      }, 1000);
    } else {
      setLoading(false);
      alert('User not found!');
    }
  };

  const rejectUser = (userId) => {
    setLoading(true);
    
    // Find the user to reject
    const userToReject = pendingUsers.find(user => user._id === userId);
    
    setTimeout(() => {
      // Remove from pending list
      setPendingUsers(prev => prev.filter(user => user._id !== userId));
      
      setLoading(false);
      
      // Show rejection notification
      setNotification({
        type: 'error',
        message: `❌ ${userToReject?.name || userToReject?.username || 'User'} has been rejected and removed.`
      });
      
      // Clear notification after 5 seconds
      setTimeout(() => setNotification(null), 5000);
    }, 1000);
  };

  const registerParticipant = (e) => {
    e.preventDefault();
    setLoading(true);
    
    setTimeout(() => {
      console.log('Participant registered (demo mode):', newParticipant);
      setShowCreateForm(false);
      setNewParticipant({
        address: '',
        name: '',
        company: '',
        role: '',
        participantType: '',
        email: '',
        phone: '',
        location: '',
        description: '',
        chainId: '80002'
      });
      setLoading(false);
      alert('Participant registered successfully! (Demo mode)');
    }, 1500);
  };

  const getParticipantTypeColor = (type) => {
    const colors = {
      'manufacturer': '#10b981',
      'supplier': '#3b82f6',
      'distributor': '#f59e0b',
      'retailer': '#ef4444',
      'logistics': '#8b5cf6',
      'transporter': '#8b5cf6',
      'buyer': '#06b6d4',
      'auditor': '#6b7280'
    };
    return colors[type] || '#6b7280';
  };

  const getRoleIcon = (role) => {
    const icons = {
      'admin': '👨‍💼',
      'manufacturer': '🏭',
      'transporter': '🚛',
      'buyer': '🛒',
      'manager': '👨‍💻',
      'operator': '👨‍🔧',
      'auditor': '🔍',
      'viewer': '👁️'
    };
    return icons[role] || '👤';
  };

  const getStatusBadge = (status) => {
    const config = {
      'approved': { color: '#10b981', bg: '#ecfdf5', text: 'Approved' },
      'pending': { color: '#f59e0b', bg: '#fffbeb', text: 'Pending' },
      'rejected': { color: '#ef4444', bg: '#fef2f2', text: 'Rejected' },
      'active': { color: '#10b981', bg: '#ecfdf5', text: 'Active' }
    };
    const cfg = config[status] || config.pending;
    return (
      <span style={{
        background: cfg.bg,
        color: cfg.color,
        padding: '4px 12px',
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: '500'
      }}>
        {cfg.text}
      </span>
    );
  };

  // Admin Panel for admin role
  if (userRole === 'admin') {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Success/Error Notification */}
        {notification && (
          <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md ${
            notification.type === 'success' 
              ? 'bg-green-100 border border-green-400 text-green-700' 
              : 'bg-red-100 border border-red-400 text-red-700'
          }`}>
            <div className="flex items-center">
              <span className="mr-2 text-lg">
                {notification.type === 'success' ? '✅' : '❌'}
              </span>
              <span className="font-medium">{notification.message}</span>
              <button 
                onClick={() => setNotification(null)}
                className="ml-4 text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="px-6 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
                <p className="text-gray-600 mt-1">Manage participants, approve users, and oversee platform operations</p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={fetchData}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  🔄 Refresh
                </button>
                {activeTab === 'participants' && (
                  <button
                    onClick={() => setShowCreateForm(!showCreateForm)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    {showCreateForm ? 'Cancel' : '+ Add Participant'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="px-6 py-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Participants</p>
                  <p className="text-2xl font-bold text-blue-600">{participants.length}</p>
                </div>
                <div className="text-3xl">👥</div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Pending Approvals</p>
                  <p className="text-2xl font-bold text-orange-600">{pendingUsers.length}</p>
                </div>
                <div className="text-3xl">⏳</div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Users</p>
                  <p className="text-2xl font-bold text-green-600">{stats.activeUsers}</p>
                </div>
                <div className="text-3xl">✅</div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Platform Health</p>
                  <p className="text-2xl font-bold text-green-600">99.9%</p>
                </div>
                <div className="text-3xl">💚</div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="mb-6">
            <div className="flex bg-white rounded-lg border border-gray-200 p-1">
              <button
                onClick={() => setActiveTab('participants')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'participants'
                    ? 'bg-blue-500 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                👥 All Participants ({participants.length})
              </button>
              <button
                onClick={() => setActiveTab('pending')}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'pending'
                    ? 'bg-blue-500 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                ⏳ Pending Approvals ({pendingUsers.length})
              </button>
            </div>
          </div>

          {/* Participant Registration Form */}
          {showCreateForm && activeTab === 'participants' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Register New Participant</h3>
              <form onSubmit={registerParticipant}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Full Name *</label>
                    <input
                      type="text"
                      required
                      value={newParticipant.name}
                      onChange={(e) => setNewParticipant({...newParticipant, name: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter full name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Company *</label>
                    <input
                      type="text"
                      required
                      value={newParticipant.company}
                      onChange={(e) => setNewParticipant({...newParticipant, company: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Company name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Participant Type *</label>
                    <select
                      required
                      value={newParticipant.participantType}
                      onChange={(e) => setNewParticipant({...newParticipant, participantType: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select type</option>
                      <option value="manufacturer">Manufacturer</option>
                      <option value="supplier">Supplier</option>
                      <option value="distributor">Distributor</option>
                      <option value="retailer">Retailer</option>
                      <option value="transporter">Transporter</option>
                      <option value="buyer">Buyer</option>
                      <option value="auditor">Auditor</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Role *</label>
                    <select
                      required
                      value={newParticipant.role}
                      onChange={(e) => setNewParticipant({...newParticipant, role: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select role</option>
                      <option value="admin">Admin</option>
                      <option value="manager">Manager</option>
                      <option value="operator">Operator</option>
                      <option value="auditor">Auditor</option>
                      <option value="viewer">Viewer</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                    <input
                      type="email"
                      value={newParticipant.email}
                      onChange={(e) => setNewParticipant({...newParticipant, email: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="email@company.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Blockchain Address</label>
                    <input
                      type="text"
                      value={newParticipant.address}
                      onChange={(e) => setNewParticipant({...newParticipant, address: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="0x... (auto-filled if empty)"
                    />
                  </div>
                </div>
                <div className="mt-6">
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Registering...' : 'Register on Blockchain'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Content based on active tab */}
          {activeTab === 'participants' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">All Participants</h3>
              {participants.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No participants found. Register the first participant to get started.
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  {participants.map((participant, index) => (
                    <div 
                      key={participant._id || index} 
                      className={`border rounded-lg p-6 hover:shadow-md transition-all duration-500 bg-white ${
                        recentlyApproved.has(participant._id) 
                          ? 'border-green-400 bg-green-50 shadow-lg ring-2 ring-green-200' 
                          : 'border-gray-200'
                      }`}
                    >
                      {recentlyApproved.has(participant._id) && (
                        <div className="flex items-center justify-center mb-3">
                          <span className="bg-green-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                            ✅ Recently Approved!
                          </span>
                        </div>
                      )}
                      <div className="flex items-center space-x-3 mb-4">
                        <div className="text-3xl">{getRoleIcon(participant.role || participant.metadata?.role)}</div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-900 text-lg">
                            {participant.name || participant.metadata?.name || 'Anonymous'}
                          </h4>
                          <p className="text-sm text-gray-600">
                            {participant.company || participant.metadata?.company || 'No company'}
                          </p>
                        </div>
                      </div>

                      {/* Role and Status Badges */}
                      <div className="flex flex-wrap gap-2 mb-4">
                        <span style={{ 
                          background: getParticipantTypeColor(participant.participant_type || participant.participantType),
                          color: 'white',
                          padding: '4px 12px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: '500'
                        }}>
                          {(participant.participant_type || participant.participantType || 'unknown').toUpperCase()}
                        </span>
                        {getStatusBadge(participant.status || 'active')}
                      </div>

                      {/* Contact Information */}
                      <div className="space-y-2 mb-4">
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="w-4 h-4 mr-2">📧</span>
                          <span className="truncate">{participant.email || 'No email'}</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="w-4 h-4 mr-2">📞</span>
                          <span>{participant.phone || 'No phone'}</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="w-4 h-4 mr-2">📍</span>
                          <span>{participant.location || 'No location'}</span>
                        </div>
                      </div>

                      {/* Blockchain Information */}
                      <div className="border-t border-gray-100 pt-4 space-y-2">
                        <div className="text-xs font-medium text-gray-700 mb-2">Blockchain Details</div>
                        <div className="flex items-center text-xs text-gray-600">
                          <span className="w-4 h-4 mr-2">🔗</span>
                          <span className="font-mono text-xs truncate">{participant.address || 'No address'}</span>
                        </div>
                        <div className="flex items-center text-xs text-gray-600">
                          <span className="w-4 h-4 mr-2">⛓️</span>
                          <span>
                            {participant.chain_id === 84532 ? 'Base Sepolia (84532)' :
                             participant.chain_id === 421614 ? 'Arbitrum Sepolia (421614)' :
                             participant.chain_id === 11155420 ? 'Optimism Sepolia (11155420)' :
                             participant.chain_id === 80002 ? 'Polygon Amoy (80002)' :
                             `Chain ID: ${participant.chain_id || 'Unknown'}`}
                          </span>
                        </div>
                      </div>

                      {/* Description */}
                      {participant.description && (
                        <div className="border-t border-gray-100 pt-4 mt-4">
                          <div className="text-xs font-medium text-gray-700 mb-1">Description</div>
                          <p className="text-xs text-gray-600">{participant.description}</p>
                        </div>
                      )}

                      {/* Registration Date */}
                      <div className="border-t border-gray-100 pt-4 mt-4">
                        <div className="text-xs text-gray-500">
                          Registered: {participant.created_at ? new Date(participant.created_at).toLocaleDateString() : 'Unknown'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'pending' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Pending User Approvals</h3>
              {pendingUsers.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No pending approvals. All users are up to date.
                </div>
              ) : (
                <div className="space-y-6">
                  {pendingUsers.map((user, index) => (
                    <div key={user._id || index} className="border border-gray-200 rounded-lg p-6 bg-white">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-4">
                          <div className="text-3xl">{getRoleIcon(user.role)}</div>
                          <div>
                            <h4 className="font-semibold text-gray-900 text-lg">{user.username}</h4>
                            <p className="text-sm text-gray-600">{user.company || 'No company'}</p>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => approveUser(user._id)}
                            disabled={loading}
                            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center space-x-1"
                          >
                            <span>✅</span>
                            <span>Approve</span>
                          </button>
                          <button
                            onClick={() => rejectUser(user._id)}
                            disabled={loading}
                            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center space-x-1"
                          >
                            <span>❌</span>
                            <span>Reject</span>
                          </button>
                        </div>
                      </div>

                      {/* User Details */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-2">
                          <div className="flex items-center text-sm text-gray-600">
                            <span className="w-4 h-4 mr-2">📧</span>
                            <span>{user.email}</span>
                          </div>
                          <div className="flex items-center text-sm text-gray-600">
                            <span className="w-4 h-4 mr-2">👤</span>
                            <span className="capitalize">{user.role}</span>
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <div className="flex items-center text-sm text-gray-600">
                            <span className="w-4 h-4 mr-2">🔗</span>
                            <span className="font-mono text-xs">{user.wallet_address}</span>
                          </div>
                          <div className="flex items-center text-sm text-gray-600">
                            <span className="w-4 h-4 mr-2">📅</span>
                            <span>{new Date(user.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>

                      {/* Status Badge */}
                      <div className="flex items-center justify-between">
                        <div>
                          {getStatusBadge('pending')}
                        </div>
                        <div className="text-xs text-gray-500">
                          Requested: {new Date(user.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Network Status for non-admin roles
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Network Status</h1>
              <p className="text-gray-600 mt-1">View platform participants and network health</p>
            </div>
            <button
              onClick={fetchData}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Network Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Network Participants</p>
                <p className="text-2xl font-bold text-blue-600">{participants.length}</p>
              </div>
              <div className="text-3xl">👥</div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Users</p>
                <p className="text-2xl font-bold text-green-600">{stats.activeUsers}</p>
              </div>
              <div className="text-3xl">✅</div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Network Health</p>
                <p className="text-2xl font-bold text-green-600">99.9%</p>
              </div>
              <div className="text-3xl">💚</div>
            </div>
          </div>
        </div>

        {/* Participants Grid */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Network Participants</h3>
          {participants.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No participants found in the network.
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {participants.map((participant, index) => (
                <div key={participant._id || index} className="border border-gray-200 rounded-lg p-6 bg-white hover:shadow-md transition-shadow">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="text-3xl">{getRoleIcon(participant.role || participant.metadata?.role)}</div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-gray-900 text-lg">
                        {participant.name || participant.metadata?.name || 'Anonymous'}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {participant.company || participant.metadata?.company || 'No company'}
                      </p>
                    </div>
                  </div>

                  {/* Role and Status Badges */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span style={{ 
                      background: getParticipantTypeColor(participant.participant_type || participant.participantType),
                      color: 'white',
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '500'
                    }}>
                      {(participant.participant_type || participant.participantType || 'unknown').toUpperCase()}
                    </span>
                    {getStatusBadge(participant.status || 'active')}
                  </div>

                  {/* Contact Information */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="w-4 h-4 mr-2">📧</span>
                      <span className="truncate">{participant.email || 'No email'}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="w-4 h-4 mr-2">📞</span>
                      <span>{participant.phone || 'No phone'}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="w-4 h-4 mr-2">📍</span>
                      <span>{participant.location || 'No location'}</span>
                    </div>
                  </div>

                  {/* Blockchain Information */}
                  <div className="border-t border-gray-100 pt-4 space-y-2">
                    <div className="text-xs font-medium text-gray-700 mb-2">Blockchain Details</div>
                    <div className="flex items-center text-xs text-gray-600">
                      <span className="w-4 h-4 mr-2">🔗</span>
                      <span className="font-mono text-xs truncate">{participant.address || 'No address'}</span>
                    </div>
                    <div className="flex items-center text-xs text-gray-600">
                      <span className="w-4 h-4 mr-2">⛓️</span>
                      <span>
                        {participant.chain_id === 84532 ? 'Base Sepolia (84532)' :
                         participant.chain_id === 421614 ? 'Arbitrum Sepolia (421614)' :
                         participant.chain_id === 11155420 ? 'Optimism Sepolia (11155420)' :
                         participant.chain_id === 80002 ? 'Polygon Amoy (80002)' :
                         `Chain ID: ${participant.chain_id || 'Unknown'}`}
                      </span>
                    </div>
                  </div>

                  {/* Description */}
                  {participant.description && (
                    <div className="border-t border-gray-100 pt-4 mt-4">
                      <div className="text-xs font-medium text-gray-700 mb-1">Description</div>
                      <p className="text-xs text-gray-600">{participant.description}</p>
                    </div>
                  )}

                  {/* Registration Date */}
                  <div className="border-t border-gray-100 pt-4 mt-4">
                    <div className="text-xs text-gray-500">
                      Registered: {participant.created_at ? new Date(participant.created_at).toLocaleDateString() : 'Unknown'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ParticipantManagement;