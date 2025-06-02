require("@nomicfoundation/hardhat-toolbox");
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

    // Polygon CDK Cardona Testnet (L2 Chains)
    cardona: {
      url: process.env.L2_CDK_RPC || "https://rpc.cardona.zkevm-rpc.com",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 2442,
      gas: 30_000_000,
      maxPriorityFeePerGas: 40000000000,
      maxFeePerGas: 70000000000,
    },

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