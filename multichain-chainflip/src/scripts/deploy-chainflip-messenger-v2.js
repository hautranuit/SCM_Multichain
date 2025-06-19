// Deploy Updated ChainFLIP Messenger V2 with LayerZero V2 Fix
// This script deploys the fixed ChainFLIP Messenger contracts across all 4 testnets
// Based on working OFT system patterns

const { ethers } = require("hardhat");

// LayerZero V2 endpoint addresses for testnets
const LAYERZERO_ENDPOINTS = {
    "baseSepolia": "0x6EDCE65403992e310A62460808c4b910D972f10f",
    "optimismSepolia": "0x6EDCE65403992e310A62460808c4b910D972f10f", 
    "arbitrumSepolia": "0x6EDCE65403992e310A62460808c4b910D972f10f",
    "amoy": "0x6EDCE65403992e310A62460808c4b910D972f10f"
};

// LayerZero V2 EIDs for peer connections
const LAYERZERO_EIDS = {
    "baseSepolia": 40245,
    "optimismSepolia": 40232,
    "arbitrumSepolia": 40231,
    "amoy": 40267
};

async function main() {
    console.log("🚀 Deploying ChainFLIP Messenger V2 with LayerZero V2 Fix");
    console.log("🔧 Based on working OFT system patterns");
    
    const [deployer] = await ethers.getSigners();
    const deployerAddress = deployer.address;
    
    console.log(`\n🔑 Deployer account: ${deployerAddress}`);
    console.log(`💰 Balance: ${ethers.utils.formatEther(await deployer.getBalance())} ETH`);
    
    // Detect network
    const network = await ethers.provider.getNetwork();
    const chainId = network.chainId;
    
    let networkName;
    let lzEndpoint;
    
    if (chainId === 84532) {
        networkName = "baseSepolia";
        lzEndpoint = LAYERZERO_ENDPOINTS.baseSepolia;
    } else if (chainId === 11155420) {
        networkName = "optimismSepolia";
        lzEndpoint = LAYERZERO_ENDPOINTS.optimismSepolia;
    } else if (chainId === 421614) {
        networkName = "arbitrumSepolia";
        lzEndpoint = LAYERZERO_ENDPOINTS.arbitrumSepolia;
    } else if (chainId === 80002) {
        networkName = "amoy";
        lzEndpoint = LAYERZERO_ENDPOINTS.amoy;
    } else {
        throw new Error(`❌ Unsupported network. Chain ID: ${chainId}`);
    }
    
    console.log(`\n🌐 Network: ${networkName} (Chain ID: ${chainId})`);
    console.log(`🔗 LayerZero Endpoint: ${lzEndpoint}`);
    console.log(`🆔 LayerZero EID: ${LAYERZERO_EIDS[networkName]}`);
    
    // Deploy ChainFLIP Messenger V2
    console.log(`\n🔨 Deploying ChainFLIPMessengerV2...`);
    
    const ChainFLIPMessengerV2 = await ethers.getContractFactory("ChainFLIPMessengerV2");
    const messenger = await ChainFLIPMessengerV2.deploy(
        lzEndpoint,      // LayerZero endpoint
        deployerAddress  // Owner (deployer)
    );
    
    await messenger.deployed();
    const messengerAddress = messenger.address;
    
    console.log(`   ✅ ChainFLIPMessengerV2 deployed: ${messengerAddress}`);
    console.log(`   👑 Owner: ${deployerAddress}`);
    console.log(`   🔗 LayerZero Endpoint: ${lzEndpoint}`);
    
    // Verify deployment
    try {
        const owner = await messenger.owner();
        const endpoint = await messenger.endpoint();
        const supportedChains = await messenger.getSupportedChains();
        
        console.log(`\n✅ Deployment Verification:`);
        console.log(`   Owner: ${owner}`);
        console.log(`   Endpoint: ${endpoint}`);
        console.log(`   Supported Chain EIDs: [${supportedChains.join(', ')}]`);
        
        // Check if contract can get CID count (basic functionality test)
        const cidCount = await messenger.getCIDCount();
        console.log(`   Initial CID Count: ${cidCount}`);
        
    } catch (error) {
        console.log(`⚠️ Verification failed: ${error.message}`);
    }
    
    // Save deployment info
    const deploymentInfo = {
        timestamp: new Date().toISOString(),
        network: networkName,
        chainId: chainId,
        deployment_type: "ChainFLIP Messenger V2 - LayerZero V2 Fix",
        contract_name: "ChainFLIPMessengerV2",
        deployment_purpose: "Fix LayerZero V2 extraOptions format and peer connections",
        addresses: {
            messenger: messengerAddress,
            layerzero_endpoint: lzEndpoint,
            deployer: deployerAddress
        },
        layerzero: {
            eid: LAYERZERO_EIDS[networkName],
            endpoint: lzEndpoint,
            version: "V2"
        },
        gas_used: {
            messenger: messenger.deployTransaction?.gasLimit?.toString() || "Unknown"
        },
        interface: "LayerZero V2 OApp with Fixed extraOptions Format",
        next_steps: [
            "Deploy on all 4 networks",
            "Set peer connections between all messenger contracts",
            "Update Python service to use new contract addresses",
            "Test cross-chain CID messaging"
        ]
    };
    
    console.log(`\n💾 Deployment Summary:`);
    console.log(JSON.stringify(deploymentInfo, null, 2));
    
    // Write deployment file
    const fs = require('fs');
    const deploymentFile = `deployments/chainflip-messenger-v2-${networkName}-${chainId}.json`;
    
    // Create deployments directory if it doesn't exist
    if (!fs.existsSync('deployments')) {
        fs.mkdirSync('deployments', { recursive: true });
    }
    
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
    console.log(`\n📄 Deployment saved to: ${deploymentFile}`);
    
    console.log(`\n🎯 Next Steps for ${networkName}:`);
    console.log(`   1. Deploy on remaining networks (if not already done)`);
    console.log(`   2. Run peer connection setup script`);
    console.log(`   3. Update backend service with new contract address: ${messengerAddress}`);
    console.log(`   4. Test CID messaging functionality`);
    
    console.log(`\n✅ ChainFLIP Messenger V2 deployment complete on ${networkName}!`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(`❌ Deployment failed: ${error.message}`);
        process.exit(1);
    });
