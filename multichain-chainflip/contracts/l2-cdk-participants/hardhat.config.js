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
    l2cdk: {
      url: process.env.L2_CDK_RPC || "http://localhost:8545",
      accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
      chainId: process.env.L2_CDK_CHAIN_ID || 1001,
      gas: 30_000_000,
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337
    }
  },
  mocha: {
    timeout: 600000
  }
};
