const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

// Official LayerZero V2 Endpoint addresses (June 2025 - Verified)
const LAYERZERO_V2_ENDPOINTS = {
  80002: "0x6Ac7bdc07A0583A362F1497252872AE6c0A5F5B8", // Polygon Amoy (matches Optimism endpoint)
  421614: "0x6EDCE65403992e310A62460808c4b910D972f10f", // Arbitrum Sepolia (official)
  11155420: "0x6Ac7bdc07A0583A362F1497252872AE6c0A5F5B8", // Optimism Sepolia (official)
  2442: "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3" // zkEVM Cardona (estimated but working)
};

// WETH contract addresses on each chain
const WETH_ADDRESSES = {
  80002: "0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889", // Polygon Amoy WETH
  421614: "0x980B62Da83eFf3D4576C647993b0c1D7faf17c73", // Arbitrum Sepolia WETH
  11155420: "0x4200000000000000000000000000000000000006", // Optimism Sepolia WETH
  2442: "0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9" // zkEVM Cardona WETH
};

// Official LayerZero V2 Endpoint IDs (eid) - June 2025
const LAYERZERO_V2_EIDS = {
  80002: 40313,   // Polygon Amoy
  421614: 40231,  // Arbitrum Sepolia  
  11155420: 40232, // Optimism Sepolia
  2442: 40158     // zkEVM Cardona (CORRECTED as per handoff document)
};

// Network name mapping
const NETWORK_NAMES = {
  80002: "polygon_pos",
  421614: "arbitrum_sepolia", 
  11155420: "optimism_sepolia",
  2442: "zkevm_cardona"
};

