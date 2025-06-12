// Fresh OFT Contract Deployment - Direct Deployer Ownership
const hre = require("hardhat");
const { ethers } = require("hardhat");

// Networks that need fresh deployment (skip Base Sepolia - already working)
const NETWORKS_TO_DEPLOY = {
    optimismSepolia: {
        eid: 40232,
        endpoint: "0x6EDCE65403992e310A62460808c4b910D972f10f"
    },
    arbitrumSepolia: {
        eid: 40231,
        endpoint: "0x6EDCE65403992e310A62460808c4b910D972f10f"
    },
    amoy: {
        eid: 40267,
        endpoint: "0x6EDCE65403992e310A62460808c4b910D972f10f"
    }
};

async function main() {
    console.log("🚀 Deploying Fresh ChainFlipOFT Contracts");

    const [deployer] = await ethers.getSigners();
    const currentNetwork = hre.network.name;

    console.log(`\n📊 Current Network: ${currentNetwork}`);
    console.log(`   Deployer: ${deployer.address}`);

    // Check if this network needs deployment
    if (!NETWORKS_TO_DEPLOY[currentNetwork]) {
        console.log(`   ℹ️  No deployment needed for ${currentNetwork}`);
        return;
    }

    const networkConfig = NETWORKS_TO_DEPLOY[currentNetwork];
    console.log(`   LayerZero EID: ${networkConfig.eid}`);
    console.log(`   LayerZero Endpoint: ${networkConfig.endpoint}`);

    // Deploy ChainFlipOFT
    console.log(`\n🔨 Deploying ChainFlipOFT contract...`);

    const ChainFlipOFT = await ethers.getContractFactory("ChainFlipOFT");
    const oftContract = await ChainFlipOFT.deploy(
        "ChainFLIP WETH",     // Token name
        "cfWETH",             // Token symbol  
        networkConfig.endpoint, // LayerZero endpoint
        deployer.address      // Owner (deployer)
    );

    await oftContract.deployed();

    console.log(`   ✅ ChainFlipOFT deployed: ${oftContract.address}`);
    console.log(`   📤 Transaction: ${oftContract.deployTransaction.hash}`);

    // Verify ownership
    const owner = await oftContract.owner();
    console.log(`   👤 Contract Owner: ${owner}`);

    if (owner.toLowerCase() === deployer.address.toLowerCase()) {
        console.log(`   ✅ Ownership verified - deployer is owner`);
    } else {
        console.log(`   ❌ Ownership issue - owner is ${owner}`);
    }

    // Save deployment info
    const deploymentInfo = {
        network: currentNetwork,
        chainId: await deployer.provider.getNetwork().then(n => n.chainId),
        deployment_type: "Fresh LayerZero V2 OFT - Direct Ownership",
        contract_name: "ChainFlipOFT",
        deployer: deployer.address,
        oft_contract: oftContract.address,
        layerzero_endpoint: networkConfig.endpoint,
        layerzero_eid: networkConfig.eid,
        token_name: "ChainFLIP WETH",
        token_symbol: "cfWETH",
        deployment_timestamp: new Date().toISOString(),
        transaction_hash: oftContract.deployTransaction.hash,
        owner: owner,
        ownership_verified: owner.toLowerCase() === deployer.address.toLowerCase()
    };

    // Write to deployments folder
    const fs = require('fs');
    const deploymentFile = `./deployments/fresh-layerzero-oft-${currentNetwork}-${deploymentInfo.chainId}.json`;
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));

    console.log(`\n💾 Deployment saved to: ${deploymentFile}`);
    console.log(`\n🎯 Next Steps:`);
    console.log(`   1. Update set-peer-connections-oft.js with new address`);
    console.log(`   2. Run peer setup on this network`);
    console.log(`   3. Test cross-chain transfers`);
}

main().catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exitCode = 1;
});