const { ethers } = require("hardhat");

async function main() {
    console.log("🔑 Granting MINTER_ROLE to Manufacturer Account...");
    
    // Get manufacturer address from environment variable first
    let manufacturerAddress = process.env.MANUFACTURER_ADDRESS;
    
    if (!manufacturerAddress) {
        console.error("❌ Error: Manufacturer address is required");
        console.log("📋 Usage (Environment Variable - REQUIRED):");
        console.log("");
        console.log("📋 Windows PowerShell:");
        console.log("   $env:MANUFACTURER_ADDRESS='0x5503a5B847e98B621d97695edf1bD84242C5862E'");
        console.log("   npx hardhat run scripts/grant-minter-role.js --network baseSepolia");
        console.log("");
        console.log("📋 Windows Command Prompt:");
        console.log("   set MANUFACTURER_ADDRESS=0x5503a5B847e98B621d97695edf1bD84242C5862E");
        console.log("   npx hardhat run scripts/grant-minter-role.js --network baseSepolia");
        console.log("");
        console.log("📋 Linux/Mac:");
        console.log("   MANUFACTURER_ADDRESS=0x5503a5B847e98B621d97695edf1bD84242C5862E npx hardhat run scripts/grant-minter-role.js --network baseSepolia");
        console.log("");
        console.log("📋 Note: Hardhat doesn't support positional arguments with 'npx hardhat run'");
        process.exit(1);
    }
    
    // Validate manufacturer address format
    if (!ethers.utils.isAddress(manufacturerAddress)) {
        console.error("❌ Error: Invalid Ethereum address format");
        console.log("📋 Provided address:", manufacturerAddress);
        console.log("📋 Example valid address: 0x5503a5B847e98B621d97695edf1bD84242C5862E");
        process.exit(1);
    }
    
    // Convert to checksum address
    const MANUFACTURER_ADDRESS = ethers.utils.getAddress(manufacturerAddress);
    
    console.log("📋 Parameters:");
    console.log("   Manufacturer Address:", MANUFACTURER_ADDRESS);
    console.log("");
    
    // Contract addresses
    const NFT_CONTRACTS = {
        "Base Sepolia": "0x0D06a583a3d1bD02D7BdEe535D53495A0E57510C",
        "OP Sepolia": "0x36f6416213f454Af4a3213067C68F81Fd4919c18", 
        "Arbitrum Sepolia": "0x76D43CEC28775032A7EC8895ad178c660246c8Ec",
        "Polygon Amoy": "0x8cF29cAA6175413AaedcDF29bdA94078ccE77aA9"
    };
    
    // Admin account (has DEFAULT_ADMIN_ROLE and MINTER_ROLE)
    const ADMIN_ADDRESS = "0x032041b4b356fEE1496805DD4749f181bC736FFA";
    
    // Get signer (admin account)
    const [deployer] = await ethers.getSigners();
    console.log("🔐 Using admin account:", deployer.address);
    
    if (deployer.address.toLowerCase() !== ADMIN_ADDRESS.toLowerCase()) {
        console.log("⚠️ Warning: Current signer is not the expected admin account");
        console.log("   Expected:", ADMIN_ADDRESS);
        console.log("   Current:", deployer.address);
        console.log("   ⚠️  Make sure you're using the correct private key in your hardhat config");
    }
    
    // NFT Contract ABI (minimal for role management)
    const nftAbi = [
        "function grantMinterRole(address account) public",
        "function hasRole(bytes32 role, address account) public view returns (bool)",
        "function MINTER_ROLE() public view returns (bytes32)"
    ];
    
    console.log("📋 Granting MINTER_ROLE to manufacturer on all chains...");
    console.log("   Admin:", deployer.address);
    console.log("   Manufacturer:", MANUFACTURER_ADDRESS);
    console.log("");
    
    let successCount = 0;
    let errorCount = 0;
    
    for (const [networkName, contractAddress] of Object.entries(NFT_CONTRACTS)) {
        try {
            console.log(`🔗 Processing ${networkName}: ${contractAddress}`);
            
            // Create contract instance
            const nftContract = new ethers.Contract(contractAddress, nftAbi, deployer);
            
            // Get MINTER_ROLE bytes32 value
            const MINTER_ROLE = await nftContract.MINTER_ROLE();
            console.log(`   MINTER_ROLE: ${MINTER_ROLE}`);
            
            // Check if manufacturer already has MINTER_ROLE
            const hasRole = await nftContract.hasRole(MINTER_ROLE, MANUFACTURER_ADDRESS);
            
            if (hasRole) {
                console.log(`   ✅ Manufacturer already has MINTER_ROLE on ${networkName}`);
                successCount++;
            } else {
                console.log(`   🔄 Granting MINTER_ROLE to manufacturer on ${networkName}...`);
                
                // Grant MINTER_ROLE
                const tx = await nftContract.grantMinterRole(MANUFACTURER_ADDRESS);
                console.log(`   📤 Transaction sent: ${tx.hash}`);
                
                // Wait for confirmation
                const receipt = await tx.wait();
                console.log(`   ✅ MINTER_ROLE granted! Block: ${receipt.blockNumber}, Gas: ${receipt.gasUsed}`);
                
                // Verify the role was granted
                const hasRoleAfter = await nftContract.hasRole(MINTER_ROLE, MANUFACTURER_ADDRESS);
                if (hasRoleAfter) {
                    console.log(`   ✅ Verification: Manufacturer now has MINTER_ROLE on ${networkName}`);
                    successCount++;
                } else {
                    console.log(`   ❌ Verification failed: Role grant unsuccessful on ${networkName}`);
                    errorCount++;
                }
            }
            
            console.log("");
            
        } catch (error) {
            console.log(`   ❌ Error on ${networkName}: ${error.message}`);
            errorCount++;
            console.log("");
        }
    }
    
    console.log("🎉 MINTER_ROLE grant process completed!");
    console.log("");
    console.log("📊 Results Summary:");
    console.log(`   ✅ Successful: ${successCount}/${Object.keys(NFT_CONTRACTS).length}`);
    console.log(`   ❌ Errors: ${errorCount}/${Object.keys(NFT_CONTRACTS).length}`);
    console.log(`   🎯 Manufacturer: ${MANUFACTURER_ADDRESS}`);
    console.log("");
    
    if (successCount > 0) {
        console.log("📋 Next Steps:");
        console.log("   • Manufacturer can now mint NFTs on successful chains");
        console.log("   • Test NFT minting from frontend");
        console.log("   • Test cross-chain NFT transfers");
    }
    
    if (errorCount > 0) {
        console.log("⚠️ Action Required:");
        console.log("   • Check network connectivity for failed chains");
        console.log("   • Verify admin account has sufficient gas");
        console.log("   • Retry failed networks individually");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Script failed:", error);
        process.exit(1);
    });