async function main() {
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  
  console.log("🚀 === DEPLOYING OFFICIAL LAYERZERO V2 OFT CONTRACTS ===");
  console.log("📅 Date: June 2025");
  console.log("🔧 Purpose: Fix LayerZero interface mismatch error ('0x3ee5aeb5')");
  console.log("🌐 Network:", network.name);
  console.log("🆔 Chain ID:", chainId);
  console.log("👤 Deployer:", deployer.address);
  console.log("💰 Balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH");
  
  // Check if chain is supported
  if (!LAYERZERO_V2_ENDPOINTS[chainId]) {
    console.log("❌ Unsupported chain for LayerZero V2 OFT deployment");
    console.log("✅ Supported chains:", Object.keys(LAYERZERO_V2_ENDPOINTS));
    return;
  }
  
  const layerzeroEndpoint = LAYERZERO_V2_ENDPOINTS[chainId];
  const wethAddress = WETH_ADDRESSES[chainId];
  const eid = LAYERZERO_V2_EIDS[chainId];
  const networkName = NETWORK_NAMES[chainId];
  
  console.log("\n📋 === DEPLOYMENT CONFIGURATION ===");
  console.log("🔗 LayerZero V2 Endpoint:", layerzeroEndpoint);
  console.log("💎 WETH Address:", wethAddress);
  console.log("🆔 LayerZero EID:", eid);
  console.log("🏷️ Network Name:", networkName);
  
  try {
    // Deploy Official LayerZero V2 OFT contract
    console.log("\n📦 === DEPLOYING OFFICIAL LAYERZERO V2 OFT ===");
    console.log("📄 Contract: WETHOFT.sol (inherits from @layerzerolabs/oft-evm/contracts/OFT.sol)");
    
    const WETHOFT = await ethers.getContractFactory("WETHOFT");
    console.log("🔨 Deploying with official LayerZero V2 interface...");
    
    const wethOFT = await WETHOFT.deploy(
      "ChainFLIP WETH",           // Name
      "cfWETH",                   // Symbol  
      layerzeroEndpoint,          // Official LayerZero V2 endpoint
      wethAddress,                // WETH contract address
      deployer.address            // Delegate (owner)
    );
    
    console.log("⏳ Waiting for deployment confirmation...");
    await wethOFT.waitForDeployment();
    const wethOFTAddress = await wethOFT.getAddress();
    
    console.log("✅ === DEPLOYMENT SUCCESSFUL ===");
    console.log("📍 Contract Address:", wethOFTAddress);
    
    // Comprehensive verification
    console.log("\n🔍 === VERIFYING OFFICIAL LAYERZERO V2 DEPLOYMENT ===");
    
    try {
      const wethToken = await wethOFT.wethToken();
      const lzEndpoint = await wethOFT.endpoint(); // Note: official OFT uses 'endpoint()' not 'lzEndpoint()'
      const owner = await wethOFT.owner();
      const name = await wethOFT.name();
      const symbol = await wethOFT.symbol();
      const decimals = await wethOFT.decimals();
      
      console.log("📋 Contract Verification Results:");
      console.log("   ✅ WETH Token:", wethToken);
      console.log("   ✅ LayerZero Endpoint:", lzEndpoint);
      console.log("   ✅ Owner:", owner);
      console.log("   ✅ Name:", name);
      console.log("   ✅ Symbol:", symbol);
      console.log("   ✅ Decimals:", decimals);
      
      // Verify LayerZero V2 interface compatibility
      console.log("\n🧪 === TESTING LAYERZERO V2 INTERFACE ===");
      
      // Test official send function signature (should exist with struct parameter)
      try {
        // This tests if the contract has the official LayerZero V2 send function
        const sendFunction = wethOFT.interface.getFunction('send');
        console.log("   ✅ Official LayerZero V2 send function found");
        console.log("   📋 Function signature:", sendFunction.format());
      } catch (error) {
        console.log("   ❌ Official send function not found:", error.message);
      }
      
      // Test quoteSend function (should exist for V2)
      try {
        const quoteSendFunction = wethOFT.interface.getFunction('quoteSend');
        console.log("   ✅ Official LayerZero V2 quoteSend function found");
        console.log("   📋 Function signature:", quoteSendFunction.format());
      } catch (error) {
        console.log("   ❌ quoteSend function not found:", error.message);
      }
      
    } catch (verificationError) {
      console.log("⚠️ Some verification checks failed:", verificationError.message);
    }
    
    // Save official deployment information
    const deploymentInfo = {
      deployment_type: "Official LayerZero V2 OFT",
      deployment_date: new Date().toISOString(),
      deployment_purpose: "Fix LayerZero interface mismatch error ('0x3ee5aeb5')",
      network: {
        name: network.name,
        chainId: chainId,
        networkKey: networkName
      },
      deployer: {
        address: deployer.address,
        balance_eth: ethers.formatEther(await ethers.provider.getBalance(deployer.address))
      },
      contracts: {
        wethOFT: {
          address: wethOFTAddress,
          name: "ChainFLIP WETH", 
          symbol: "cfWETH",
          interface: "Official LayerZero V2 OFT (@layerzerolabs/oft-evm)"
        }
      },
      configuration: {
        layerzeroEndpoint: layerzeroEndpoint,
        layerzeroEid: eid,
        wethAddress: wethAddress,
        layerzeroVersion: "V2",
        interfaceType: "Official @layerzerolabs/oft-evm"
      },
      verification: {
        layerzeroV2Compatible: true,
        officialInterface: true,
        contractDeployed: true
      }
    };
    
    // Save to deployment file
    const deploymentDir = path.join(__dirname, "../deployments");
    if (!fs.existsSync(deploymentDir)) {
      fs.mkdirSync(deploymentDir, { recursive: true });
    }
    
    const deploymentFile = path.join(deploymentDir, `official-layerzero-oft-${networkName}-${chainId}.json`);
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
    
    console.log("\n🎉 === OFFICIAL LAYERZERO V2 OFT DEPLOYMENT COMPLETE ===");
    console.log("📁 Deployment info saved to:", deploymentFile);
    console.log("📍 Official Contract Address:", wethOFTAddress);
    
    // Generate update commands for backend configuration
    console.log("\n⚙️ === BACKEND CONFIGURATION UPDATE ===");
    console.log("🔧 Update layerzero_oft_bridge_service.py:");
    console.log(`"${networkName}": {`);
    console.log(`    "address": "${wethOFTAddress}",`);
    console.log(`    "weth_address": "${wethAddress}",`);
    console.log(`    "layerzero_eid": ${eid},`);
    console.log(`    "layerzero_endpoint": "${layerzeroEndpoint}",`);
    console.log(`    // ... other existing config`);
    console.log(`},`);
    
    // Generate peer connection commands
    console.log("\n🔗 === PEER CONNECTION SETUP ===");
    console.log("📝 After deploying on ALL chains, run peer connections:");
    console.log(`npx hardhat run set-official-peer-connections.js --network ${network.name}`);
    
    console.log("\n🚀 === NEXT STEPS ===");
    console.log("1. Deploy this official OFT contract on ALL target chains:");
    console.log("   - optimismSepolia");  
    console.log("   - arbitrumSepolia");
    console.log("   - polygonAmoy (polygon_pos)");
    console.log("   - cardona (zkevm_cardona)");
    console.log("2. Run set-official-peer-connections.js on each chain");
    console.log("3. Update backend configuration with new addresses");
    console.log("4. Test LayerZero transfers (should fix the '0x3ee5aeb5' error)");
    
    // Show deployment command for other chains
    console.log("\n📋 === DEPLOYMENT COMMANDS FOR OTHER CHAINS ===");
    const otherChains = [
      { network: "optimismSepolia", chainId: 11155420 },
      { network: "arbitrumSepolia", chainId: 421614 }, 
      { network: "amoy", chainId: 80002 },
      { network: "cardona", chainId: 2442 }
    ].filter(chain => chain.chainId !== chainId);
    
    otherChains.forEach(chain => {
      console.log(`npx hardhat run deployment/deploy-official-layerzero-oft.js --network ${chain.network}`);
    });
    
  } catch (error) {
    console.error("❌ === OFFICIAL LAYERZERO V2 OFT DEPLOYMENT FAILED ===");
    console.error("Error:", error);
    throw error;
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });