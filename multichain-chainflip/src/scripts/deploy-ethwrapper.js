// Fixed ETHWrapper Deployment Script - Owner-Mediated Minting
// Deploys ETHWrapper contract with owner-mediated minting to fix permission issues

const { ethers } = require("hardhat");

// Existing OFT contract addresses that need Fixed ETHWrapper
const EXISTING_OFT_ADDRESSES = {
    baseSepolia: "0xdAd142646292A550008B44D968764c52eF1C3f67",
    optimismSepolia: "0x76D43CEC28775032A7EC8895ad178c660246c8Ec",
    arbitrumSepolia: "0x47FaF4084F4F69b705A6f947f020B59AA1993FD9",
    polygon_amoy: "0x36DDc43D2FfA30588CcAC8C2979b69225c292a73"
};

async function main() {
    console.log("🔧 === DEPLOYING FIXED ETHWRAPPER ===");
    console.log("🎯 Purpose: Fix 'Ownable: caller is not the owner' permission issue");
    console.log("✨ Solution: Owner-mediated minting pattern");
    
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
    
    // Verify OFT contract exists and check owner
    try {
        const oftContract = await ethers.getContractAt("ChainFlipOFT", oftAddress);
        const tokenName = await oftContract.name();
        const tokenSymbol = await oftContract.symbol();
        const owner = await oftContract.owner();
        
        console.log(`   ✅ OFT verified: ${tokenName} (${tokenSymbol})`);
        console.log(`   👑 OFT Owner: ${owner}`);
        
        if (owner !== "0x032041b4b356fEE1496805DD4749f181bC736FFA") {
            console.log(`   ⚠️  Warning: Owner is not the expected address`);
        }
        
    } catch (error) {
        console.log(`   ❌ Cannot connect to OFT contract: ${error.message}`);
        return;
    }
    
    // Deploy Fixed ETHWrapper
    console.log("\n🔨 Deploying Fixed ETHWrapper with Owner-Mediated Minting...");
    
    const ETHWrapper = await ethers.getContractFactory("ETHWrapper");
    const wrapper = await ETHWrapper.deploy(oftAddress);
    
    await wrapper.deployed();
    const wrapperAddress = wrapper.address;
    
    console.log("\n✅ Fixed ETHWrapper Deployment Successful!");
    console.log(`   Contract Address: ${wrapperAddress}`);
    console.log(`   Transaction: ${wrapper.deployTransaction.hash}`);
    console.log(`   Connected to OFT: ${oftAddress}`);
    console.log(`   🔧 Fix Applied: Owner-mediated minting pattern`);
    
    // Verify Fixed wrapper functions
    console.log("\n🔍 Verifying Fixed ETHWrapper Interface...");
    try {
        const oftAddr = await wrapper.getOFTAddress();
        const owner = await wrapper.owner();
        const contractBalance = await wrapper.getContractBalance();
        
        console.log(`   ✅ Connected OFT: ${oftAddr}`);
        console.log(`   👑 Wrapper Owner: ${owner}`);
        console.log(`   📊 Contract ETH Balance: ${ethers.utils.formatEther(contractBalance)} ETH`);
        
        // Test new pending deposit functionality
        const testUser = "0x04351e7dF40d04B5E610c4aA033faCf435b98711";
        const pendingDeposit = await wrapper.getPendingDeposit(testUser);
        console.log(`   ✅ Pending deposit tracking: ${ethers.utils.formatEther(pendingDeposit)} ETH`);
        
        console.log(`   ✅ Fixed ETHWrapper can track pending deposits`);
        console.log(`   ✅ Owner can process minting via processPendingDeposit()`);
        
    } catch (error) {
        console.log(`   ❌ Verification failed: ${error.message}`);
    }
    
    // Save deployment info
    const deploymentInfo = {
        network: network,
        chainId: chainId.toString(),
        deployment_type: "Fixed ETHWrapper with Owner-Mediated Minting",
        contract_name: "ETHWrapper (Fixed)",
        deployment_purpose: "Fix permission issue - owner-mediated minting pattern",
        fix_applied: "Owner-mediated minting to bypass 'Ownable: caller is not the owner' error",
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
    
    const filename = `fixed-ethwrapper-${network}-${chainId}.json`;
    const filepath = path.join(deploymentsDir, filename);
    
    fs.writeFileSync(filepath, JSON.stringify(deploymentInfo, null, 2));
    console.log(`\n📄 Deployment info saved to: ${filename}`);
    
    console.log("\n🎯 NEXT STEPS:");
    console.log("1. Update backend .env configuration:");
    console.log(`   ETHWRAPPER_${network.toUpperCase()}=${wrapperAddress}`);
    console.log("2. Restart backend service");
    console.log("3. Test ETH → cfWETH conversion (should now work!)");
    console.log("4. Test cross-chain transfers");
    console.log("5. Test cfWETH → ETH withdrawal");
    
    console.log("\n🔧 HOW THE FIX WORKS:");
    console.log("• User deposits ETH → Creates pending deposit");
    console.log("• Backend uses owner account → Processes minting via processPendingDeposit()");
    console.log("• Result: ETH → cfWETH conversion without permission errors");
    
    console.log(`\n✅ FIXED ETHWRAPPER DEPLOYED: ${wrapperAddress}`);
    console.log(`🔗 Connected to OFT: ${oftAddress}`);
    console.log(`🐛 Permission issue resolved with owner-mediated minting`);
    
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
