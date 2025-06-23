import React, { useState } from 'react';
import { MapPin, Phone, Mail, User, Package, Truck } from 'lucide-react';

const ShippingInformationForm = ({ 
  onSubmit, 
  onCancel, 
  productName = "Product", 
  productPrice = "0.001",
  loading = false 
}) => {
  const [shippingInfo, setShippingInfo] = useState({
    name: '',
    phone: '',
    email: '',
    street: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'USA',
    delivery_instructions: '',
    signature_required: true
  });

  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (!shippingInfo.name.trim()) newErrors.name = 'Name is required';
    if (!shippingInfo.phone.trim()) newErrors.phone = 'Phone number is required';
    if (!shippingInfo.email.trim()) newErrors.email = 'Email is required';
    if (!shippingInfo.street.trim()) newErrors.street = 'Street address is required';
    if (!shippingInfo.city.trim()) newErrors.city = 'City is required';
    if (!shippingInfo.state.trim()) newErrors.state = 'State is required';
    if (!shippingInfo.zip_code.trim()) newErrors.zip_code = 'ZIP code is required';
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (shippingInfo.email && !emailRegex.test(shippingInfo.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    // Phone validation (basic)
    const phoneRegex = /^[\+]?[\d\s\-\(\)]{10,}$/;
    if (shippingInfo.phone && !phoneRegex.test(shippingInfo.phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(shippingInfo);
    }
  };

  const handleInputChange = (field, value) => {
    setShippingInfo(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 rounded-3xl border border-white/20 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-4">
              <Package className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">Shipping Information</h2>
            <p className="text-blue-100/80">Please provide delivery details for your purchase</p>
            <div className="mt-4 bg-white/10 backdrop-blur-sm rounded-2xl p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/70">Product:</span>
                <span className="text-white font-medium">{productName}</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <span className="text-white/70">Price:</span>
                <span className="text-cyan-400 font-bold">{productPrice} ETH</span>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Contact Information */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                <User className="w-5 h-5 mr-2 text-blue-400" />
                Contact Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-white/90 font-medium mb-2">Full Name *</label>
                  <input
                    type="text"
                    value={shippingInfo.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className={`w-full px-4 py-3 bg-white/10 backdrop-blur-sm border rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 transition-all duration-200 ${
                      errors.name ? 'border-red-400 focus:ring-red-400/25' : 'border-white/20 focus:border-cyan-400 focus:ring-cyan-400/25'
                    }`}
                    placeholder="Enter your full name"
                  />
                  {errors.name && <p className="text-red-400 text-sm mt-1">{errors.name}</p>}
                </div>
                
                <div>
                  <label className="block text-white/90 font-medium mb-2">Phone Number *</label>
                  <input
                    type="tel"
                    value={shippingInfo.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    className={`w-full px-4 py-3 bg-white/10 backdrop-blur-sm border rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 transition-all duration-200 ${
                      errors.phone ? 'border-red-400 focus:ring-red-400/25' : 'border-white/20 focus:border-cyan-400 focus:ring-cyan-400/25'
                    }`}
                    placeholder="+1 (555) 123-4567"
                  />
                  {errors.phone && <p className="text-red-400 text-sm mt-1">{errors.phone}</p>}
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-white/90 font-medium mb-2">Email Address *</label>
                  <input
                    type="email"
                    value={shippingInfo.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className={`w-full px-4 py-3 bg-white/10 backdrop-blur-sm border rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 transition-all duration-200 ${
                      errors.email ? 'border-red-400 focus:ring-red-400/25' : 'border-white/20 focus:border-cyan-400 focus:ring-cyan-400/25'
                    }`}
                    placeholder="your.email@example.com"
                  />
                  {errors.email && <p className="text-red-400 text-sm mt-1">{errors.email}</p>}
                </div>
              </div>
            </div>

            {/* Delivery Address */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                <MapPin className="w-5 h-5 mr-2 text-green-400" />
                Delivery Address
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-white/90 font-medium mb-2">Street Address *</label>
                  <input
                    type="text"
                    value={shippingInfo.street}
                    onChange={(e) => handleInputChange('street', e.target.value)}
                    className={`w-full px-4 py-3 bg-white/10 backdrop-blur-sm border rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 transition-all duration-200 ${
                      errors.street ? 'border-red-400 focus:ring-red-400/25' : 'border-white/20 focus:border-cyan-400 focus:ring-cyan-400/25'
                    }`}
                    placeholder="123 Main Street, Apt 4B"
                  />
                  {errors.street && <p className="text-red-400 text-sm mt-1">{errors.street}</p>}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-white/90 font-medium mb-2">City *</label>
                    <input
                      type="text"
                      value={shippingInfo.city}
                      onChange={(e) => handleInputChange('city', e.target.value)}
                      className={`w-full px-4 py-3 bg-white/10 backdrop-blur-sm border rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 transition-all duration-200 ${
                        errors.city ? 'border-red-400 focus:ring-red-400/25' : 'border-white/20 focus:border-cyan-400 focus:ring-cyan-400/25'
                      }`}
                      placeholder="New York"
                    />
                    {errors.city && <p className="text-red-400 text-sm mt-1">{errors.city}</p>}
                  </div>
                  
                  <div>
                    <label className="block text-white/90 font-medium mb-2">State *</label>
                    <input
                      type="text"
                      value={shippingInfo.state}
                      onChange={(e) => handleInputChange('state', e.target.value)}
                      className={`w-full px-4 py-3 bg-white/10 backdrop-blur-sm border rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 transition-all duration-200 ${
                        errors.state ? 'border-red-400 focus:ring-red-400/25' : 'border-white/20 focus:border-cyan-400 focus:ring-cyan-400/25'
                      }`}
                      placeholder="NY"
                    />
                    {errors.state && <p className="text-red-400 text-sm mt-1">{errors.state}</p>}
                  </div>
                  
                  <div>
                    <label className="block text-white/90 font-medium mb-2">ZIP Code *</label>
                    <input
                      type="text"
                      value={shippingInfo.zip_code}
                      onChange={(e) => handleInputChange('zip_code', e.target.value)}
                      className={`w-full px-4 py-3 bg-white/10 backdrop-blur-sm border rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 transition-all duration-200 ${
                        errors.zip_code ? 'border-red-400 focus:ring-red-400/25' : 'border-white/20 focus:border-cyan-400 focus:ring-cyan-400/25'
                      }`}
                      placeholder="10001"
                    />
                    {errors.zip_code && <p className="text-red-400 text-sm mt-1">{errors.zip_code}</p>}
                  </div>
                </div>
                
                <div>
                  <label className="block text-white/90 font-medium mb-2">Country</label>
                  <select
                    value={shippingInfo.country}
                    onChange={(e) => handleInputChange('country', e.target.value)}
                    className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200"
                  >
                    <option value="USA" className="bg-slate-800">United States</option>
                    <option value="Canada" className="bg-slate-800">Canada</option>
                    <option value="Mexico" className="bg-slate-800">Mexico</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Delivery Preferences */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                <Truck className="w-5 h-5 mr-2 text-yellow-400" />
                Delivery Preferences
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-white/90 font-medium mb-2">Delivery Instructions</label>
                  <textarea
                    value={shippingInfo.delivery_instructions}
                    onChange={(e) => handleInputChange('delivery_instructions', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-white/50 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/25 transition-all duration-200 resize-none"
                    placeholder="Special delivery instructions (optional)"
                  />
                </div>
                
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    id="signature"
                    checked={shippingInfo.signature_required}
                    onChange={(e) => handleInputChange('signature_required', e.target.checked)}
                    className="w-5 h-5 text-cyan-500 bg-white/10 border-white/20 rounded focus:ring-cyan-500 focus:ring-2"
                  />
                  <label htmlFor="signature" className="text-white/90 font-medium">
                    Require signature on delivery
                  </label>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-6">
              <button
                type="button"
                onClick={onCancel}
                disabled={loading}
                className="flex-1 px-8 py-4 bg-white/10 backdrop-blur-sm border border-white/20 text-white rounded-2xl hover:bg-white/20 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel Purchase
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-2xl transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/25 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {loading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Processing Purchase...</span>
                  </div>
                ) : (
                  'Complete Purchase'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ShippingInformationForm;
