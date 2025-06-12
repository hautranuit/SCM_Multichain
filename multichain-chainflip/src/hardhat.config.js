require("dotenv").config();

module.exports = {
    solidity: {
        version: "0.8.22",
        settings: {
            optimizer: {
                enabled: true,
                runs: 200,
            },
        },
    },
    networks: {
        amoy: {
            url: process.env.POLYGON_AMOY_RPC || "https://polygon-amoy.drpc.org",
            accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
            chainId: 80002,
        },
        cardona: {
            url: process.env.L2_CDK_RPC || "https://rpc.cardona.zkevm-rpc.com",
            accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
            chainId: 2442,
        },
        arbitrumSepolia: {
            url: process.env.ARBITRUM_SEPOLIA_RPC || "https://sepolia-rollup.arbitrum.io/rpc",
            accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
            chainId: 421614,
        },
        optimismSepolia: {
            url: process.env.OPTIMISM_SEPOLIA_RPC || "https://sepolia.optimism.io",
            accounts: process.env.PRIVATE_KEYS ? process.env.PRIVATE_KEYS.split(",").map(key => `0x${key.trim()}`) : [],
            chainId: 11155420,
        },
    },
};