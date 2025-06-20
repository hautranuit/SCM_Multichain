const { ethers, network } = require("hardhat");
const fs = require('fs');
const path = require('path');

// Multi-network deployment configuration
const NETWORKS = {
    baseSepolia: {
        name: "Base Sepolia",
        chainId: 84532,
        envKey: "NFT_CONTRACT_BASE_SEPOLIA"
    },
    optimismSepolia: {
        name: "OP Sepolia", 
        chainId: 11155420,
        envKey: "NFT_CONTRACT_OP_SEPOLIA"
    },
    arbitrumSepolia: {
        name: "Arbitrum Sepolia",
        chainId: 421614, 
        envKey: "NFT_CONTRACT_ARBITRUM_SEPOLIA"
    },
    amoy: {
        name: "Polygon Amoy",
        chainId: 80002,
        envKey: "NFT_CONTRACT_POLYGON_AMOY"
    }
};

async function deployToNetwork(networkName) {
    console.log(`\n🚀 Deploying ChainFLIP Product NFT Contract to ${NETWORKS[networkName].name}...`);
    
    const [deployer] = await ethers.getSigners();
    console.log("📝 Deploying with account:", deployer.address);
    
    const balance = await deployer.getBalance();
    console.log("💰 Account balance:", ethers.utils.formatEther(balance), "ETH");
    
    if (balance.eq(0)) {
        throw new Error("❌ Deployer account has no ETH for gas fees");
    }

    // Contract constructor parameters
    const contractName = "ChainFLIP Product NFT";
    const contractSymbol = "CFPNFT";
    const initialOwner = deployer.address;

    console.log("\n📋 Deployment Parameters:");
    console.log("Contract Name:", contractName);
    console.log("Contract Symbol:", contractSymbol);
    console.log("Initial Owner:", initialOwner);
    console.log("Network:", network.name);
    console.log("Chain ID:", network.config.chainId);
    console.log("Expected Chain ID:", NETWORKS[networkName].chainId);

    // Verify we're on the correct network
    if (network.config.chainId !== NETWORKS[networkName].chainId) {
        throw new Error(`❌ Chain ID mismatch. Expected ${NETWORKS[networkName].chainId}, got ${network.config.chainId}`);
    }

    // Deploy ChainFLIPProductNFT
    console.log("\n🔨 Compiling and deploying contract...");
    const ChainFLIPProductNFT = await ethers.getContractFactory("ChainFLIPProductNFT");
    
    console.log("⏳ Deploying contract...");
    const nftContract = await ChainFLIPProductNFT.deploy(
        contractName,
        contractSymbol,
        initialOwner
    );

    console.log("⏳ Waiting for deployment confirmation...");
    await nftContract.deployed();

    const contractAddress = nftContract.address;
    const deployTx = nftContract.deployTransaction;
    
    console.log("🎉 Contract deployed successfully!");
    console.log("📍 Contract address:", contractAddress);
    console.log("🧾 Transaction hash:", deployTx?.hash || "N/A");
    
    // Wait for additional confirmations
    console.log("⏳ Waiting for additional confirmations...");
    const receipt = await deployTx.wait(2); // Wait for 2 confirmations
    
    console.log("📦 Block number:", receipt.blockNumber);
    console.log("⛽ Gas used:", receipt.gasUsed.toString());

    // Verify the contract is working
    console.log("\n🔍 Verifying contract deployment...");
    try {
        const name = await nftContract.name();
        const symbol = await nftContract.symbol();
        const version = await nftContract.VERSION();
        const owner = await nftContract.owner();
        
        console.log("✅ Contract verification successful:");
        console.log("   Name:", name);
        console.log("   Symbol:", symbol);
        console.log("   Version:", version);
        console.log("   Owner:", owner);
        
        // Test minter role
        const MINTER_ROLE = await nftContract.MINTER_ROLE();
        const hasMinterRole = await nftContract.hasRole(MINTER_ROLE, deployer.address);
        console.log("   Deployer has Minter Role:", hasMinterRole);
        
    } catch (error) {
        console.log("⚠️ Contract verification failed:", error.message);
    }

    // Save deployment information
    const deploymentInfo = {
        contractName: "ChainFLIPProductNFT",
        contractAddress: contractAddress,
        transactionHash: deployTx?.hash,
        blockNumber: receipt.blockNumber,
        gasUsed: receipt.gasUsed.toString(),
        deployer: deployer.address,
        network: network.name,
        chainId: network.config.chainId,
        deploymentTimestamp: Math.floor(Date.now() / 1000),
        contractVersion: await nftContract.VERSION().catch(() => "1.0.0"),
        constructorParams: {
            name: contractName,
            symbol: contractSymbol,
            initialOwner: initialOwner
        }
    };

    // Save to JSON file
    const deploymentDir = path.join(__dirname, '../../backend');
    const deploymentFile = path.join(deploymentDir, 'nft_deployment.json');
    
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
    console.log("💾 Deployment info saved to:", deploymentFile);

    // Generate .env update instructions
    console.log("\n📝 Environment Variable Update Required:");
    console.log("=".repeat(60));
    console.log("Add this to your .env file:");
    console.log(`NFT_CORE_CONTRACT=${contractAddress}`);
    console.log("=".repeat(60));

    console.log("\n📋 Deployment Summary:");
    console.log("=".repeat(50));
    console.log("✅ Contract Address:", contractAddress);
    console.log("✅ Deployer:", deployer.address);
    console.log("✅ Network:", network.name);
    console.log("✅ Chain ID:", network.config.chainId);
    console.log("✅ Transaction Hash:", deployTx?.hash);
    console.log("✅ Block Number:", receipt.blockNumber);
    console.log("✅ Gas Used:", receipt.gasUsed.toString());
    console.log("=".repeat(50));

    return {
        success: true,
        contractAddress: contractAddress,
        transactionHash: deployTx?.hash,
        deploymentInfo: deploymentInfo
    };
}

async function main() {
    console.log("🚀 Deploying ChainFLIP Product NFT Contract...");
    
    // Detect current network (similar to chainflip-messenger-v2.js)
    const network = await ethers.provider.getNetwork();
    const chainId = network.chainId;
    
    let networkName;
    if (chainId === 84532) {
        networkName = "baseSepolia";
    } else if (chainId === 11155420) {
        networkName = "optimismSepolia";
    } else if (chainId === 421614) {
        networkName = "arbitrumSepolia";
    } else if (chainId === 80002) {
        networkName = "amoy";
    } else {
        throw new Error(`❌ Unsupported network. Chain ID: ${chainId}`);
    }
    
    console.log(`🌐 Target Network: ${NETWORKS[networkName].name} (Chain ID: ${chainId})`);
    
    // Deploy to current network only
    const result = await deployToNetwork(networkName);
    
    console.log("\n🏁 Deployment completed successfully!");
    return result;
}

// Export functions for use in other scripts
module.exports = { main, deployToNetwork };

// Run the deployment if this script is executed directly
if (require.main === module) {
    main()
        .then(() => {
            console.log("\n🏁 Deployment completed!");
            process.exit(0);
        })
        .catch((error) => {
            console.error("\n❌ Deployment failed:", error);
            process.exit(1);
        });
}