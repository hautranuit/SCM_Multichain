const { ethers } = require("hardhat");

async function main() {
    // Account to grant SENDER_ROLE to (the manufacturer account)
    const targetAccount = "0x04351e7dF40d04B5E610c4aA033faCf435b98711";
    const directMessengerContract = "0x1208F8F0E40381F14E41621906D13C9c3CaAa061"; // Base Sepolia DirectLayerZeroMessenger
    
    console.log("🌐 Granting SENDER_ROLE on DirectLayerZeroMessenger");
    console.log("🔐 Target Account:", targetAccount);
    console.log("📝 Contract:", directMessengerContract);
    
    const [deployer] = await ethers.getSigners();
    console.log("🔑 Using admin account:", deployer.address);
    
    // DirectLayerZeroMessenger ABI for role management
    const abi = [
        "function SENDER_ROLE() view returns (bytes32)",
        "function hasRole(bytes32 role, address account) view returns (bool)",
        "function grantRole(bytes32 role, address account)",
        "function DEFAULT_ADMIN_ROLE() view returns (bytes32)",
        "function getRoleAdmin(bytes32 role) view returns (bytes32)"
    ];
    
    const messenger = new ethers.Contract(directMessengerContract, abi, deployer);
    
    try {
        // Get SENDER_ROLE bytes32 value
        const SENDER_ROLE = await messenger.SENDER_ROLE();
        console.log("🔐 SENDER_ROLE:", SENDER_ROLE);
        
        // Check if target account already has SENDER_ROLE
        const hasRole = await messenger.hasRole(SENDER_ROLE, targetAccount);
        console.log("🔍 Current SENDER_ROLE status:", hasRole);
        
        if (hasRole) {
            console.log("✅ Account already has SENDER_ROLE");
            return;
        }
        
        // Check if deployer has admin role
        const DEFAULT_ADMIN_ROLE = await messenger.DEFAULT_ADMIN_ROLE();
        const hasAdminRole = await messenger.hasRole(DEFAULT_ADMIN_ROLE, deployer.address);
        
        console.log("🔑 Deployer admin role status:", hasAdminRole);
        
        if (!hasAdminRole) {
            console.log("❌ Deployer does not have admin role. Cannot grant SENDER_ROLE");
            console.log("💡 Contact the contract owner to grant admin role first");
            return;
        }
        
        console.log("🚀 Granting SENDER_ROLE to manufacturer account...");
        console.log("📋 Transaction details:");
        console.log("   - From:", deployer.address);
        console.log("   - To:", directMessengerContract);
        console.log("   - Function: grantRole(SENDER_ROLE, targetAccount)");
        
        // Execute the grant role transaction
        const tx = await messenger.grantRole(SENDER_ROLE, targetAccount);
        console.log("📤 Transaction submitted:", tx.hash);
        console.log("⏳ Waiting for confirmation...");
        
        const receipt = await tx.wait();
        console.log("✅ SENDER_ROLE granted successfully!");
        console.log("📊 Block number:", receipt.blockNumber);
        console.log("⛽ Gas used:", receipt.gasUsed.toString());
        
        // Verify the role was granted
        const verifyRole = await messenger.hasRole(SENDER_ROLE, targetAccount);
        console.log("🔍 Verification - SENDER_ROLE granted:", verifyRole);
        
        console.log("\n🎉 SUCCESS! The manufacturer account can now send cross-chain messages");
        console.log("✅ Account", targetAccount, "now has SENDER_ROLE on DirectLayerZeroMessenger");
        console.log("🌐 Cross-chain CID sync is now fully functional");
        
    } catch (error) {
        console.error("❌ Error granting SENDER_ROLE:", error.message);
        
        // Provide helpful error diagnosis
        if (error.message.includes("AccessControl")) {
            console.log("💡 This appears to be an access control error");
            console.log("💡 The deployer account may not have sufficient permissions");
            console.log("💡 Check if the deployer is the contract owner or has admin role");
        } else if (error.message.includes("revert")) {
            console.log("💡 Transaction reverted - check contract state and permissions");
        }
        
        throw error;
    }
}

main().catch((error) => {
    console.error("❌ Script execution failed:", error);
    process.exit(1);
});