const hre = require("hardhat");
const { ethers } = require("hardhat");

// LayerZero V2 Endpoints
const LAYERZERO_ENDPOINTS = {
    optimismSepolia: "0x6EDCE65403992e310A62460808c4b910D972f10f",
    arbitrumSepolia: "0x6EDCE65403992e310A62460808c4b910D972f10f", 
    amoy: "0x6EDCE65403992e310A62460808c4b910D972f10f",
    cardona: "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3"
};

async function main() {
    console.log("🚀 Deploying Separated OFT + Wrapper Architecture...");

    try {
        const [deployer] = await ethers.getSigners();
        const network = hre.network.name;

        console.log(`Network: ${network}`);
        console.log(`Deployer: ${deployer.address}`);
        
        const balance = await deployer.getBalance();
        console.log(`Deployer balance: ${ethers.utils.formatEther(balance)} ETH`);

        const lzEndpoint = LAYERZERO_ENDPOINTS[network];
        if (!lzEndpoint) {
            throw new Error(`Unsupported network: ${network}`);
        }

        console.log(`LayerZero Endpoint: ${lzEndpoint}`);

        // Verify endpoint
        const code = await ethers.provider.getCode(lzEndpoint);
        if (code === "0x") {
            throw new Error(`LayerZero endpoint ${lzEndpoint} is not a contract`);
        }
        console.log(`✅ LayerZero endpoint verified`);

        // Step 1: Deploy Pure OFT Contract
        console.log("\n📦 Step 1: Deploying Pure ChainFlipOFT...");
        const ChainFlipOFT = await ethers.getContractFactory("ChainFlipOFT");
        
        const oft = await ChainFlipOFT.deploy(
            "ChainFLIP WETH",
            "cfWETH",
            lzEndpoint,
            deployer.address,
            {
                gasLimit: 5000000
            }
        );

        console.log("⏳ Waiting for OFT deployment...");
        await oft.deployed();
        
        console.log(`✅ ChainFlipOFT deployed at: ${oft.address}`);

        // Test basic OFT functionality
        const name = await oft.name();
        const symbol = await oft.symbol();
        const owner = await oft.owner();
        
        console.log(`- Name: ${name}`);
        console.log(`- Symbol: ${symbol}`);
        console.log(`- Owner: ${owner}`);

        // Step 2: Deploy ETH Wrapper Contract
        console.log("\n📦 Step 2: Deploying ETH Wrapper...");
        const ETHWrapper = await ethers.getContractFactory("ETHWrapper");
        
        const wrapper = await ETHWrapper.deploy(oft.address, {
            gasLimit: 3000000
        });

        console.log("⏳ Waiting for Wrapper deployment...");
        await wrapper.deployed();
        
        console.log(`✅ ETHWrapper deployed at: ${wrapper.address}`);

        // Step 3: Configure Permissions
        console.log("\n🔧 Step 3: Configuring permissions...");
        
        // Transfer OFT ownership to wrapper so it can mint/burn
        console.log("Transferring OFT ownership to wrapper...");
        const transferTx = await oft.transferOwnership(wrapper.address);
        await transferTx.wait();
        console.log("✅ OFT ownership transferred to wrapper");

        // Step 4: Add initial liquidity to wrapper
        console.log("\n💰 Step 4: Adding initial liquidity...");
        const liquidityAmount = ethers.utils.parseEther("0.1"); // 0.1 ETH
        
        const liquidityTx = await wrapper.addLiquidity({
            value: liquidityAmount,
            gasLimit: 100000
        });
        await liquidityTx.wait();
        console.log(`✅ Added ${ethers.utils.formatEther(liquidityAmount)} ETH liquidity`);

        // Step 5: Test the system
        console.log("\n🧪 Step 5: Testing the system...");
        
        const contractBalance = await wrapper.getContractBalance();
        console.log(`Contract ETH balance: ${ethers.utils.formatEther(contractBalance)} ETH`);

        // Deployment summary
        const deploymentInfo = {
            network: network,
            oft: {
                address: oft.address,
                name: name,
                symbol: symbol,
                owner: await oft.owner()
            },
            wrapper: {
                address: wrapper.address,
                ethBalance: ethers.utils.formatEther(contractBalance)
            },
            lzEndpoint: lzEndpoint,
            deployer: deployer.address,
            timestamp: new Date().toISOString()
        };
        
        console.log("\n🎉 DEPLOYMENT SUCCESSFUL!");
        console.log("📄 Summary:", JSON.stringify(deploymentInfo, null, 2));

        console.log("\n🚀 Next Steps:");
        console.log("1. Deploy on other networks using the same script");
        console.log("2. Set up peer connections between networks");
        console.log("3. Users can:");
        console.log(`   - Deposit ETH: wrapper.deposit() at ${wrapper.address}`);
        console.log(`   - Withdraw ETH: wrapper.withdraw(amount) at ${wrapper.address}`);
        console.log(`   - Cross-chain transfer: Use LayerZero OFT at ${oft.address}`);

        return {
            oft: oft.address,
            wrapper: wrapper.address,
            network: network
        };
        
    } catch (error) {
        console.error("❌ Deployment failed:", error.message);
        if (error.data) {
            console.error("Error data:", error.data);
        }
        throw error;
    }
}

main().catch(console.error);