import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Shield, Clock, XCircle, Loader2 } from 'lucide-react';

const ProtectedRoute = ({ children, requireAdmin = false, requireApproval = true }) => {
  const { isLoading, isAuthenticated, user, isAdmin, isApproved } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-12 w-12 text-indigo-600 mx-auto" />
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <Shield className="mx-auto h-12 w-12 text-gray-400" />
          <h2 className="mt-6 text-2xl font-bold text-gray-900">Authentication Required</h2>
          <p className="mt-2 text-gray-600">
            You need to sign in to access this page.
          </p>
          <div className="mt-6 space-y-4">
            <button
              onClick={() => window.location.href = '/login'}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
            >
              Sign In
            </button>
            <button
              onClick={() => window.location.href = '/register'}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Create Account
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (requireAdmin && !isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <XCircle className="mx-auto h-12 w-12 text-red-400" />
          <h2 className="mt-6 text-2xl font-bold text-gray-900">Access Denied</h2>
          <p className="mt-2 text-gray-600">
            You don't have permission to access this page. Admin access required.
          </p>
          <button
            onClick={() => window.location.href = '/dashboard'}
            className="mt-6 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (requireApproval && !isApproved && !isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <Clock className="mx-auto h-12 w-12 text-yellow-400" />
          <h2 className="mt-6 text-2xl font-bold text-gray-900">Account Pending Approval</h2>
          <p className="mt-2 text-gray-600">
            Your account is waiting for admin approval. You'll receive an email once approved.
          </p>
          
          <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="text-sm text-yellow-800">
              <p className="font-medium">Account Details:</p>
              <p>Name: {user?.name}</p>
              <p>Email: {user?.email}</p>
              <p>Role: {user?.role}</p>
              <p>Status: {user?.approval_status}</p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <button
              onClick={() => window.location.reload()}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Refresh Status
            </button>
            <button
              onClick={() => {
                localStorage.clear();
                window.location.href = '/login';
              }}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;