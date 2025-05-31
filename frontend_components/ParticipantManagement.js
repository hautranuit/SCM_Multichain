import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ParticipantManagement = () => {
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedParticipant, setSelectedParticipant] = useState(null);
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
    fetchParticipants();
  }, []);

  const fetchParticipants = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/participants`);
      setParticipants(response.data || []);
    } catch (error) {
      console.error('Error fetching participants:', error);
      setParticipants([]);
    }
    setLoading(false);
  };

  const registerParticipant = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/blockchain/participants/register`, {
        address: newParticipant.address || "0x032041b4b356fEE1496805DD4749f181bC736FFA",
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
      'auditor': '#6b7280'
    };
    return colors[type] || '#6b7280';
  };

  const getRoleIcon = (role) => {
    const icons = {
      'admin': '👨‍💼',
      'manager': '👨‍💻',
      'operator': '👨‍🔧',
      'auditor': '🔍',
      'viewer': '👁️'
    };
    return icons[role] || '👤';
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 'bold', margin: 0 }}>👥 Participants Management</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="btn"
          style={{ 
            background: '#3b82f6', 
            color: 'white', 
            border: 'none', 
            padding: '12px 24px', 
            borderRadius: '8px',
            fontSize: '16px',
            cursor: 'pointer'
          }}
        >
          {showCreateForm ? 'Cancel' : '+ Register Participant'}
        </button>
      </div>

      {/* Register Participant Form */}
      {showCreateForm && (
        <div className="card" style={{ marginBottom: '30px', padding: '20px' }}>
          <h3 style={{ marginBottom: '20px' }}>Register New Participant</h3>
          <form onSubmit={registerParticipant}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Full Name *</label>
                <input
                  type="text"
                  required
                  value={newParticipant.name}
                  onChange={(e) => setNewParticipant({...newParticipant, name: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="Enter full name"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Company *</label>
                <input
                  type="text"
                  required
                  value={newParticipant.company}
                  onChange={(e) => setNewParticipant({...newParticipant, company: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="Company name"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Participant Type *</label>
                <select
                  required
                  value={newParticipant.participantType}
                  onChange={(e) => setNewParticipant({...newParticipant, participantType: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                >
                  <option value="">Select type</option>
                  <option value="manufacturer">Manufacturer</option>
                  <option value="supplier">Supplier</option>
                  <option value="distributor">Distributor</option>
                  <option value="retailer">Retailer</option>
                  <option value="logistics">Logistics Provider</option>
                  <option value="auditor">Auditor</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Role *</label>
                <select
                  required
                  value={newParticipant.role}
                  onChange={(e) => setNewParticipant({...newParticipant, role: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
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
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Email</label>
                <input
                  type="email"
                  value={newParticipant.email}
                  onChange={(e) => setNewParticipant({...newParticipant, email: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="email@company.com"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Phone</label>
                <input
                  type="tel"
                  value={newParticipant.phone}
                  onChange={(e) => setNewParticipant({...newParticipant, phone: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="+1234567890"
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Blockchain Address</label>
                <input
                  type="text"
                  value={newParticipant.address}
                  onChange={(e) => setNewParticipant({...newParticipant, address: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="0x..."
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Chain ID</label>
                <select
                  value={newParticipant.chainId}
                  onChange={(e) => setNewParticipant({...newParticipant, chainId: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                >
                  <option value="80002">Polygon PoS (80002)</option>
                  <option value="2442">L2 CDK (2442)</option>
                </select>
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Location</label>
                <input
                  type="text"
                  value={newParticipant.location}
                  onChange={(e) => setNewParticipant({...newParticipant, location: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px' 
                  }}
                  placeholder="City, Country"
                />
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>Description</label>
                <textarea
                  value={newParticipant.description}
                  onChange={(e) => setNewParticipant({...newParticipant, description: e.target.value})}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '4px',
                    minHeight: '80px'
                  }}
                  placeholder="Brief description of the participant"
                />
              </div>
            </div>
            <div style={{ marginTop: '20px' }}>
              <button
                type="submit"
                disabled={loading}
                className="btn"
                style={{ 
                  background: loading ? '#9ca3af' : '#10b981', 
                  color: 'white', 
                  border: 'none', 
                  padding: '12px 24px', 
                  borderRadius: '8px',
                  fontSize: '16px',
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Registering...' : 'Register on Blockchain'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Participants List */}
      <div className="card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>Registered Participants</h3>
          <button
            onClick={fetchParticipants}
            className="btn"
            style={{ 
              background: '#6b7280', 
              color: 'white', 
              border: 'none', 
              padding: '8px 16px', 
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            🔄 Refresh
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '18px', color: '#6b7280' }}>Loading participants...</div>
          </div>
        )}

        {!loading && participants.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '18px', color: '#6b7280', marginBottom: '10px' }}>No participants registered</div>
            <div style={{ fontSize: '14px', color: '#9ca3af' }}>Register your first participant to get started</div>
          </div>
        )}

        {!loading && participants.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
            {participants.map((participant, index) => (
              <div key={participant.id || index} className="card" style={{ border: '1px solid #e5e7eb', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                  <div>
                    <h4 style={{ margin: '0 0 5px 0', fontSize: '18px', fontWeight: '600' }}>
                      {getRoleIcon(participant.role || participant.metadata?.role)} {participant.name || participant.metadata?.name || 'Unknown'}
                    </h4>
                    <div style={{ fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>
                      {participant.company || participant.metadata?.company || 'Unknown Company'}
                    </div>
                  </div>
                  <span style={{ 
                    background: getParticipantTypeColor(participant.participant_type || participant.participantType),
                    color: 'white',
                    padding: '4px 8px', 
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: '500'
                  }}>
                    {(participant.participant_type || participant.participantType || 'unknown').toUpperCase()}
                  </span>
                </div>
                
                <div style={{ fontSize: '14px', color: '#374151', marginBottom: '15px' }}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>📧 Email:</strong> {participant.email || participant.metadata?.email || 'Not provided'}
                  </div>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>📞 Phone:</strong> {participant.phone || participant.metadata?.phone || 'Not provided'}
                  </div>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>📍 Location:</strong> {participant.location || participant.metadata?.location || 'Not specified'}
                  </div>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>🔗 Address:</strong> 
                    <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                      {participant.address ? `${participant.address.substring(0, 15)}...` : 'Not provided'}
                    </span>
                  </div>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>⛓️ Chain:</strong> {participant.chain_id === 80002 ? 'Polygon PoS' : 'L2 CDK'} ({participant.chain_id})
                  </div>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>👤 Role:</strong> 
                    <span style={{ 
                      background: '#f3f4f6', 
                      padding: '2px 6px', 
                      borderRadius: '4px',
                      marginLeft: '5px'
                    }}>
                      {(participant.role || participant.metadata?.role || 'viewer').toUpperCase()}
                    </span>
                  </div>
                </div>

                {(participant.description || participant.metadata?.description) && (
                  <div style={{ 
                    padding: '10px', 
                    background: '#f9fafb', 
                    borderRadius: '6px',
                    fontSize: '13px',
                    color: '#6b7280',
                    marginBottom: '15px'
                  }}>
                    <strong>Description:</strong> {participant.description || participant.metadata?.description}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                    Registered: {participant.createdAt ? new Date(participant.createdAt).toLocaleDateString() : 'Unknown'}
                  </div>
                  <button
                    onClick={() => setSelectedParticipant(selectedParticipant?.id === participant.id ? null : participant)}
                    className="btn"
                    style={{ 
                      background: '#3b82f6', 
                      color: 'white', 
                      border: 'none', 
                      padding: '6px 12px', 
                      borderRadius: '4px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    {selectedParticipant?.id === participant.id ? 'Hide' : 'Details'}
                  </button>
                </div>

                {selectedParticipant?.id === participant.id && (
                  <div style={{ 
                    marginTop: '15px', 
                    padding: '10px', 
                    background: '#f0f9ff', 
                    borderRadius: '6px',
                    fontSize: '12px',
                    borderLeft: '3px solid #3b82f6'
                  }}>
                    <div><strong>Participant ID:</strong> {participant.id || 'N/A'}</div>
                    <div><strong>Status:</strong> Active</div>
                    <div><strong>Permissions:</strong> Read, Write, Update</div>
                    {participant.transactionHash && (
                      <div><strong>Tx Hash:</strong> {participant.transactionHash.substring(0, 20)}...</div>
                    )}
                    <div style={{ marginTop: '8px', color: '#6b7280' }}>
                      This participant is registered on the blockchain and can participate in supply chain operations.
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ParticipantManagement;