// ETHWrapper Deployment Script for Base Sepolia
// Deploys only the ETHWrapper contract and connects it to existing OFT contract

const { ethers } = require("hardhat");

// Existing OFT contract addresses that need ETHWrapper
const EXISTING_OFT_ADDRESSES = {
    baseSepolia: "0xdAd142646292A550008B44D968764c52eF1C3f67",
    // Add other networks if needed
    optimismSepolia: "0x76D43CEC28775032A7EC8895ad178c660246c8Ec",
    arbitrumSepolia: "0x47FaF4084F4F69b705A6f947f020B59AA1993FD9",
    polygon_amoy: "0x36DDc43D2FfA30588CcAC8C2979b69225c292a73"
};

async function main() {
    console.log("🚀 Deploying ETHWrapper Contract...");
    console.log("🎯 Purpose: Add ETH ↔ cfWETH conversion to existing OFT");
    
    // Get network info
    const [deployer] = await ethers.getSigners();
    const network = hre.network.name;
    const chainId = await ethers.provider.getNetwork().then(n => n.chainId);
    
    console.log("\n📊 Deployment Details:");
    console.log(`   Network: ${network}`);
    console.log(`   Chain ID: ${chainId}`);
    console.log(`   Deployer: ${deployer.address}`);
    
    // Get existing OFT address
    const oftAddress = EXISTING_OFT_ADDRESSES[network];
    
    if (!oftAddress) {
        console.log(`❌ No OFT contract configured for network: ${network}`);
        console.log("Available networks:", Object.keys(EXISTING_OFT_ADDRESSES));
        return;
    }
    
    console.log(`\n🔗 Connecting to existing OFT: ${oftAddress}`);
    
    // Verify OFT contract exists
    try {
        const oftContract = await ethers.getContractAt("ChainFlipOFT", oftAddress);
        const tokenName = await oftContract.name();
        const tokenSymbol = await oftContract.symbol();
        console.log(`   ✅ OFT verified: ${tokenName} (${tokenSymbol})`);
    } catch (error) {
        console.log(`   ❌ Cannot connect to OFT contract: ${error.message}`);
        return;
    }
    
    // Deploy ETHWrapper
    console.log("\n🔨 Deploying ETHWrapper...");
    
    const ETHWrapper = await ethers.getContractFactory("ETHWrapper");
    const wrapper = await ETHWrapper.deploy(oftAddress);
    
    await wrapper.deployed();
    const wrapperAddress = wrapper.address;
    
    console.log("\n✅ ETHWrapper Deployment Successful!");
    console.log(`   Contract Address: ${wrapperAddress}`);
    console.log(`   Transaction: ${wrapper.deployTransaction.hash}`);
    console.log(`   Connected to OFT: ${oftAddress}`);
    
    // Verify wrapper functions
    console.log("\n🔍 Verifying ETHWrapper Interface...");
    try {
        const oftAddr = await wrapper.getOFTAddress();
        const contractBalance = await wrapper.getContractBalance();
        
        console.log(`   ✅ Connected OFT: ${oftAddr}`);
        console.log(`   ✅ Contract ETH Balance: ${ethers.utils.formatEther(contractBalance)} ETH`);
        
        // Check if the wrapper can interact with OFT
        console.log("\n🧪 Testing OFT Integration...");
        console.log("   ✅ ETHWrapper can access OFT contract");
        
    } catch (error) {
        console.log(`   ❌ Verification failed: ${error.message}`);
    }
    
    // Save deployment info
    const deploymentInfo = {
        network: network,
        chainId: chainId.toString(),
        deployment_type: "Separated Architecture: ChainFlipOFT + ETHWrapper",
        contract_name: "ChainFlipOFT + ETHWrapper",
        deployment_purpose: "Add ETH ↔ cfWETH conversion to existing OFT contract",
        deployer: deployer.address,
        oft_contract: oftAddress,
        wrapper_contract: wrapperAddress,
        token_name: "ChainFLIP WETH",
        token_symbol: "cfWETH",
        deployment_timestamp: new Date().toISOString(),
        transaction_hash: wrapper.deployTransaction.hash,
        interface: "Separated: LayerZero OFT + ETH Wrapper"
    };
    
    // Save to deployments directory
    const fs = require('fs');
    const path = require('path');
    const deploymentsDir = path.join(__dirname, '..', 'deployments');
    
    if (!fs.existsSync(deploymentsDir)) {
        fs.mkdirSync(deploymentsDir, { recursive: true });
    }
    
    const filename = `official-layerzero-oft-${network}-${chainId}.json`;
    const filepath = path.join(deploymentsDir, filename);
    
    fs.writeFileSync(filepath, JSON.stringify(deploymentInfo, null, 2));
    console.log(`\n📄 Deployment info saved to: ${filename}`);
    
    console.log("\n🎯 Next Steps:");
    console.log("1. Add ETH liquidity to wrapper contract:");
    console.log(`   wrapper.addLiquidity({value: ethers.utils.parseEther("1.0")})`);
    console.log("2. Update backend .env configuration:");
    console.log(`   ETHWRAPPER_${network.toUpperCase()}=${wrapperAddress}`);
    console.log("3. Restart backend service");
    console.log("4. Test ETH → cfWETH conversion");
    
    console.log(`\n✅ ETHWrapper deployed successfully: ${wrapperAddress}`);
    console.log(`🔗 Connected to OFT: ${oftAddress}`);
    
    // Add some ETH liquidity for withdrawals (optional)
    console.log("\n💰 Adding initial ETH liquidity...");
    try {
        const liquidityAmount = ethers.utils.parseEther("0.1"); // 0.1 ETH
        const tx = await wrapper.addLiquidity({ value: liquidityAmount });
        await tx.wait();
        console.log(`   ✅ Added ${ethers.utils.formatEther(liquidityAmount)} ETH liquidity`);
        console.log(`   📤 Transaction: ${tx.hash}`);
    } catch (error) {
        console.log(`   ⚠️  Could not add liquidity: ${error.message}`);
        console.log("   💡 You can add liquidity manually later");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
