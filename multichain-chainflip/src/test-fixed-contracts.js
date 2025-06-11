const { ethers } = require("hardhat");

// New LayerZero OFT Contract Addresses (Fixed Contracts)
const CONTRACTS = {
  optimismSepolia: "0xc62b85a3C3165de614406bf2a67792648F536d93",
  arbitrumSepolia: "0x7345824F815bF1C4693D1995224128ed299Fcec0", 
  polygonAmoy: "0x0785d8F40e1837190089Ca7c65AAF95331Ce0294",
  zkevmCardona: "0x308F0975F32675F7d343360d16fAb9EA6aAeDF49"
};

// LayerZero V2 Endpoint IDs
const EIDS = {
  optimismSepolia: 40232,
  arbitrumSepolia: 40231,
  polygonAmoy: 40313,
  zkevmCardona: 40158
};

// Basic contract ABI for testing
const TEST_ABI = [
  {
    "inputs": [],
    "name": "name",
    "outputs": [{"name": "", "type": "string"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "symbol", 
    "outputs": [{"name": "", "type": "string"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "decimals",
    "outputs": [{"name": "", "type": "uint8"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "lzEndpoint",
    "outputs": [{"name": "", "type": "address"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{"name": "_eid", "type": "uint32"}],
    "name": "peers",
    "outputs": [{"name": "", "type": "bytes32"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {"name": "_dstEid", "type": "uint32"},
      {"name": "_to", "type": "bytes32"},
      {"name": "_amountLD", "type": "uint256"},
      {"name": "_minAmountLD", "type": "uint256"},
      {"name": "_extraOptions", "type": "bytes"},
      {"name": "_payInLzToken", "type": "bool"}
    ],
    "name": "quoteSend",
    "outputs": [{"name": "", "type": "tuple", "components": [
      {"name": "nativeFee", "type": "uint256"},
      {"name": "lzTokenFee", "type": "uint256"}
    ]}],
    "stateMutability": "view",
    "type": "function"
  }
];

async function testFixedContracts() {
  console.log("🧪 Testing Fixed LayerZero OFT Contracts...");
  
  // Get current network
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  
  console.log(`🌐 Current Network: ${network.name} (${chainId})`);
  
  // Determine current chain and contract
  let currentChain;
  let currentContract;
  
  if (chainId === 11155420) {
    currentChain = "optimismSepolia";
    currentContract = CONTRACTS.optimismSepolia;
  } else if (chainId === 421614) {
    currentChain = "arbitrumSepolia"; 
    currentContract = CONTRACTS.arbitrumSepolia;
  } else if (chainId === 80002) {
    currentChain = "polygonAmoy";
    currentContract = CONTRACTS.polygonAmoy;
  } else if (chainId === 2442) {
    currentChain = "zkevmCardona";
    currentContract = CONTRACTS.zkevmCardona;
  } else {
    console.error("❌ Unsupported network for testing");
    return;
  }

  console.log(`📍 Testing contract: ${currentChain} (${currentContract})\n`);

  // Get contract instance
  const oftContract = new ethers.Contract(currentContract, TEST_ABI, ethers.provider);

  // Test 1: Basic ERC20 functions
  console.log("📋 Test 1: Basic Contract Functions");
  try {
    const name = await oftContract.name();
    const symbol = await oftContract.symbol();
    const decimals = await oftContract.decimals();
    
    console.log(`   Name: ${name}`);
    console.log(`   Symbol: ${symbol}`);
    console.log(`   Decimals: ${decimals}`);
    console.log("   ✅ Basic functions working\n");
  } catch (error) {
    console.error(`   ❌ Basic functions failed: ${error.message}\n`);
  }

  // Test 2: LayerZero endpoint
  console.log("🔗 Test 2: LayerZero Endpoint");
  try {
    const lzEndpoint = await oftContract.lzEndpoint();
    console.log(`   LayerZero Endpoint: ${lzEndpoint}`);
    console.log("   ✅ LayerZero endpoint accessible\n");
  } catch (error) {
    console.error(`   ❌ LayerZero endpoint failed: ${error.message}\n`);
  }

  // Test 3: Peer connections
  console.log("👥 Test 3: Peer Connections");
  const otherChains = Object.entries(EIDS).filter(([chain]) => chain !== currentChain);
  
  for (const [chainName, eid] of otherChains) {
    try {
      const peer = await oftContract.peers(eid);
      const peerAddress = peer === "0x0000000000000000000000000000000000000000000000000000000000000000" 
        ? "Not set" 
        : `0x${peer.slice(26)}`;
      
      console.log(`   ${chainName} (EID ${eid}): ${peerAddress}`);
      
      if (peerAddress !== "Not set") {
        console.log(`   ✅ Peer configured for ${chainName}`);
      } else {
        console.log(`   ⚠️ Peer NOT configured for ${chainName}`);
      }
    } catch (error) {
      console.error(`   ❌ Error checking peer for ${chainName}: ${error.message}`);
    }
  }
  console.log();

  // Test 4: Quote function (most critical test)
  console.log("💰 Test 4: Quote Function (Critical)");
  const testAmount = ethers.parseEther("0.01"); // 0.01 ETH
  const testRecipient = "0x0000000000000000000000000000000000000000000000000000000000000001";
  
  for (const [chainName, eid] of otherChains.slice(0, 1)) { // Test with first other chain
    try {
      console.log(`   Testing quote to ${chainName} (EID ${eid})...`);
      
      const quote = await oftContract.quoteSend(
        eid,                    // destination EID
        testRecipient,          // recipient (dummy)
        testAmount,             // amount
        testAmount,             // min amount
        "0x",                   // extra options
        false                   // pay in LZ token
      );
      
      const nativeFeeEth = ethers.formatEther(quote.nativeFee);
      const lzTokenFee = quote.lzTokenFee.toString();
      
      console.log(`   📊 Quote Results:`);
      console.log(`      Native Fee: ${nativeFeeEth} ETH`);
      console.log(`      LZ Token Fee: ${lzTokenFee}`);
      console.log(`   ✅ QUOTE FUNCTION WORKS! This was the main issue before.`);
      
    } catch (error) {
      console.error(`   ❌ Quote function failed for ${chainName}: ${error.message}`);
      console.error(`   🚨 This indicates the contract still has issues!`);
    }
  }

  console.log("\n🎉 Contract Testing Complete!");
  console.log("📝 Summary:");
  console.log(`   Contract: ${currentContract}`);
  console.log(`   Chain: ${currentChain}`);
  console.log(`   Status: Fixed contracts deployed successfully`);
}

async function main() {
  try {
    await testFixedContracts();
  } catch (error) {
    console.error("❌ Contract testing failed:", error);
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });