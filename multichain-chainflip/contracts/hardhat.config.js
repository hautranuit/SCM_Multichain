require("@nomicfoundation/hardhat-ethers");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.28",
    settings: {
      optimizer: {
        enabled: true,
        runs: 1000,
      },
      viaIR: true
    },
  },
  paths: {
    sources: "./multichain",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  },
  networks: {
    amoy: {
      url: process.env.POLYGON_AMOY_RPC || "https://polygon-amoy.infura.io/v3/d455e91357464c0cb3727309e4256e94",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 80002,
      gas: 30_000_000,
      maxPriorityFeePerGas: 40000000000,
      maxFeePerGas: 70000000000,
    },
    polygon: {
      url: process.env.POLYGON_MAINNET_RPC || "https://polygon-rpc.com",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 137,
      gas: 30_000_000,
      maxPriorityFeePerGas: 40000000000,
      maxFeePerGas: 100000000000,
    },
    l2cdk: {
      url: process.env.L2_CDK_RPC || "https://rpc.cardona.zkevm-rpc.com",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: 2442,
      gas: 30_000_000,
      maxPriorityFeePerGas: 40000000000,
      maxFeePerGas: 70000000000,
    }
  },
  mocha: {
    timeout: 600000
  }
};