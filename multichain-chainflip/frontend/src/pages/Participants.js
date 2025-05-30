import React, { useState, useEffect } from 'react';
import { useBlockchain } from '../contexts/BlockchainContext';
import { useNotification } from '../contexts/NotificationContext';

export const Participants = () => {
  const { isConnected, account } = useBlockchain();
  const { showSuccess, showError } = useNotification();
  
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showRegisterModal, setShowRegisterModal] = useState(false);

  useEffect(() => {
    fetchParticipants();
  }, []);

  const fetchParticipants = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/participants/activity`);
      
      if (response.ok) {
        const data = await response.json();
        setParticipants(data.top_participants || []);
      }
    } catch (error) {
      console.error('Failed to fetch participants:', error);
      showError('Failed to load participants');
    } finally {
      setLoading(false);
    }
  };

  const getParticipantTypeColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'manufacturer':
        return 'badge-primary';
      case 'distributor':
        return 'badge-warning';
      case 'retailer':
        return 'badge-success';
      case 'transporter':
        return 'badge-info';
      default:
        return 'badge-gray';
    }
  };

  const getParticipantIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'manufacturer':
        return '🏭';
      case 'distributor':
        return '🚚';
      case 'retailer':
        return '🏪';
      case 'transporter':
        return '🚛';
      default:
        return '👤';
    }
  };

  const getReputationColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const ParticipantCard = ({ participant }) => (
    <div className="card hover:shadow-md transition-shadow duration-200">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="text-3xl">{getParticipantIcon(participant.participant_type)}</div>
          <div>
            <h3 className="font-semibold text-gray-900">
              {participant.address?.slice(0, 10)}...{participant.address?.slice(-4)}
            </h3>
            <span className={`badge ${getParticipantTypeColor(participant.participant_type)}`}>
              {participant.participant_type || 'Unknown'}
            </span>
          </div>
        </div>
        
        <div className="text-right">
          <div className={`text-2xl font-bold ${getReputationColor(participant.reputation_score)}`}>
            {participant.reputation_score || 0}
          </div>
          <div className="text-xs text-gray-500">Reputation</div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-600">Products:</span>
          <span className="ml-2 font-medium">{participant.product_count || 0}</span>
        </div>
        <div>
          <span className="text-gray-600">Chain:</span>
          <span className="ml-2 font-medium">
            {participant.chain_id === 80002 ? 'Polygon PoS' : 'L2 CDK'}
          </span>
        </div>
      </div>
      
      <div className="mt-4 flex space-x-2">
        <button className="btn-secondary text-sm flex-1">
          📊 View Activity
        </button>
        <button className="btn-primary text-sm flex-1">
          📞 Contact
        </button>
      </div>
    </div>
  );

  const RegisterModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Register as Participant</h2>
        
        <form onSubmit={(e) => {
          e.preventDefault();
          const formData = new FormData(e.target);
          const participantType = formData.get('participantType');
          
          // Handle registration logic
          setShowRegisterModal(false);
          showSuccess(`Registration as ${participantType} initiated`);
        }}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Participant Type
              </label>
              <select name="participantType" className="select-field" required>
                <option value="">Select your role</option>
                <option value="manufacturer">Manufacturer</option>
                <option value="distributor">Distributor</option>
                <option value="retailer">Retailer</option>
                <option value="transporter">Transporter</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company Name
              </label>
              <input 
                name="companyName"
                type="text" 
                className="input-field" 
                placeholder="Enter company name" 
                required 
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Wallet Address
              </label>
              <input 
                type="text" 
                className="input-field" 
                value={account || ''}
                disabled
                placeholder="Connect wallet first"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferred Chain
              </label>
              <select name="chainId" className="select-field" required>
                <option value="80002">Polygon PoS (Main Operations)</option>
                <option value="1001">L2 CDK (High-Frequency)</option>
              </select>
            </div>
          </div>
          
          <div className="flex space-x-3 mt-6">
            <button type="submit" className="btn-primary flex-1" disabled={!isConnected}>
              Register
            </button>
            <button 
              type="button" 
              onClick={() => setShowRegisterModal(false)}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Participants</h1>
          <p className="text-gray-600">Network participants across both chains</p>
        </div>
        
        <div className="flex space-x-3">
          <button 
            onClick={fetchParticipants}
            className="btn-secondary"
          >
            🔄 Refresh
          </button>
          {isConnected && (
            <button 
              onClick={() => setShowRegisterModal(true)}
              className="btn-primary"
            >
              ➕ Register
            </button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card text-center">
          <div className="text-3xl mb-2">🏭</div>
          <div className="text-2xl font-bold text-gray-900">
            {participants.filter(p => p.participant_type === 'manufacturer').length}
          </div>
          <div className="text-sm text-gray-600">Manufacturers</div>
        </div>
        
        <div className="card text-center">
          <div className="text-3xl mb-2">🚚</div>
          <div className="text-2xl font-bold text-gray-900">
            {participants.filter(p => p.participant_type === 'distributor').length}
          </div>
          <div className="text-sm text-gray-600">Distributors</div>
        </div>
        
        <div className="card text-center">
          <div className="text-3xl mb-2">🏪</div>
          <div className="text-2xl font-bold text-gray-900">
            {participants.filter(p => p.participant_type === 'retailer').length}
          </div>
          <div className="text-sm text-gray-600">Retailers</div>
        </div>
        
        <div className="card text-center">
          <div className="text-3xl mb-2">🚛</div>
          <div className="text-2xl font-bold text-gray-900">
            {participants.filter(p => p.participant_type === 'transporter').length}
          </div>
          <div className="text-sm text-gray-600">Transporters</div>
        </div>
      </div>

      {/* Connection Warning */}
      {!isConnected && (
        <div className="bg-info-50 border border-info-200 rounded-lg p-4">
          <div className="flex">
            <span className="text-info-600 text-xl mr-3">ℹ️</span>
            <div>
              <h3 className="text-sm font-medium text-info-800">
                Connect Wallet to Register
              </h3>
              <p className="mt-1 text-sm text-info-700">
                Connect your wallet to register as a participant and join the network.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Participants Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      ) : participants.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {participants.map((participant, index) => (
            <ParticipantCard key={participant.address || index} participant={participant} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">👥</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Participants Found</h3>
          <p className="text-gray-600 mb-6">Be the first to register as a participant.</p>
          {isConnected && (
            <button 
              onClick={() => setShowRegisterModal(true)}
              className="btn-primary"
            >
              ➕ Register Now
            </button>
          )}
        </div>
      )}

      {/* Modal */}
      {showRegisterModal && <RegisterModal />}
    </div>
  );
};
