import React, { useState, useEffect } from 'react';
import { 
  Users, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Building, 
  Truck, 
  ShoppingCart,
  BarChart3,
  Shield,
  UserCheck,
  UserX,
  AlertCircle,
  Wallet
} from 'lucide-react';

const AdminDashboard = ({ authService }) => {
  const [stats, setStats] = useState(null);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const [statsResponse, pendingResponse, allUsersResponse] = await Promise.all([
        authService.getAdminStats(),
        authService.getPendingUsers(),
        authService.getAllUsers()
      ]);

      setStats(statsResponse);
      setPendingUsers(pendingResponse);
      setAllUsers(allUsersResponse);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUserApproval = async (userId, status, adminNotes = '') => {
    try {
      await authService.approveUser(userId, status, adminNotes);
      // Reload data after approval
      await loadDashboardData();
    } catch (error) {
      console.error('Error approving user:', error);
      alert('Error approving user. Please try again.');
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'manufacturer':
        return Building;
      case 'transporter':
        return Truck;
      case 'buyer':
        return ShoppingCart;
      default:
        return Users;
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'manufacturer':
        return 'blue';
      case 'transporter':
        return 'green';
      case 'buyer':
        return 'purple';
      default:
        return 'gray';
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'approved':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="h-3 w-3 mr-1" />
            Approved
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            <XCircle className="h-3 w-3 mr-1" />
            Rejected
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            <Clock className="h-3 w-3 mr-1" />
            Pending
          </span>
        );
      default:
        return status;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
          <p className="mt-4 text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-indigo-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">ChainFLIP Admin Dashboard</h1>
                <p className="text-sm text-gray-600">Multi-Chain User Management</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                {pendingUsers.length} pending approvals
              </span>
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Return to App
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', name: 'Overview', icon: BarChart3 },
              { id: 'pending', name: 'Pending Approvals', icon: Clock },
              { id: 'users', name: 'All Users', icon: Users }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {tab.name}
                  {tab.id === 'pending' && pendingUsers.length > 0 && (
                    <span className="ml-2 bg-red-100 text-red-600 text-xs rounded-full px-2 py-1">
                      {pendingUsers.length}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  title: 'Total Users',
                  value: stats.total_users,
                  icon: Users,
                  color: 'bg-blue-500'
                },
                {
                  title: 'Pending Approvals',
                  value: stats.pending_approvals,
                  icon: Clock,
                  color: 'bg-yellow-500'
                },
                {
                  title: 'Approved Users',
                  value: stats.approved_users,
                  icon: CheckCircle,
                  color: 'bg-green-500'
                },
                {
                  title: 'Rejected Users',
                  value: stats.rejected_users,
                  icon: XCircle,
                  color: 'bg-red-500'
                }
              ].map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <div key={index} className="bg-white overflow-hidden shadow rounded-lg">
                    <div className="p-5">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className={`${stat.color} rounded-md p-3`}>
                            <Icon className="h-6 w-6 text-white" />
                          </div>
                        </div>
                        <div className="ml-5 w-0 flex-1">
                          <dl>
                            <dt className="text-sm font-medium text-gray-500 truncate">
                              {stat.title}
                            </dt>
                            <dd className="text-lg font-medium text-gray-900">
                              {stat.value}
                            </dd>
                          </dl>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {[
                {
                  title: 'Manufacturers',
                  value: stats.manufacturers,
                  icon: Building,
                  description: 'L2 Chain ID: 84532 (Base Sepolia)'
                },
                {
                  title: 'Transporters',
                  value: stats.transporters,
                  icon: Truck,
                  description: 'L2 Chain ID: 421614 (Arbitrum Sepolia)'
                },
                {
                  title: 'Buyers',
                  value: stats.buyers,
                  icon: ShoppingCart,
                  description: 'L2 Chain ID: 11155420 (Optimism Sepolia)'
                }
              ].map((role, index) => {
                const Icon = role.icon;
                return (
                  <div key={index} className="bg-white overflow-hidden shadow rounded-lg">
                    <div className="p-5">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <Icon className="h-8 w-8 text-gray-400" />
                        </div>
                        <div className="ml-5">
                          <h3 className="text-lg font-medium text-gray-900">{role.title}</h3>
                          <p className="text-2xl font-bold text-indigo-600">{role.value}</p>
                          <p className="text-sm text-gray-500">{role.description}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Pending Approvals Tab */}
        {activeTab === 'pending' && (
          <div className="space-y-6">
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Pending User Approvals
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  Review and approve or reject new user registrations.
                </p>
              </div>
              {pendingUsers.length === 0 ? (
                <div className="text-center py-12">
                  <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No pending approvals</h3>
                  <p className="mt-1 text-sm text-gray-500">All users have been processed.</p>
                </div>
              ) : (
                <ul className="divide-y divide-gray-200">
                  {pendingUsers.map((user) => {
                    const RoleIcon = getRoleIcon(user.role);
                    const roleColor = getRoleColor(user.role);
                    return (
                      <li key={user.id} className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className={`flex-shrink-0 h-12 w-12 bg-${roleColor}-100 rounded-lg flex items-center justify-center`}>
                              <RoleIcon className={`h-6 w-6 text-${roleColor}-600`} />
                            </div>
                            <div className="ml-4">
                              <div className="flex items-center">
                                <p className="text-sm font-medium text-gray-900">{user.name}</p>
                                <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${roleColor}-100 text-${roleColor}-800`}>
                                  {user.role}
                                </span>
                              </div>
                              <p className="text-sm text-gray-500">{user.email}</p>
                              <div className="flex items-center text-xs text-gray-400">
                                <Wallet className="h-3 w-3 mr-1" />
                                <span className="font-mono">{user.wallet_address}</span>
                              </div>
                              <p className="text-xs text-gray-400">
                                Registered: {new Date(user.registration_date).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleUserApproval(user.id, 'approved')}
                              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                            >
                              <UserCheck className="h-4 w-4 mr-1" />
                              Approve
                            </button>
                            <button
                              onClick={() => handleUserApproval(user.id, 'rejected')}
                              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                            >
                              <UserX className="h-4 w-4 mr-1" />
                              Reject
                            </button>
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>
        )}

        {/* All Users Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  All Users
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  Complete list of all registered users and their status.
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        L2 Chain
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ethereum Address
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Registration Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {allUsers.map((user) => {
                      const RoleIcon = getRoleIcon(user.role);
                      return (
                        <tr key={user.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 h-10 w-10">
                                <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                                  <span className="text-sm font-medium text-gray-700">
                                    {user.name.charAt(0).toUpperCase()}
                                  </span>
                                </div>
                              </div>
                              <div className="ml-4">
                                <div className="text-sm font-medium text-gray-900">{user.name}</div>
                                <div className="text-sm text-gray-500">{user.email}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <RoleIcon className="h-4 w-4 mr-2 text-gray-400" />
                              <span className="capitalize text-sm text-gray-900">{user.role}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {getStatusBadge(user.approval_status)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {user.role === 'manufacturer' ? '84532 (Base Sepolia)' : 
                             user.role === 'transporter' ? '421614 (Arbitrum Sepolia)' :
                             user.role === 'buyer' ? '11155420 (Optimism Sepolia)' : 'Not assigned'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center text-sm text-gray-900">
                              <Wallet className="h-3 w-3 mr-1 text-gray-400" />
                              <span className="font-mono text-xs">{user.wallet_address}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(user.registration_date).toLocaleDateString()}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;