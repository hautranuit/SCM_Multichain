class AuthService {
  constructor() {
    this.baseURL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    this.token = localStorage.getItem('authToken');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}/api/auth${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    if (this.token && !options.skipAuth) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('Auth request failed:', error);
      throw error;
    }
  }

  async register(userData) {
    try {
      const response = await this.request('/register', {
        method: 'POST',
        body: JSON.stringify(userData),
        skipAuth: true,
      });
      return response;
    } catch (error) {
      throw new Error(error.message || 'Registration failed');
    }
  }

  async login(credentials) {
    try {
      const response = await this.request('/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
        skipAuth: true,
      });

      if (response.access_token) {
        this.token = response.access_token;
        localStorage.setItem('authToken', this.token);
        localStorage.setItem('user', JSON.stringify(response.user));
      }

      return response;
    } catch (error) {
      throw new Error(error.message || 'Login failed');
    }
  }

  async logout() {
    try {
      await this.request('/logout', {
        method: 'POST',
      });
    } catch (error) {
      console.error('Logout request failed:', error);
    } finally {
      this.token = null;
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
    }
  }

  async getCurrentUser() {
    try {
      const response = await this.request('/me');
      return response;
    } catch (error) {
      // If token is invalid, clear it
      this.logout();
      throw error;
    }
  }

  async getPendingUsers() {
    try {
      const response = await this.request('/admin/pending-users');
      return response;
    } catch (error) {
      throw new Error(error.message || 'Failed to get pending users');
    }
  }

  async getAllUsers() {
    try {
      const response = await this.request('/admin/all-users');
      return response;
    } catch (error) {
      throw new Error(error.message || 'Failed to get all users');
    }
  }

  async getAdminStats() {
    try {
      const response = await this.request('/admin/stats');
      return response;
    } catch (error) {
      throw new Error(error.message || 'Failed to get admin stats');
    }
  }

  async approveUser(userId, approvalStatus, adminNotes = '') {
    try {
      const response = await this.request('/admin/approve-user', {
        method: 'POST',
        body: JSON.stringify({
          user_id: userId,
          approval_status: approvalStatus,
          admin_notes: adminNotes,
        }),
      });
      return response;
    } catch (error) {
      throw new Error(error.message || 'Failed to approve user');
    }
  }

  async initializeAdmin() {
    try {
      const response = await this.request('/admin/initialize', {
        skipAuth: true,
      });
      return response;
    } catch (error) {
      throw new Error(error.message || 'Failed to initialize admin');
    }
  }

  isAuthenticated() {
    return !!this.token;
  }

  getCurrentUserFromStorage() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  getToken() {
    return this.token;
  }

  isAdmin() {
    const user = this.getCurrentUserFromStorage();
    return user && user.role === 'admin';
  }

  isApproved() {
    const user = this.getCurrentUserFromStorage();
    return user && user.approval_status === 'approved';
  }

  getUserRole() {
    const user = this.getCurrentUserFromStorage();
    return user ? user.role : null;
  }

  getL2Blockchain() {
    const user = this.getCurrentUserFromStorage();
    return user ? user.l2_blockchain_assigned : null;
  }
}

export default new AuthService();