import React, { useState } from 'react';
import { Truck, Star, MapPin, CheckCircle, AlertCircle, User } from 'lucide-react';

const TransporterRegistration = () => {
  const [formData, setFormData] = useState({
    address: '',
    chain_id: '421614', // Arbitrum Sepolia by default
    location: '',
    coordinates: ['', ''],
    capacity: '',
    vehicle_type: '',
    contact_info: '',
    experience_years: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Create transporter reputation record
      const reputation_data = {
        transporter_id: `TRANS-${Date.now()}-${Math.random().toString(36).substring(7)}`,
        address: formData.address,
        reputation_score: 0.7, // Starting score
        total_deliveries: 0,
        successful_deliveries: 0,
        status: 'available',
        chain_id: parseInt(formData.chain_id),
        location: formData.location,
        coordinates: [
          parseFloat(formData.coordinates[0]),
          parseFloat(formData.coordinates[1])
        ],
        capacity: formData.capacity,
        vehicle_type: formData.vehicle_type,
        contact_info: formData.contact_info,
        experience_years: parseInt(formData.experience_years),
        role: 'transporter'
      };

      // In a real implementation, this would call a registration endpoint
      // For now, we'll simulate by directly updating the reputation collection
      console.log('Registering transporter:', reputation_data);
      
      setSuccess(true);
      setFormData({
        address: '',
        chain_id: '421614',
        location: '',
        coordinates: ['', ''],
        capacity: '',
        vehicle_type: '',
        contact_info: '',
        experience_years: ''
      });
      
    } catch (error) {
      console.error('Registration error:', error);
      alert(`Registration failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const vehicleTypes = [
    'Small Van',
    'Large Van',
    'Truck',
    'Motorcycle',
    'Bicycle',
    'Cargo Bike',
    'Pickup Truck',
    'Semi Truck'
  ];

  const chainOptions = [
    { value: '421614', label: 'Arbitrum Sepolia (Primary)' },
    { value: '11155420', label: 'Optimism Sepolia' },
    { value: '84532', label: 'Base Sepolia' },
    { value: '80002', label: 'Polygon Amoy' }
  ];

  if (success) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-green-900 mb-2">Registration Successful!</h2>
          <p className="text-green-700 mb-4">
            You've been registered as a transporter. Your starting reputation score is 0.7.
          </p>
          <p className="text-sm text-green-600">
            Complete successful deliveries to improve your reputation and get more assignments.
          </p>
          <button
            onClick={() => setSuccess(false)}
            className="mt-4 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
          >
            Register Another Transporter
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-lg">
          <div className="flex items-center">
            <Truck className="h-8 w-8 mr-3" />
            <div>
              <h1 className="text-2xl font-bold">Transporter Registration</h1>
              <p className="text-blue-100">Join the ChainFLIP supply chain network</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="bg-blue-50 p-4 rounded-lg mb-6">
            <h3 className="font-medium text-blue-900 mb-2">How it works:</h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Register with your wallet address and transportation details</li>
              <li>• Start with a reputation score of 0.7</li>
              <li>• Complete deliveries successfully to improve your reputation</li>
              <li>• Higher reputation = more assignments and better rewards</li>
              <li>• Distance-based assignment: 50-1000 miles determines transporter count</li>
            </ul>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Wallet Address *
              </label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0x..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Primary Chain *
              </label>
              <select
                value={formData.chain_id}
                onChange={(e) => setFormData({...formData, chain_id: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {chainOptions.map(chain => (
                  <option key={chain.value} value={chain.value}>
                    {chain.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location *
              </label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({...formData, location: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="City, State/Country"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Coordinates *
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  step="any"
                  value={formData.coordinates[0]}
                  onChange={(e) => setFormData({
                    ...formData, 
                    coordinates: [e.target.value, formData.coordinates[1]]
                  })}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Latitude"
                  required
                />
                <input
                  type="number"
                  step="any"
                  value={formData.coordinates[1]}
                  onChange={(e) => setFormData({
                    ...formData, 
                    coordinates: [formData.coordinates[0], e.target.value]
                  })}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Longitude"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vehicle Type *
              </label>
              <select
                value={formData.vehicle_type}
                onChange={(e) => setFormData({...formData, vehicle_type: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Select vehicle type</option>
                {vehicleTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Carrying Capacity
              </label>
              <input
                type="text"
                value={formData.capacity}
                onChange={(e) => setFormData({...formData, capacity: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 50kg, 5 cubic meters"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Experience (years)
              </label>
              <input
                type="number"
                value={formData.experience_years}
                onChange={(e) => setFormData({...formData, experience_years: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="3"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Contact Information
              </label>
              <textarea
                value={formData.contact_info}
                onChange={(e) => setFormData({...formData, contact_info: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="3"
                placeholder="Phone, email, or other contact details"
              />
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Reputation System</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-medium text-green-700">Reputation Boosts:</p>
                  <ul className="text-green-600 mt-1 space-y-1">
                    <li>• Successful delivery: +0.02</li>
                    <li>• On-time delivery: +0.01</li>
                    <li>• Excellent condition: +0.01</li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-red-700">Reputation Penalties:</p>
                  <ul className="text-red-600 mt-1 space-y-1">
                    <li>• Failed delivery: -0.05</li>
                    <li>• Late delivery (>150%): -0.03</li>
                    <li>• Poor condition: -0.02</li>
                  </ul>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center font-medium"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Registering...
                </>
              ) : (
                <>
                  <User className="h-4 w-4 mr-2" />
                  Register as Transporter
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TransporterRegistration;
