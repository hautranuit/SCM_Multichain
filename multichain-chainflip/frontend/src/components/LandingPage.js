import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const LandingPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalTransactions: 0,
    activeUsers: 0
  });

  useEffect(() => {
    // Load platform statistics
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/network-status`);
      if (response.data.success) {
        setStats({
          totalProducts: response.data.multichain?.statistics?.total_products || 0,
          totalTransactions: response.data.multichain?.statistics?.total_transactions || 0,
          activeUsers: 1250 // Mock data for demo
        });
      }
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const features = [
    {
      title: "Unmatched Blockchain Expertise",
      description: "Work with experts who go further, no matter what, and know more than anyone else about logistics for your industry, business, and customers.",
      image: "https://images.unsplash.com/photo-1639322537228-f710d846310a"
    },
    {
      title: "Unrivaled Scale",
      description: "We get you anywhere you need to go—even when others can't—with the full power of our connections, relationships, and global reach.",
      image: "https://images.unsplash.com/photo-1624927637280-f033784c1279"
    },
    {
      title: "Tailored Solutions", 
      description: "Unlock solutions designed for your business through integrated, multimodal services and advanced blockchain technology capabilities.",
      image: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5"
    }
  ];

  const systemFeatures = [
    {
      title: "Smart Payment System",
      description: "Automated escrow payments with performance-based incentives for transporters",
      number: "01"
    },
    {
      title: "Dispute Resolution",
      description: "Decentralized consensus voting mechanism for fair conflict resolution",
      number: "02"
    },
    {
      title: "Supply Chain Coordination",
      description: "Cross-chain coordination for seamless multi-network operations",
      number: "03"
    },
    {
      title: "Enhanced Verification",
      description: "Advanced product verification with batch processing and analytics",
      number: "04"
    },
    {
      title: "Marketplace Platform",
      description: "Secondary marketplace for verified products with secure ownership transfers",
      number: "05"
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="text-2xl font-bold text-blue-600">
                ChainFLIP
              </div>
              <div className="hidden md:flex space-x-8 ml-8">
                <a href="#services" className="text-gray-700 hover:text-blue-600 font-medium">Services</a>
                <a href="#capabilities" className="text-gray-700 hover:text-blue-600 font-medium">Capabilities</a>
                <a href="#technology" className="text-gray-700 hover:text-blue-600 font-medium">Technology</a>
                <a href="#resources" className="text-gray-700 hover:text-blue-600 font-medium">Resources</a>
                <a href="#about" className="text-gray-700 hover:text-blue-600 font-medium">About</a>
                <a href="#contact" className="text-gray-700 hover:text-blue-600 font-medium">Contact</a>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => navigate('/login')}
                className="text-gray-700 hover:text-blue-600 font-medium"
              >
                Get a quote
              </button>
              <button 
                onClick={() => navigate('/login')}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-medium"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center bg-gradient-to-r from-blue-900 to-blue-600">
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{
            backgroundImage: `linear-gradient(rgba(30, 64, 175, 0.8), rgba(37, 99, 235, 0.8)), url('https://images.unsplash.com/photo-1695222833131-54ee679ae8e5')`
          }}
        />
        
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
            Blockchain
            <br />
            <span className="text-cyan-300">Like No One Else</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-blue-100 mb-8 max-w-3xl mx-auto">
            Revolutionary multi-chain supply chain management powered by 5 sophisticated AI systems
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <button 
              onClick={() => navigate('/register')}
              className="bg-cyan-400 text-blue-900 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-cyan-300 transition-colors"
            >
              Ship with us
            </button>
            <button 
              onClick={() => navigate('/login')}
              className="border-2 border-white text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white hover:text-blue-900 transition-colors"
            >
              Mail with us
            </button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-cyan-300 mb-2">{stats.totalProducts}+</div>
              <div className="text-blue-100">Products Tracked</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-cyan-300 mb-2">{stats.totalTransactions}+</div>
              <div className="text-blue-100">Transactions</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-cyan-300 mb-2">{stats.activeUsers}+</div>
              <div className="text-blue-100">Active Users</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-cyan-300 mb-2">5</div>
              <div className="text-blue-100">AI Systems</div>
            </div>
          </div>
        </div>

        {/* Floating Action Cards */}
        <div className="absolute bottom-8 left-8 right-8 z-10">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white/95 backdrop-blur rounded-lg p-6 hover:shadow-xl transition-shadow cursor-pointer">
                <h3 className="font-semibold text-gray-800 mb-2">Your source for supply chain news and updates</h3>
                <button className="text-blue-600 hover:text-blue-800 font-medium text-sm">
                  Explore more →
                </button>
              </div>
              <div className="bg-white/95 backdrop-blur rounded-lg p-6 hover:shadow-xl transition-shadow cursor-pointer">
                <h3 className="font-semibold text-gray-800 mb-2">Gartner recognizes our TMS platform in their report</h3>
                <button className="text-blue-600 hover:text-blue-800 font-medium text-sm">
                  Access report →
                </button>
              </div>
              <div className="bg-white/95 backdrop-blur rounded-lg p-6 hover:shadow-xl transition-shadow cursor-pointer">
                <h3 className="font-semibold text-gray-800 mb-2">See market trends that are impacting your supply chain</h3>
                <button className="text-blue-600 hover:text-blue-800 font-medium text-sm">
                  Get the latest →
                </button>
              </div>
              <div className="bg-white/95 backdrop-blur rounded-lg p-6 hover:shadow-xl transition-shadow cursor-pointer">
                <h3 className="font-semibold text-gray-800 mb-2">Carriers, fuel your business and get paid in minutes</h3>
                <button 
                  onClick={() => navigate('/register')}
                  className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                >
                  Get started →
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Value Proposition Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                We deliver success through{' '}
                <span className="text-blue-600">exceptional service</span>{' '}
                and high value
                <br />
                <span className="text-gray-700">—like no one else</span>
              </h2>
            </div>
            
            <div className="space-y-8">
              {features.map((feature, index) => (
                <div key={index} className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                    <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section id="technology" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              5 Sophisticated <span className="text-blue-600">AI Systems</span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our platform is powered by cutting-edge artificial intelligence systems that revolutionize supply chain management
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {systemFeatures.map((feature, index) => (
              <div key={index} className="group relative bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-8 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="absolute top-6 right-6 text-6xl font-bold text-blue-100 group-hover:text-blue-200 transition-colors">
                  {feature.number}
                </div>
                <div className="relative">
                  <h3 className="text-xl font-bold text-gray-900 mb-4 group-hover:text-blue-600 transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to revolutionize your supply chain?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto">
            Join thousands of companies already using our blockchain-powered platform to transform their logistics operations.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={() => navigate('/register')}
              className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Get Started Today
            </button>
            <button 
              onClick={() => navigate('/login')}
              className="border-2 border-white text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors"
            >
              Schedule Demo
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <div className="text-2xl font-bold text-blue-400 mb-4">ChainFLIP</div>
              <p className="text-gray-400 mb-4 max-w-md">
                Revolutionary blockchain-powered supply chain management platform with 5 AI systems for unmatched efficiency and transparency.
              </p>
              <div className="flex space-x-4">
                <button className="text-gray-400 hover:text-white">LinkedIn</button>
                <button className="text-gray-400 hover:text-white">Twitter</button>
                <button className="text-gray-400 hover:text-white">GitHub</button>
              </div>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Platform</h3>
              <ul className="space-y-2 text-gray-400">
                <li><button onClick={() => navigate('/login')} className="hover:text-white">Dashboard</button></li>
                <li><button onClick={() => navigate('/register')} className="hover:text-white">Get Started</button></li>
                <li><a href="#technology" className="hover:text-white">Technology</a></li>
                <li><a href="#" className="hover:text-white">API Documentation</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Help Center</a></li>
                <li><a href="#contact" className="hover:text-white">Contact Us</a></li>
                <li><a href="#" className="hover:text-white">Status</a></li>
                <li><a href="#" className="hover:text-white">Security</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 ChainFLIP. All rights reserved. Blockchain supply chain management platform.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;