import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';

export const Sidebar = () => {
  const location = useLocation();

  const navigation = [
    {
      name: 'Dashboard',
      href: '/',
      icon: '📊',
      description: 'Overview and analytics'
    },
    {
      name: 'Products',
      href: '/products',
      icon: '📦',
      description: 'Product management'
    },
    {
      name: 'Participants',
      href: '/participants',
      icon: '👥',
      description: 'Network participants'
    },
    {
      name: 'Federated Learning',
      href: '/federated-learning',
      icon: '🤖',
      description: 'AI model training'
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: '📈',
      description: 'Performance metrics'
    },
    {
      name: 'QR Scanner',
      href: '/qr-scanner',
      icon: '📱',
      description: 'Scan product QR codes'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: '⚙️',
      description: 'System configuration'
    }
  ];

  return (
    <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-gray-900">
      <div className="flex h-full flex-col">
        {/* Sidebar Header */}
        <div className="flex h-16 shrink-0 items-center px-6 bg-gray-800">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">CF</span>
            </div>
            <div>
              <div className="text-white font-semibold text-sm">ChainFLIP</div>
              <div className="text-gray-400 text-xs">Multi-Chain</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-1 flex-col px-6 py-4">
          <ul role="list" className="flex flex-1 flex-col gap-y-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                (item.href !== '/' && location.pathname.startsWith(item.href));
              
              return (
                <li key={item.name}>
                  <NavLink
                    to={item.href}
                    className={`group flex gap-x-3 rounded-md p-3 text-sm leading-6 font-medium transition-colors duration-200 ${
                      isActive
                        ? 'bg-primary-600 text-white'
                        : 'text-gray-300 hover:text-white hover:bg-gray-800'
                    }`}
                  >
                    <span className="text-lg">{item.icon}</span>
                    <div className="flex flex-col">
                      <span>{item.name}</span>
                      <span className={`text-xs ${isActive ? 'text-primary-100' : 'text-gray-500'}`}>
                        {item.description}
                      </span>
                    </div>
                  </NavLink>
                </li>
              );
            })}
          </ul>

          {/* Footer */}
          <div className="mt-auto pt-4 border-t border-gray-700">
            <div className="flex items-center space-x-2 text-gray-400 text-xs">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>System Online</span>
            </div>
          </div>
        </nav>
      </div>
    </aside>
  );
};
