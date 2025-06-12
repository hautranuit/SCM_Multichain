require("@nomicfoundation/hardhat-toolbox");
require("@layerzero-devs/hardhat-lz-oapp");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.28",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      viaIR: true
    },
  },
  networks: {
    // === POLYGON ECOSYSTEM ===
    
    // Polygon Amoy Testnet (Hub)
    amoy: {
      url: process.env.POLYGON_AMOY_RPC || "https://polygon-amoy.drpc.org",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 80002,
      gas: 30_000_000,
      maxPriorityFeePerGas: 40000000000,
      maxFeePerGas: 70000000000,
    },
    
    // Polygon Mainnet (Production Hub)
    polygon: {
      url: process.env.POLYGON_MAINNET_RPC || "https://polygon-rpc.com",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 137,
      gas: 30_000_000,
      maxPriorityFeePerGas: 40000000000,
      maxFeePerGas: 100000000000,
    },

    // Polygon CDK Cardona Testnet (Manufacturer L2)
    cardona: {
      url: process.env.L2_CDK_RPC || "https://rpc.cardona.zkevm-rpc.com",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 2442,
      gas: 30_000_000,
      maxPriorityFeePerGas: 40000000000,
      maxFeePerGas: 70000000000,
    },

    // === ARBITRUM ECOSYSTEM ===
    
    // Arbitrum Sepolia Testnet (Transporter L2)
    arbitrumSepolia: {
      url: process.env.ARBITRUM_SEPOLIA_RPC || "https://sepolia-rollup.arbitrum.io/rpc",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 421614,
      gas: 30_000_000,
      maxPriorityFeePerGas: 1000000000,  // 1 gwei
      maxFeePerGas: 10000000000,         // 10 gwei
      gasPrice: "auto",
      // LayerZero V2 Configuration
      lz: {
        eid: 40231  // Official LayerZero V2 EID for Arbitrum Sepolia
      }
    },

    // Arbitrum One Mainnet (Production)
    arbitrumOne: {
      url: process.env.ARBITRUM_ONE_RPC || "https://arb1.arbitrum.io/rpc",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 42161,
      gas: 30_000_000,
      maxPriorityFeePerGas: 1000000000,
      maxFeePerGas: 10000000000,
    },

    // === OPTIMISM ECOSYSTEM ===
    
    // Optimism Sepolia Testnet (Buyer L2)
    optimismSepolia: {
      url: process.env.OPTIMISM_SEPOLIA_RPC || "https://sepolia.optimism.io",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 11155420,
      gas: 30_000_000,
      maxPriorityFeePerGas: 1000000000,  // 1 gwei
      maxFeePerGas: 10000000000,         // 10 gwei
      gasPrice: "auto",
      // LayerZero V2 Configuration
      lz: {
        eid: 40232  // Official LayerZero V2 EID for Optimism Sepolia
      }
    },

    // Optimism Mainnet (Production)
    optimismMainnet: {
      url: process.env.OPTIMISM_MAINNET_RPC || "https://mainnet.optimism.io",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 10,
      gas: 30_000_000,
      maxPriorityFeePerGas: 1000000000,
      maxFeePerGas: 10000000000,
    },

    // === LOCAL DEVELOPMENT NETWORKS ===
    
    // Local Manufacturer Chain (L2)
    manufacturer: {
      url: process.env.MANUFACTURER_RPC || "http://localhost:8545",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 2001,
      gas: 30_000_000,
    },

    // Local Transporter Chain (L2)
    transporter: {
      url: process.env.TRANSPORTER_RPC || "http://localhost:8546",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 2002,
      gas: 30_000_000,
    },

    // Local Buyer Chain (L2)
    buyer: {
      url: process.env.BUYER_RPC || "http://localhost:8547",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 2003,
      gas: 30_000_000,
    },

    // Hardhat local network
    hardhat: {
      chainId: 31337,
      gas: 30_000_000,
      accounts: {
        count: 20,
        accountsBalance: "10000000000000000000000" // 10000 ETH
      }
    },

    // Localhost for testing
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    }
  },
  
  mocha: {
    timeout: 600000
  },

  paths: {
    sources: "./contracts",
    tests: "./tests",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};
