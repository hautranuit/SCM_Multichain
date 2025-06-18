const { ethers } = require("hardhat");

async function main() {
    // Account to grant MINTER_ROLE to
    const targetAccount = "0x04351e7dF40d04B5E610c4aA033faCf435b98711";
    const nftContract = "0x75d2E18211390A8f2bdA96BB4Bd2D45ba77d5baD";
    
    console.log("🔐 Granting MINTER_ROLE to:", targetAccount);
    
    const [deployer] = await ethers.getSigners();
    console.log("🔑 Using admin account:", deployer.address);
    
    const abi = [
        "function MINTER_ROLE() view returns (bytes32)",
        "function hasRole(bytes32 role, address account) view returns (bool)",
        "function grantRole(bytes32 role, address account)"
    ];
    
    const nft = new ethers.Contract(nftContract, abi, deployer);
    
    const MINTER_ROLE = await nft.MINTER_ROLE();
    console.log("🔐 MINTER_ROLE:", MINTER_ROLE);
    
    const hasRole = await nft.hasRole(MINTER_ROLE, targetAccount);
    
    if (hasRole) {
        console.log("✅ Account already has MINTER_ROLE");
        return;
    }
    
    console.log("🚀 Granting MINTER_ROLE...");
    const tx = await nft.grantRole(MINTER_ROLE, targetAccount);
    console.log("📤 Transaction:", tx.hash);
    
    await tx.wait();
    console.log("✅ MINTER_ROLE granted successfully!");
}

main().catch(console.error);
