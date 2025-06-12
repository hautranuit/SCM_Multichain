// LayerZero V2 Peer Connection Setup via Wrapper Contract
// Since wrapper owns the OFT contract, we need to call setPeer through wrapper

const hre = require("hardhat");
const { ethers } = require("hardhat");

// ETH Wrapper Contract addresses (these own the OFT contracts)
const WRAPPER_CONTRACTS = {
    optimismSepolia: "0x5428793EBd36693c993D6B3f8f2641C46121ec29",
    arbitrumSepolia: "0x5952569276eA7f7eF95B910EAd0a67067A518188",
    amoy: "0xA471c665263928021AF5aa7852724b6f757005e1"
};

// ChainFlipOFT Contract addresses (owned by wrappers above)
const OFT_CONTRACTS = {
    optimismSepolia: "0x6478eAB366A16d96ae910fd16F6770DDa1845648",
    arbitrumSepolia: "0x441C06d8548De93d64072F781e15E16A7c316b67",
    amoy: "0x865F1Dac1d8E17f492FFce578095b49f3D604ad4"
};

// LayerZero Endpoint IDs for V2
const LAYERZERO_EIDS = {
    optimismSepolia: 40232,
    arbitrumSepolia: 40231,
    amoy: 40267
};

// Enhanced Wrapper ABI - includes setPeer function
const WRAPPER_ABI = [
    {
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "amount", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "cfWETH",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    // Add setPeer function if wrapper can delegate to OFT
    {
        "inputs": [
            {"name": "_eid", "type": "uint32"},
            {"name": "_peer", "type": "bytes32"}
        ],
        "name": "setPeer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
];

// OFT ABI for verification
const OFT_ABI = [
    {
        "inputs": [{"name": "_eid", "type": "uint32"}],
        "name": "peers",
        "outputs": [{"name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
];

async function main() {
    console.log("🔗 Setting LayerZero V2 Peers via Wrapper Contracts");
    console.log("✨ Wrapper contracts own OFT contracts and can set peers");
    
    const [deployer] = await ethers.getSigners();
    const currentNetwork = hre.network.name;
    
    console.log(`\n📊 Current Network: ${currentNetwork}`);
    console.log(`   Deployer: ${deployer.address}`);
    
    // Get current network contracts
    const currentWrapperAddress = WRAPPER_CONTRACTS[currentNetwork];
    const currentOftAddress = OFT_CONTRACTS[currentNetwork];
    
    if (!currentWrapperAddress || !currentOftAddress) {
        throw new Error(`No contracts configured for network: ${currentNetwork}`);
    }
    
    console.log(`   ETH Wrapper: ${currentWrapperAddress}`);
    console.log(`   ChainFlipOFT: ${currentOftAddress}`);
    
    // Try different approaches to set peers
    
    // Approach 1: Direct call to wrapper setPeer (if it exists)
    console.log(`\n🔗 Approach 1: Try wrapper setPeer...`);
    const wrapperContract = new ethers.Contract(currentWrapperAddress, WRAPPER_ABI, deployer);
    
    let wrapperCanSetPeers = false;
    try {
        // Test if wrapper has setPeer function
        await wrapperContract.callStatic.setPeer(40231, "0x0000000000000000000000000000000000000000000000000000000000000000");
        wrapperCanSetPeers = true;
        console.log(`   ✅ Wrapper contract supports setPeer`);
    } catch (error) {
        console.log(`   ❌ Wrapper doesn't support setPeer: ${error.message.slice(0, 100)}...`);
    }
    
    if (wrapperCanSetPeers) {
        // Set peers via wrapper
        console.log(`\n🔗 Setting peer connections via wrapper...`);
        
        for (const [networkName, oftAddress] of Object.entries(OFT_CONTRACTS)) {
            if (networkName === currentNetwork) continue;
            
            const targetEid = LAYERZERO_EIDS[networkName];
            const peerBytes32 = ethers.utils.hexZeroPad(oftAddress.toLowerCase(), 32);
            
            console.log(`\n📡 Setting peer: ${networkName}`);
            console.log(`   EID: ${targetEid}`);
            console.log(`   OFT Address: ${oftAddress}`);
            console.log(`   Bytes32: ${peerBytes32}`);
            
            try {
                const tx = await wrapperContract.setPeer(targetEid, peerBytes32);
                console.log(`   📤 Transaction sent: ${tx.hash}`);
                
                const receipt = await tx.wait();
                console.log(`   ✅ Peer set via wrapper (Gas used: ${receipt.gasUsed})`);
                
            } catch (error) {
                console.log(`   ❌ Failed to set peer via wrapper: ${error.message}`);
            }
        }
    } else {
        // Approach 2: Manual instructions for contract owner
        console.log(`\n🔗 Approach 2: Manual peer setting required`);
        console.log(`   The wrapper contract owns the OFT contract but doesn't expose setPeer.`);
        console.log(`   You need to either:`);
        console.log(`   1. Add setPeer function to wrapper contract`);
        console.log(`   2. Or transfer OFT ownership to deployer temporarily`);
        
        // Show the calls that need to be made
        console.log(`\n📋 Required setPeer calls on OFT contract (${currentOftAddress}):`);
        for (const [networkName, oftAddress] of Object.entries(OFT_CONTRACTS)) {
            if (networkName === currentNetwork) continue;
            
            const targetEid = LAYERZERO_EIDS[networkName];
            const peerBytes32 = ethers.utils.hexZeroPad(oftAddress.toLowerCase(), 32);
            
            console.log(`   setPeer(${targetEid}, "${peerBytes32}") // ${networkName}`);
        }
    }
    
    // Verify peer connections
    console.log(`\n🔍 Verifying peer connections on OFT contract...`);
    const oftContract = new ethers.Contract(currentOftAddress, OFT_ABI, deployer);
    
    for (const [networkName, oftAddress] of Object.entries(OFT_CONTRACTS)) {
        if (networkName === currentNetwork) continue;
        
        const targetEid = LAYERZERO_EIDS[networkName];
        const expectedPeer = ethers.utils.hexZeroPad(oftAddress.toLowerCase(), 32);
        
        try {
            const actualPeer = await oftContract.peers(targetEid);
            if (actualPeer === expectedPeer) {
                console.log(`   ✅ ${networkName} (EID ${targetEid}): CORRECT`);
            } else if (actualPeer === "0x0000000000000000000000000000000000000000000000000000000000000000") {
                console.log(`   ⚠️ ${networkName} (EID ${targetEid}): NOT SET`);
            } else {
                console.log(`   ❌ ${networkName} (EID ${targetEid}): MISMATCH`);
                console.log(`      Expected: ${expectedPeer}`);
                console.log(`      Actual: ${actualPeer}`);
            }
        } catch (error) {
            console.log(`   ❌ ${networkName} (EID ${targetEid}): ERROR - ${error.message}`);
        }
    }
    
    console.log(`\n🎯 Peer Setup Process Complete!`);
    console.log(`\n🔗 Run on other networks:`);
    console.log(`   npx hardhat run scripts/set-peer-connections-via-wrapper.js --network optimismSepolia`);
    console.log(`   npx hardhat run scripts/set-peer-connections-via-wrapper.js --network arbitrumSepolia`);
    console.log(`   npx hardhat run scripts/set-peer-connections-via-wrapper.js --network amoy`);
}

main().catch((error) => {
    console.error("❌ Error setting peer connections:", error);
    process.exitCode = 1;
});
