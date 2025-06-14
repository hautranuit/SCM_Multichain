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
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center px-4 py-8">
      <div className="max-w-2xl w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-emerald-600 rounded-lg flex items-center justify-center">
            <UserPlus className="h-6 w-6 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Join ChainFLIP
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Register for Multi-Chain Supply Chain Access
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
            {/* Role Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Select Your Role
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {roles.map((role) => {
                  const RoleIcon = role.icon;
                  return (
                    <div
                      key={role.value}
                      onClick={() => setFormData({ ...formData, role: role.value })}
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        formData.role === role.value
                          ? 'border-emerald-500 bg-emerald-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex flex-col items-center text-center space-y-2">
                        <RoleIcon className={`h-8 w-8 ${
                          formData.role === role.value ? 'text-emerald-600' : 'text-gray-400'
                        }`} />
                        <h3 className="font-medium text-gray-900">{role.label}</h3>
                        <p className="text-xs text-gray-500">{role.description}</p>
                        <p className="text-xs text-emerald-600 font-medium">{role.l2Chain}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Personal Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Full Name
                </label>
                <div className="mt-1 relative">
                  <User className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <input
                    id="name"
                    name="name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={handleChange}
                    className="pl-10 block w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 py-2"
                    placeholder="Enter your full name"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email Address
                </label>
                <div className="mt-1 relative">
                  <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    className="pl-10 block w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 py-2"
                    placeholder="Enter your email"
                  />
                </div>
              </div>
            </div>

            {/* Wallet Address */}
            <div>
              <label htmlFor="wallet_address" className="block text-sm font-medium text-gray-700">
                Ethereum Wallet Address
              </label>
              <div className="mt-1 relative">
                <Wallet className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                <input
                  id="wallet_address"
                  name="wallet_address"
                  type="text"
                  required
                  value={formData.wallet_address}
                  onChange={handleChange}
                  className={`pl-10 block w-full rounded-md shadow-sm py-2 ${
                    errors.wallet_address
                      ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                      : 'border-gray-300 focus:ring-emerald-500 focus:border-emerald-500'
                  }`}
                  placeholder="0x..."
                />
              </div>
              {errors.wallet_address && (
                <p className="mt-1 text-sm text-red-600">{errors.wallet_address}</p>
              )}
            </div>

            {/* Password Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <div className="mt-1 relative">
                  <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className={`pl-10 block w-full rounded-md shadow-sm py-2 ${
                      errors.password
                        ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300 focus:ring-emerald-500 focus:border-emerald-500'
                    }`}
                    placeholder="Enter password"
                  />
                </div>
                {errors.password && (
                  <p className="mt-1 text-sm text-red-600">{errors.password}</p>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                  Confirm Password
                </label>
                <div className="mt-1 relative">
                  <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    required
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={`pl-10 block w-full rounded-md shadow-sm py-2 ${
                      errors.confirmPassword
                        ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                        : 'border-gray-300 focus:ring-emerald-500 focus:border-emerald-500'
                    }`}
                    placeholder="Confirm password"
                  />
                </div>
                {errors.confirmPassword && (
                  <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
                )}
              </div>
            </div>

            {/* Selected Role Summary */}
            <div className="bg-emerald-50 border border-emerald-200 rounded-md p-4">
              <div className="flex items-center space-x-3">
                <IconComponent className="h-6 w-6 text-emerald-600" />
                <div>
                  <h4 className="font-medium text-emerald-900">
                    Registering as: {selectedRole?.label}
                  </h4>
                  <p className="text-sm text-emerald-700">{selectedRole?.description}</p>
                  <p className="text-sm font-medium text-emerald-800">
                    You will be assigned to: {selectedRole?.l2Chain}
                  </p>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin h-4 w-4 mr-2" />
                  Creating Account...
                </>
              ) : (
                <>
                  <UserPlus className="h-4 w-4 mr-2" />
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
                className="font-medium text-emerald-600 hover:text-emerald-500"
              >
                Sign in here
              </button>
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-2">Registration Process:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Submit your registration form</li>
                <li>Wait for admin approval (you'll receive an email)</li>
                <li>Once approved, you'll be automatically assigned to your L2 blockchain</li>
                <li>Start using ChainFLIP with full access to your role's features</li>
              </ol>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterForm;