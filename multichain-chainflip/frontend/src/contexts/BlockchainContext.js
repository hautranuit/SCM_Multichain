import React, { createContext, useContext, useState, useEffect } from 'react';
import { ethers } from 'ethers';

const BlockchainContext = createContext();

export const useBlockchain = () => {
  const context = useContext(BlockchainContext);
  if (!context) {
    throw new Error('useBlockchain must be used within a BlockchainProvider');
  }
  return context;
};

export const BlockchainProvider = ({ children }) => {
  const [account, setAccount] = useState(null);
  const [provider, setProvider] = useState(null);
  const [signer, setSigner] = useState(null);
  const [chainId, setChainId] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [networkStatus, setNetworkStatus] = useState({
    polygonPos: { connected: false, chainId: 80002 },
    l2Cdk: { connected: false, chainId: 1001 }
  });

  // Check if MetaMask is installed
  const isMetaMaskInstalled = () => {
    return typeof window !== 'undefined' && typeof window.ethereum !== 'undefined';
  };

  // Connect to MetaMask
  const connectWallet = async () => {
    if (!isMetaMaskInstalled()) {
      alert('Please install MetaMask to use this application');
      return;
    }

    try {
      setIsConnecting(true);
      
      // Request account access
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts',
      });

      if (accounts.length > 0) {
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();
        const network = await provider.getNetwork();

        setAccount(accounts[0]);
        setProvider(provider);
        setSigner(signer);
        setChainId(Number(network.chainId));
        setIsConnected(true);
        
        // Check network status
        await checkNetworkStatus();
      }
    } catch (error) {
      console.error('Failed to connect wallet:', error);
      alert('Failed to connect wallet. Please try again.');
    } finally {
      setIsConnecting(false);
    }
  };

  // Disconnect wallet
  const disconnectWallet = () => {
    setAccount(null);
    setProvider(null);
    setSigner(null);
    setChainId(null);
    setIsConnected(false);
  };

  // Switch to Polygon network
  const switchToPolygon = async () => {
    if (!isMetaMaskInstalled()) return;

    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: '0x13882' }], // Polygon Amoy testnet
      });
    } catch (switchError) {
      // If network doesn't exist, add it
      if (switchError.code === 4902) {
        try {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [
              {
                chainId: '0x13882',
                chainName: 'Polygon Amoy Testnet',
                nativeCurrency: {
                  name: 'MATIC',
                  symbol: 'MATIC',
                  decimals: 18,
                },
                rpcUrls: ['https://polygon-amoy.drpc.org'],
                blockExplorerUrls: ['https://amoy.polygonscan.com/'],
              },
            ],
          });
        } catch (addError) {
          console.error('Failed to add Polygon network:', addError);
        }
      } else {
        console.error('Failed to switch to Polygon network:', switchError);
      }
    }
  };

  // Check network connectivity status
  const checkNetworkStatus = async () => {
    try {
      // Check Polygon PoS connectivity
      const polygonProvider = new ethers.JsonRpcProvider(process.env.REACT_APP_POLYGON_RPC);
      const polygonNetwork = await polygonProvider.getNetwork();
      
      // Check L2 CDK connectivity (if configured)
      let l2Status = { connected: false, chainId: 1001 };
      if (process.env.REACT_APP_L2_CDK_RPC) {
        try {
          const l2Provider = new ethers.JsonRpcProvider(process.env.REACT_APP_L2_CDK_RPC);
          const l2Network = await l2Provider.getNetwork();
          l2Status = { connected: true, chainId: Number(l2Network.chainId) };
        } catch (error) {
          console.warn('L2 CDK network not available:', error);
        }
      }

      setNetworkStatus({
        polygonPos: { 
          connected: true, 
          chainId: Number(polygonNetwork.chainId) 
        },
        l2Cdk: l2Status
      });
    } catch (error) {
      console.error('Failed to check network status:', error);
      setNetworkStatus({
        polygonPos: { connected: false, chainId: 80002 },
        l2Cdk: { connected: false, chainId: 1001 }
      });
    }
  };

  // Listen for account changes
  useEffect(() => {
    if (isMetaMaskInstalled()) {
      const handleAccountsChanged = (accounts) => {
        if (accounts.length === 0) {
          disconnectWallet();
        } else if (accounts[0] !== account) {
          setAccount(accounts[0]);
        }
      };

      const handleChainChanged = (chainId) => {
        setChainId(parseInt(chainId, 16));
        window.location.reload(); // Reload to reset state
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);

      // Check if already connected
      window.ethereum.request({ method: 'eth_accounts' })
        .then(accounts => {
          if (accounts.length > 0) {
            connectWallet();
          }
        });

      return () => {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
        window.ethereum.removeListener('chainChanged', handleChainChanged);
      };
    }
  }, [account]);

  // Check network status periodically
  useEffect(() => {
    checkNetworkStatus();
    const interval = setInterval(checkNetworkStatus, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const value = {
    account,
    provider,
    signer,
    chainId,
    isConnected,
    isConnecting,
    networkStatus,
    connectWallet,
    disconnectWallet,
    switchToPolygon,
    checkNetworkStatus,
    isMetaMaskInstalled,
  };

  return (
    <BlockchainContext.Provider value={value}>
      {children}
    </BlockchainContext.Provider>
  );
};
