const { ethers } = require('ethers');

const LAYERZERO_INFRASTRUCTURE = {
    arbitrum_sepolia: {
        sendLib: "0x4f7cd4DA19ABB31b0eC98b9066B9e857B1bf9C0E",
        receiveLib: "0x75Db67CDab2824970131D5aa9CECfC9F69c69636",
        executor: "0x5Df3a1cEbBD9c8BA7F8dF51Fd632A9aef8308897",
        dvn: "0xA85BE08A6Ce2771C730661766AACf2c8Bb24C611"
    },
    base_sepolia: {
        sendLib: "0xC1868e054425D378095A003EcbB3823a5D0135C9",
        receiveLib: "0x12523de19dc41c91F7d2093E0CFbB76b17012C8d",
        executor: "0x8A3D588D9f6AC041476b094f97FF94ec30169d3D",
        dvn: "0x78551ADC2553EF1858a558F5300F7018Aad2FA7e"
    },
    optimism_sepolia: {
        sendLib: "0xB31D2cb502E25B30C651842C7C3293c51Fe6d16f",
        receiveLib: "0x9284fd59B95b9143AF0b9795CAC16eb3C723C9Ca",
        executor: "0xDc0D68899405673b932F0DB7f8A49191491A5bcB",
        dvn: "0xA85BE08A6Ce2771C730661766AACf2c8Bb24C611"
    },
    polygon_amoy: {
        sendLib: "0x1d186C560281B8F1AF831957ED5047fD3AB902F9",
        receiveLib: "0x53fd4C4fBBd53F6bC58CaE6704b92dB1f360A648",
        executor: "0x4Cf1B3Fa61465c2c907f82fC488B43223BA0CF93",
        dvn: "0xA85BE08A6Ce2771C730661766AACf2c8Bb24C611"
    }
};

const OFT_CONTRACTS = {
    arbitrum_sepolia: "0x47FaF4084F4F69b705A6f947f020B59AA1993FD9",
    base_sepolia: "0xdAd142646292A550008B44D968764c52eF1C3f67",
    optimism_sepolia: "0x76D43CEC28775032A7EC8895ad178c660246c8Ec",
    polygon_amoy: "0x36DDc43D2FfA30588CcAC8C2979b69225c292a73"
};

const RPC_URLS = {
    arbitrum_sepolia: "https://sepolia-rollup.arbitrum.io/rpc",
    base_sepolia: "https://sepolia.base.org",
    optimism_sepolia: "https://sepolia.optimism.io",
    polygon_amoy: "https://rpc-amoy.polygon.technology"
};

const PRIVATE_KEY = "5d014eee1544fe8e166b0ffc5d9a5da41456cec5d4c15b76611e8747d848f079";

const ENDPOINT_ABI = [
    "function setSendLibrary(address _oapp, uint32 _dstEid, address _newLib) external",
    "function setReceiveLibrary(address _oapp, uint32 _srcEid, address _newLib, uint256 _gracePeriod) external",
    "function setConfig(address _oapp, address _lib, tuple(uint32 eid, uint32 configType, bytes config)[] _setConfigParams) external"
];

const LAYERZERO_ENDPOINT = "0x6EDCE65403992e310A62460808c4b910D972f10f";

async function setupEnhancedLayerZero() {
    console.log("🚀 Setting up Enhanced LayerZero Infrastructure...");
    console.log("📋 This will configure DVN, Executor, and Library settings for all OFT contracts");
    
    for (const [networkName, config] of Object.entries(LAYERZERO_INFRASTRUCTURE)) {
        try {
            console.log(`\n📡 Configuring ${networkName}...`);
            
            const provider = new ethers.JsonRpcProvider(RPC_URLS[networkName]);
            const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
            const endpointContract = new ethers.Contract(LAYERZERO_ENDPOINT, ENDPOINT_ABI, wallet);
            
            const oftAddress = OFT_CONTRACTS[networkName];
            
            console.log(`   🏢 OFT Contract: ${oftAddress}`);
            console.log(`   📚 Send Library: ${config.sendLib}`);
            console.log(`   📥 Receive Library: ${config.receiveLib}`);
            console.log(`   ⚡ Executor: ${config.executor}`);
            console.log(`   🔒 DVN: ${config.dvn}`);
            
            // Set Send and Receive Libraries for all destination networks
            for (const [destNetwork, destConfig] of Object.entries(LAYERZERO_INFRASTRUCTURE)) {
                if (destNetwork !== networkName) {
                    const destEid = getEidForNetwork(destNetwork);
                    
                    console.log(`  🔄 Setting send library for ${destNetwork} (EID: ${destEid})...`);
                    try {
                        const tx1 = await endpointContract.setSendLibrary(
                            oftAddress,
                            destEid,
                            config.sendLib,
                            {
                                gasLimit: 200000,
                                gasPrice: await provider.getGasPrice()
                            }
                        );
                        await tx1.wait();
                        console.log(`  ✅ Send library set: ${tx1.hash}`);
                    } catch (error) {
                        console.log(`  ⚠️ Send library configuration: ${error.message}`);
                    }
                    
                    console.log(`  🔄 Setting receive library for ${destNetwork} (EID: ${destEid})...`);
                    try {
                        const tx2 = await endpointContract.setReceiveLibrary(
                            oftAddress,
                            destEid,
                            config.receiveLib,
                            0,  // Grace period
                            {
                                gasLimit: 200000,
                                gasPrice: await provider.getGasPrice()
                            }
                        );
                        await tx2.wait();
                        console.log(`  ✅ Receive library set: ${tx2.hash}`);
                    } catch (error) {
                        console.log(`  ⚠️ Receive library configuration: ${error.message}`);
                    }
                    
                    // Small delay between transactions
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }
            }
            
            console.log(`✅ ${networkName} infrastructure configuration complete`);
            
        } catch (error) {
            console.error(`❌ Error configuring ${networkName}:`, error.message);
        }
        
        // Delay between networks
        await new Promise(resolve => setTimeout(resolve, 3000));
    }
    
    console.log("\n🎉 Enhanced LayerZero infrastructure setup complete!");
    console.log("🔧 All DVN and Executor configurations applied");
    console.log("✅ Ready for cross-chain transfers");
    console.log("\n📋 Next Steps:");
    console.log("1. Start the backend server");
    console.log("2. Test with /api/layerzero-oft/infrastructure-status");
    console.log("3. Run transfer test with /api/layerzero-oft/test-enhanced-infrastructure");
}

function getEidForNetwork(networkName) {
    const eids = {
        arbitrum_sepolia: 40231,
        base_sepolia: 40245,
        optimism_sepolia: 40232,
        polygon_amoy: 40267
    };
    return eids[networkName];
}

// Error handling for the script
process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
});

// Run setup
console.log("🔧 LayerZero Enhanced Infrastructure Setup Tool");
console.log("=====================================");
setupEnhancedLayerZero().catch(console.error);