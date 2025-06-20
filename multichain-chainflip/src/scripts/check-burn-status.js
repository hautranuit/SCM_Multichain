const { ethers } = require("hardhat");

async function main() {
    console.log("🔥 Testing NFT Burn Function...");
    
    const TOKEN_ID = "1";
    const NFT_CONTRACT = "0x0D06a583a3d1bD02D7BdEe535D53495A0E57510C";
    const MANUFACTURER = "0x5503a5B847e98B621d97695edf1bD84242C5862E";
    
    console.log(`📋 Checking Token ID ${TOKEN_ID} on Base Sepolia...`);
    console.log(`🏭 Contract: ${NFT_CONTRACT}`);
    console.log("");
    
    // Get signer
    const [deployer] = await ethers.getSigners();
    console.log("🔐 Using admin account:", deployer.address);
    
    // NFT Contract ABI
    const nftAbi = [
        "function ownerOf(uint256 tokenId) public view returns (address owner)",
        "function tokenURI(uint256 tokenId) public view returns (string memory)",
        "function _exists(uint256 tokenId) public view returns (bool)",
        "function burnForBridge(uint256 tokenId) public returns (string memory)",
        "function hasRole(bytes32 role, address account) public view returns (bool)",
        "function MINTER_ROLE() public view returns (bytes32)"
    ];
    
    try {
        const nftContract = new ethers.Contract(NFT_CONTRACT, nftAbi, deployer);
        
        console.log("🔍 Current Token Status:");
        
        // Check owner
        try {
            const owner = await nftContract.ownerOf(TOKEN_ID);
            console.log(`   👤 Owner: ${owner}`);
            
            if (owner === ethers.constants.AddressZero) {
                console.log("   ❌ Token transferred to zero address (pseudo-burn)");
            } else if (owner === MANUFACTURER) {
                console.log("   ✅ Token still owned by manufacturer");
            } else {
                console.log("   ⚠️ Token owned by someone else");
            }
        } catch (error) {
            console.log("   ❌ Token does not exist (true burn) or other error:", error.message);
        }
        
        // Check token URI
        try {
            const tokenURI = await nftContract.tokenURI(TOKEN_ID);
            console.log(`   📄 Token URI: ${tokenURI.substring(0, 50)}...`);
        } catch (error) {
            console.log("   ❌ Cannot get token URI:", error.message);
        }
        
        // Check if manufacturer has MINTER_ROLE
        try {
            const MINTER_ROLE = await nftContract.MINTER_ROLE();
            const hasRole = await nftContract.hasRole(MINTER_ROLE, MANUFACTURER);
            console.log(`   🔑 Manufacturer has MINTER_ROLE: ${hasRole}`);
        } catch (error) {
            console.log("   ⚠️ Could not check MINTER_ROLE:", error.message);
        }
        
        console.log("");
        console.log("📋 Burn Transaction Analysis:");
        console.log("   TX Hash: 95fa4614fa1617b406296b7f1a503b34238013e09d3868c0027b427a3db601d3");
        console.log("   Explorer: https://sepolia.basescan.org/tx/95fa4614fa1617b406296b7f1a503b34238013e09d3868c0027b427a3db601d3");
        console.log("");
        
        if (owner === ethers.constants.AddressZero) {
            console.log("🔧 Result: Token was transferred to zero address, not truly burned");
            console.log("💡 This means the burn function might not be working as expected");
            console.log("💡 Or the function used was transfer() instead of _burn()");
        }
        
    } catch (error) {
        console.error("❌ Error checking token:", error.message);
    }
}

main()
    .then(() => {
        console.log("🔥 Burn check completed!");
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Script failed:", error);
        process.exit(1);
    });