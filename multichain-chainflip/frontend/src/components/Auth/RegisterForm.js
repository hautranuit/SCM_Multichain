import React, { useState } from 'react';
import { Mail, Lock, User, Wallet, UserPlus, Loader2, Building, Truck, ShoppingCart } from 'lucide-react';

const RegisterForm = ({ onRegister, isLoading }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    wallet_address: '',
    role: 'manufacturer'
  });

  const [errors, setErrors] = useState({});

  const roles = [
    {
      value: 'manufacturer',
      label: 'Manufacturer',
      icon: Building,
      description: 'Produce and create products in the supply chain',
      l2Chain: 'Base Sepolia (Chain ID: 84532)'
    },
    {
      value: 'transporter',
      label: 'Transporter',
      icon: Truck,
      description: 'Transport and logistics for supply chain',
      l2Chain: 'Arbitrum Sepolia (Chain ID: 421614)'
    },
    {
      value: 'buyer',
      label: 'Buyer',
      icon: ShoppingCart,
      description: 'Purchase and verify products',
      l2Chain: 'Optimism Sepolia (Chain ID: 11155420)'
    }
  ];

  const validateForm = () => {
    const newErrors = {};

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (!formData.wallet_address.match(/^0x[a-fA-F0-9]{40}$/)) {
      newErrors.wallet_address = 'Invalid Ethereum wallet address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      const { confirmPassword, ...submitData } = formData;
      onRegister(submitData);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear error when user starts typing
    if (errors[e.target.name]) {
      setErrors({
        ...errors,
        [e.target.name]: ''
      });
    }
  };

  const selectedRole = roles.find(role => role.value === formData.role);
  const IconComponent = selectedRole?.icon || Building;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-100 flex items-center justify-center px-4 py-8">
      <div className="max-w-2xl w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
            <UserPlus className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-4xl font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Join ChainFLIP
          </h2>
          <p className="mt-3 text-lg text-gray-600">
            Register for Multi-Chain Supply Chain Access
          </p>
          <div className="mt-4 flex items-center justify-center space-x-2">
            <div className="h-1 w-12 bg-gradient-to-r from-blue-400 to-indigo-400 rounded-full"></div>
            <div className="h-1 w-1 bg-gray-300 rounded-full"></div>
            <div className="h-1 w-12 bg-gradient-to-r from-indigo-400 to-purple-400 rounded-full"></div>
          </div>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-xl border border-white/20 p-8 space-y-6">
            {/* Role Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4">
                Select Your Role
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {roles.map((role) => {
                  const RoleIcon = role.icon;
                  return (
                    <div
                      key={role.value}
                      onClick={() => setFormData({ ...formData, role: role.value })}
                      className={`p-5 border-2 rounded-xl cursor-pointer transition-all duration-200 transform hover:scale-105 ${
                        formData.role === role.value
                          ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-md'
                          : 'border-gray-200 hover:border-gray-300 bg-white hover:shadow-md'
                      }`}
                    >
                      <div className="flex flex-col items-center text-center space-y-3">
                        <div className={`p-3 rounded-xl ${
                          formData.role === role.value ? 'bg-blue-100' : 'bg-gray-100'
                        }`}>
                          <RoleIcon className={`h-8 w-8 ${
                            formData.role === role.value ? 'text-blue-600' : 'text-gray-400'
                          }`} />
                        </div>
                        <h3 className="font-semibold text-gray-900">{role.label}</h3>
                        <p className="text-xs text-gray-500 leading-relaxed">{role.description}</p>
                        <p className="text-xs text-blue-600 font-medium bg-blue-50 px-2 py-1 rounded-md">{role.l2Chain}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Personal Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name
                </label>
                <div className="relative group">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                  <input
                    id="name"
                    name="name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={handleChange}
                    className="pl-10 block w-full border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent py-3 px-4 transition-all duration-200 bg-white/50 backdrop-blur-sm"
                    placeholder="Enter your full name"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <div className="relative group">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    className="pl-10 block w-full border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent py-3 px-4 transition-all duration-200 bg-white/50 backdrop-blur-sm"
                    placeholder="Enter your email"
                  />
                </div>
              </div>
            </div>

            {/* Wallet Address */}
            <div>
              <label htmlFor="wallet_address" className="block text-sm font-medium text-gray-700 mb-2">
                Ethereum Wallet Address
              </label>
              <div className="relative group">
                <Wallet className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                <input
                  id="wallet_address"
                  name="wallet_address"
                  type="text"
                  required
                  value={formData.wallet_address}
                  onChange={handleChange}
                  className={`pl-10 block w-full rounded-xl shadow-sm py-3 px-4 transition-all duration-200 bg-white/50 backdrop-blur-sm ${
                    errors.wallet_address
                      ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                      : 'border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                  }`}
                  placeholder="0x..."
                />
              </div>
              {errors.wallet_address && (
                <p className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded-lg">{errors.wallet_address}</p>
              )}
            </div>

            {/* Password Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className={`pl-10 block w-full rounded-xl shadow-sm py-3 px-4 transition-all duration-200 bg-white/50 backdrop-blur-sm ${
                      errors.password
                        ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                    }`}
                    placeholder="Enter password"
                  />
                </div>
                {errors.password && (
                  <p className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded-lg">{errors.password}</p>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm Password
                </label>
                <div className="relative group">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    required
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={`pl-10 block w-full rounded-xl shadow-sm py-3 px-4 transition-all duration-200 bg-white/50 backdrop-blur-sm ${
                      errors.confirmPassword
                        ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                    }`}
                    placeholder="Confirm password"
                  />
                </div>
                {errors.confirmPassword && (
                  <p className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded-lg">{errors.confirmPassword}</p>
                )}
              </div>
            </div>

            {/* Selected Role Summary */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-blue-100 rounded-xl">
                  <IconComponent className="h-8 w-8 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-blue-900 text-lg">
                    Registering as: {selectedRole?.label}
                  </h4>
                  <p className="text-sm text-blue-700 mt-1">{selectedRole?.description}</p>
                  <p className="text-sm font-medium text-blue-800 mt-2 bg-blue-100 inline-block px-3 py-1 rounded-lg">
                    📍 Chain Assignment: {selectedRole?.l2Chain}
                  </p>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center py-4 px-6 border border-transparent rounded-xl shadow-lg text-lg font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin h-5 w-5 mr-3" />
                  Creating Account...
                </>
              ) : (
                <>
                  <UserPlus className="h-5 w-5 mr-3" />
                  Create Account
                </>
              )}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => window.location.href = '/login'}
                className="font-medium text-blue-600 hover:text-blue-500 transition-colors"
              >
                Sign in here
              </button>
            </p>
          </div>

          <div className="bg-white/80 backdrop-blur-lg border border-blue-200 rounded-xl p-6">
            <div className="text-sm text-blue-800">
              <p className="font-semibold mb-3 text-lg">🚀 Registration Process:</p>
              <ol className="list-decimal list-inside space-y-2 text-gray-700">
                <li className="flex items-center">
                  <span className="mr-2">📝</span>
                  Submit your registration form
                </li>
                <li className="flex items-center">
                  <span className="mr-2">⏳</span>
                  Wait for admin approval (you'll receive an email)
                </li>
                <li className="flex items-center">
                  <span className="mr-2">🔗</span>
                  Once approved, you'll be automatically assigned to your L2 blockchain
                </li>
                <li className="flex items-center">
                  <span className="mr-2">🎉</span>
                  Start using ChainFLIP with full access to your role's features
                </li>
              </ol>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterForm;