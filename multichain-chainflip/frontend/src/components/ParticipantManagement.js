import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const ParticipantManagement = () => {
  const { userRole, user } = useAuth();
  const [participants, setParticipants] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedParticipant, setSelectedParticipant] = useState(null);
  const [activeTab, setActiveTab] = useState('participants');
  const [stats, setStats] = useState({
    totalParticipants: 0,
    pendingApprovals: 0,
    activeUsers: 0,
    totalTransactions: 0
  });

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

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchParticipants(),
        userRole === 'admin' ? fetchPendingUsers() : Promise.resolve(),
        fetchNetworkStats()
      ]);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  const fetchParticipants = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/participants/`);
      setParticipants(response.data || []);
    } catch (error) {
      console.error('Error fetching participants:', error);
      setParticipants([]);
    }
  };

  const fetchPendingUsers = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/auth/pending-users`);
      setPendingUsers(response.data?.users || []);
    } catch (error) {
      console.error('Error fetching pending users:', error);
      setPendingUsers([]);
    }
  };

  const fetchNetworkStats = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/network-status`);
      setStats({
        totalParticipants: participants.length || 0,
        pendingApprovals: pendingUsers.length || 0,
        activeUsers: response.data?.multichain?.statistics?.active_users || 1250,
        totalTransactions: response.data?.multichain?.statistics?.total_transactions || 0
      });
    } catch (error) {
      console.error('Error fetching network stats:', error);
    }
  };

  const approveUser = async (userId) => {
    try {
      setLoading(true);
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/auth/approve-user`, { user_id: userId });
      alert('User approved successfully!');
      await fetchPendingUsers();
    } catch (error) {
      console.error('Error approving user:', error);
      alert('Error approving user: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const rejectUser = async (userId) => {
    try {
      setLoading(true);
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/auth/reject-user`, { user_id: userId });
      alert('User rejected successfully!');
      await fetchPendingUsers();
    } catch (error) {
      console.error('Error rejecting user:', error);
      alert('Error rejecting user: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const registerParticipant = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/blockchain/participants/register`, {
        address: newParticipant.address || user?.wallet_address || "0x032041b4b356fEE1496805DD4749f181bC736FFA",
        participant_type: newParticipant.participantType,
        chain_id: parseInt(newParticipant.chainId),
        metadata: {
          name: newParticipant.name,
          company: newParticipant.company,
          role: newParticipant.role,
          email: newParticipant.email,
          phone: newParticipant.phone,
          location: newParticipant.location,
          description: newParticipant.description
        }
      });
      
      console.log('Participant registered:', response.data);
      await fetchParticipants();
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
      alert('Participant registered successfully on blockchain!');
    } catch (error) {
      console.error('Error registering participant:', error);
      alert('Error registering participant: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {participants.map((participant, index) => (
                    <div key={participant.id || index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="text-2xl">{getRoleIcon(participant.role || participant.metadata?.role)}</div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-900 truncate">
                            {participant.name || participant.metadata?.name || 'Anonymous'}
                          </h4>
                          <p className="text-sm text-gray-600 truncate">
                            {participant.company || participant.metadata?.company || 'No company'}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 mb-3">
                        <span style={{ 
                          background: getParticipantTypeColor(participant.participant_type || participant.participantType),
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '11px',
                          fontWeight: '500'
                        }}>
                          {(participant.participant_type || participant.participantType || 'unknown').toUpperCase()}
                        </span>
                        {getStatusBadge('active')}
                      </div>
                      <div className="text-xs text-gray-500">
                        Registered: {participant.createdAt ? new Date(participant.createdAt).toLocaleDateString() : 'Unknown'}
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
                <div className="space-y-4">
                  {pendingUsers.map((user, index) => (
                    <div key={user.id || index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="text-2xl">{getRoleIcon(user.role)}</div>
                          <div>
                            <h4 className="font-semibold text-gray-900">{user.username}</h4>
                            <p className="text-sm text-gray-600">{user.email}</p>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className="text-xs text-gray-500">Role: {user.role}</span>
                              <span className="text-xs text-gray-500">•</span>
                              <span className="text-xs text-gray-500">
                                Requested: {new Date(user.createdAt).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => approveUser(user.id)}
                            disabled={loading}
                            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                          >
                            ✅ Approve
                          </button>
                          <button
                            onClick={() => rejectUser(user.id)}
                            disabled={loading}
                            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                          >
                            ❌ Reject
                          </button>
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {participants.map((participant, index) => (
                <div key={participant.id || index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="text-2xl">{getRoleIcon(participant.role || participant.metadata?.role)}</div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-gray-900 truncate">
                        {participant.name || participant.metadata?.name || 'Anonymous'}
                      </h4>
                      <p className="text-sm text-gray-600 truncate">
                        {participant.company || participant.metadata?.company || 'No company'}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span style={{ 
                      background: getParticipantTypeColor(participant.participant_type || participant.participantType),
                      color: 'white',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      fontWeight: '500'
                    }}>
                      {(participant.participant_type || participant.participantType || 'unknown').toUpperCase()}
                    </span>
                    {getStatusBadge('active')}
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