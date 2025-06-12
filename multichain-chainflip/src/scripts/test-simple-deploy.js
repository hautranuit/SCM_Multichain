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
    console.log("🧪 Testing SIMPLE LayerZero OFT Contract...");

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
        
        console.log("📦 Deploying simplified contract...");
        console.log(`Parameters:`);
        console.log(`- Name: "Test cfWETH"`);
        console.log(`- Symbol: "tcfWETH"`);
        console.log(`- LZ Endpoint: ${lzEndpoint}`);
        console.log(`- Delegate: ${deployer.address}`);

        const oft = await RealChainFlipOFT.deploy(
            "Test cfWETH",
            "tcfWETH",
            lzEndpoint,
            deployer.address,
            {
                gasLimit: 5000000 // Increase gas limit
            }
        );

        console.log("⏳ Waiting for deployment...");
        await oft.deployed();
        
        console.log(`✅ Deployed at: ${oft.address}`);
        console.log(`✅ Simple LayerZero OFT deployment successful!`);
        
        // Test basic functionality
        console.log("🔍 Testing basic functions...");
        
        const name = await oft.name();
        const symbol = await oft.symbol();
        const owner = await oft.owner();
        
        console.log(`- Name: ${name}`);
        console.log(`- Symbol: ${symbol}`);
        console.log(`- Owner: ${owner}`);
        
        // Save deployment info
        const deploymentInfo = {
            network: network,
            address: oft.address,
            deployer: deployer.address,
            lzEndpoint: lzEndpoint,
            name: name,
            symbol: symbol,
            owner: owner,
            timestamp: new Date().toISOString()
        };
        
        console.log("📄 Deployment Info:", deploymentInfo);
        
    } catch (error) {
        console.error("❌ Deployment failed:", error.message);
        if (error.data) {
            console.error("Error data:", error.data);
        }
        if (error.receipt) {
            console.error("Receipt status:", error.receipt.status);
            console.error("Gas used:", error.receipt.gasUsed.toString());
        }
        throw error;
    }
}

main().catch(console.error);