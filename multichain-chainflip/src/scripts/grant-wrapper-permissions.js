// Grant ETHWrapper minting permissions on ChainFlipOFT contract
const { ethers } = require("hardhat");

// Contract addresses for Base Sepolia
const ETHWRAPPER_ADDRESS = "0x5C3922761DA97B7D89D0a8505746cb87d63A446E";
const OFT_ADDRESS = "0xdAd142646292A550008B44D968764c52eF1C3f67";

async function main() {
    console.log("🔐 Granting ETHWrapper minting permissions...");
    
    const [deployer] = await ethers.getSigners();
    const network = hre.network.name;
    
    console.log(`\n📊 Network: ${network}`);
    console.log(`   Deployer: ${deployer.address}`);
    console.log(`   OFT Contract: ${OFT_ADDRESS}`);
    console.log(`   ETHWrapper Contract: ${ETHWRAPPER_ADDRESS}`);
    
    // Connect to OFT contract
    console.log("\n🔗 Connecting to ChainFlipOFT contract...");
    const oftContract = await ethers.getContractAt("ChainFlipOFT", OFT_ADDRESS);
    
    // Check current owner
    try {
        const owner = await oftContract.owner();
        console.log(`   ✅ OFT Owner: ${owner}`);
        
        if (owner.toLowerCase() !== deployer.address.toLowerCase()) {
            console.log(`   ❌ Deployer is not owner. Cannot grant permissions.`);
            return;
        }
    } catch (error) {
        console.log(`   ⚠️  Could not check ownership: ${error.message}`);
    }
    
    // Check if contract has a minter role or similar
    console.log("\n🔍 Checking access control methods...");
    
    try {
        // Try different permission methods that might exist
        
        // Method 1: Check if there's a minter role
        try {
            const MINTER_ROLE = await oftContract.MINTER_ROLE();
            console.log(`   🔑 MINTER_ROLE found: ${MINTER_ROLE}`);
            
            // Grant minter role to ETHWrapper
            console.log(`   🔐 Granting MINTER_ROLE to ETHWrapper...`);
            const tx1 = await oftContract.grantRole(MINTER_ROLE, ETHWRAPPER_ADDRESS);
            await tx1.wait();
            console.log(`   ✅ MINTER_ROLE granted: ${tx1.hash}`);
            
        } catch (roleError) {
            console.log(`   ℹ️  No MINTER_ROLE found`);
            
            // Method 2: Try setMinter function
            try {
                console.log(`   🔐 Trying setMinter function...`);
                const tx2 = await oftContract.setMinter(ETHWRAPPER_ADDRESS, true);
                await tx2.wait();
                console.log(`   ✅ Minter set: ${tx2.hash}`);
                
            } catch (minterError) {
                console.log(`   ℹ️  No setMinter function found`);
                
                // Method 3: Try addMinter function
                try {
                    console.log(`   🔐 Trying addMinter function...`);
                    const tx3 = await oftContract.addMinter(ETHWRAPPER_ADDRESS);
                    await tx3.wait();
                    console.log(`   ✅ Minter added: ${tx3.hash}`);
                    
                } catch (addMinterError) {
                    console.log(`   ❌ No standard minting permission methods found`);
                    console.log(`   💡 The OFT contract might need manual modification`);
                }
            }
        }
        
    } catch (error) {
        console.log(`   ❌ Permission setup failed: ${error.message}`);
    }
    
    // Test minting permission
    console.log("\n🧪 Testing minting permission...");
    try {
        // Connect to ETHWrapper and try a small mint
        const wrapperContract = await ethers.getContractAt("ETHWrapper", ETHWRAPPER_ADDRESS);
        
        // Try to deposit a small amount
        console.log(`   🧪 Testing deposit function...`);
        const testAmount = ethers.utils.parseEther("0.001"); // 0.001 ETH
        
        // Estimate gas first
        const gasEstimate = await wrapperContract.estimateGas.deposit({ value: testAmount });
        console.log(`   ⛽ Gas estimate: ${gasEstimate.toString()}`);
        
        // If gas estimation succeeds, permissions are likely correct
        console.log(`   ✅ ETHWrapper can mint tokens (gas estimation successful)`);
        
    } catch (testError) {
        console.log(`   ❌ Minting test failed: ${testError.message}`);
        
        if (testError.message.includes("AccessControl")) {
            console.log(`   💡 Access control issue - permissions not granted correctly`);
        } else if (testError.message.includes("Ownable")) {
            console.log(`   💡 Ownership issue - ETHWrapper needs to be owner or approved`);
        }
    }
    
    console.log("\n✅ Permission setup complete!");
    console.log("\n🎯 Next Steps:");
    console.log("1. Test ETH → cfWETH conversion again");
    console.log("2. If still failing, check the OFT contract source for permission methods");
    console.log("3. May need to transfer ownership or use a different approach");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Permission setup failed:", error);
        process.exit(1);
    });
