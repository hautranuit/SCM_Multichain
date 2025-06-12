const hre = require("hardhat");
const { ethers } = require("hardhat");

// Updated LayerZero V2 Endpoints for 2025
const LAYERZERO_ENDPOINTS = {
    optimismSepolia: "0x6EDCE65403992e310A62460808c4b910D972f10f",
    arbitrumSepolia: "0x6EDCE65403992e310A62460808c4b910D972f10f", 
    amoy: "0x6EDCE65403992e310A62460808c4b910D972f10f",
    cardona: "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3"
};

async function main() {
    console.log("🚀 Deploying REAL LayerZero OFT Contract...");

    try {
        // Get deployer from Hardhat's ethers
        const [deployer] = await ethers.getSigners();
        const network = hre.network.name;

        console.log(`Network: ${network}`);
        console.log(`Deployer: ${deployer.address}`);
        
        // Check deployer balance
        const balance = await deployer.getBalance();
        console.log(`Deployer balance: ${ethers.utils.formatEther(balance)} ETH`);

        const lzEndpoint = LAYERZERO_ENDPOINTS[network];
        if (!lzEndpoint) {
            console.log(`❌ Unsupported network: ${network}`);
            return;
        }

        console.log(`LayerZero Endpoint: ${lzEndpoint}`);

        // Verify endpoint exists by checking if it's a contract
        const code = await ethers.provider.getCode(lzEndpoint);
        if (code === "0x") {
            throw new Error(`LayerZero endpoint ${lzEndpoint} is not a contract on ${network}`);
        }
        console.log(`✅ LayerZero endpoint verified`);

        // Get contract factory using Hardhat's ethers
        const RealChainFlipOFT = await ethers.getContractFactory("RealChainFlipOFT");
        
        console.log("📦 Deploying contract...");
        const oft = await RealChainFlipOFT.deploy(
            "ChainFLIP WETH",
            "cfWETH",
            lzEndpoint,
            deployer.address,
            {
                gasLimit: 3000000 // Set explicit gas limit
            }
        );

        console.log("⏳ Waiting for deployment...");
        await oft.deployed();
        
        console.log(`✅ Deployed at: ${oft.address}`);
        console.log(`✅ Real LayerZero OFT with deposit/withdraw functionality!`);
        
        // Save deployment info
        const deploymentInfo = {
            network: network,
            address: oft.address,
            deployer: deployer.address,
            lzEndpoint: lzEndpoint,
            timestamp: new Date().toISOString()
        };
        
        console.log("📄 Deployment Info:", deploymentInfo);
        
    } catch (error) {
        console.error("❌ Deployment failed:", error.message);
        if (error.data) {
            console.error("Error data:", error.data);
        }
        throw error;
    }
}

main().catch(console.error);
