const { ethers } = require("hardhat");

async function debugContract() {
    console.log("🔍 Debugging LayerZero OFT Contract Functions");

    const contractAddress = "0x1A3F3924662aaa4f5122cD2B2EDff614Cf1d6eb0";

    // Get the contract bytecode
    const provider = ethers.provider;
    const code = await provider.getCode(contractAddress);

    console.log(`📍 Contract: ${contractAddress}`);
    console.log(`📄 Bytecode length: ${code.length} bytes`);
    console.log(`✅ Contract deployed: ${code !== '0x'}`);

    // Try to extract function selectors from bytecode
    console.log("\n🔍 Analyzing contract bytecode for function signatures...");

    // Common LayerZero OFT function selectors
    const knownSelectors = {
        "0x32e0d80b": "send(struct,struct,address)", // V2 struct-based
        "0x6a0f2c5b": "send(uint32,bytes32,uint256,uint256,bytes,struct,address)", // V1 individual
        "0x7d25a05e": "sendFrom(address,uint32,bytes32,uint256,uint256,bytes,struct,address)", // OFT Adapter
        "0x70a08231": "balanceOf(address)",
        "0x18160ddd": "totalSupply()",
        "0x06fdde03": "name()",
        "0x95d89b41": "symbol()",
        "0x313ce567": "decimals()",
        "0x5737619": "peers(uint32)",
        "0x3400288b": "setPeer(uint32,bytes32)",
        "0xb353aaa7": "lzEndpoint()",
        "0xa9059cbb": "transfer(address,uint256)",
        "0x095ea7b3": "approve(address,uint256)",
        "0x66dd0f24": "depositWETH(uint256)",
        "0xfc4dd333": "withdrawWETH(uint256)"
    };

    console.log("🔍 Checking for known function selectors in bytecode:");
    for (const [selector, signature] of Object.entries(knownSelectors)) {
        const selectorInCode = code.toLowerCase().includes(selector.slice(2));
        const status = selectorInCode ? "✅" : "❌";
        console.log(`${status} ${selector}: ${signature}`);
    }

    // Try basic contract calls to see what works
    console.log("\n🧪 Testing basic contract functions:");

    try {
        // Test balanceOf function
        const abi = ["function balanceOf(address) view returns (uint256)"];
        const contract = new ethers.Contract(contractAddress, abi, provider);
        const balance = await contract.balanceOf("0xc6A050a538a9E857B4DCb4A33436280c202F6941");
        console.log(`✅ balanceOf works: ${ethers.formatEther(balance)} tokens`);
    } catch (e) {
        console.log(`❌ balanceOf failed: ${e.message}`);
    }

    try {
        // Test peers function
        const abi = ["function peers(uint32) view returns (bytes32)"];
        const contract = new ethers.Contract(contractAddress, abi, provider);
        const peer = await contract.peers(40158); // zkEVM Cardona EID
        console.log(`✅ peers(40158) works: ${peer}`);
    } catch (e) {
        console.log(`❌ peers failed: ${e.message}`);
    }

    try {
        // Test lzEndpoint function
        const abi = ["function lzEndpoint() view returns (address)"];
        const contract = new ethers.Contract(contractAddress, abi, provider);
        const endpoint = await contract.lzEndpoint();
        console.log(`✅ lzEndpoint works: ${endpoint}`);
    } catch (e) {
        console.log(`❌ lzEndpoint failed: ${e.message}`);
    }
}

debugContract()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });