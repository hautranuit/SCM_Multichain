const { ethers } = require('ethers');

// LayerZero Endpoint V2 ABI for configuration
const ENDPOINT_ABI = [
    {
        "inputs": [
            {"name": "_oapp", "type": "address"},
            {"name": "_config", "type": "tuple", "components": [
                {"name": "eid", "type": "uint32"},
                {"name": "configType", "type": "uint32"},
                {"name": "config", "type": "bytes"}
            ]}
        ],
        "name": "setConfig",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
];

// Wrapper ABI to call endpoint configuration as owner
const WRAPPER_ABI = [
    {
        "inputs": [
            {"name": "_oapp", "type": "address"},
            {"name": "_config", "type": "tuple", "components": [
                {"name": "eid", "type": "uint32"},
                {"name": "configType", "type": "uint32"},
                {"name": "config", "type": "bytes"}
            ]}
        ],
        "name": "setConfig",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
];

const PRIVATE_KEY = "5d014eee1544fe8e166b0ffc5d9a5da41456cec5d4c15b76611e8747d848f079";

// LayerZero configuration constants
const CONFIG_TYPES = {
    SEND_LIBRARY: 1,
    RECEIVE_LIBRARY: 2,
    EXECUTOR: 3,
    DVN: 4
};

// Complete LayerZero V2 configuration
const NETWORKS = {
    optimism_sepolia: {
        oft: "0x6478eAB366A16d96ae910fd16F6770DDa1845648",
        wrapper: "0x5428793EBd36693c993D6B3f8f2641C46121ec29",
        rpc: "https://sepolia.optimism.io",
        eid: 40232,
        endpoint: "0x6EDCE65403992e310A62460808c4b910D972f10f",
        sendLib: "0xB31D2cb502E25B30C651842C7C3293c51Fe6d16f",
        receiveLib: "0x9284fd59B95b9143AF0b9795CAC16eb3C723C9Ca",
        executor: "0xDc0D68899405673b932F0DB7f8A49191491A5bcB",
        blockedMessageLib: "0x0c77d8d771ab35e2e184e7ce127f19ced31ff8c0"
    },
    arbitrum_sepolia: {
        oft: "0x441C06d8548De93d64072F781e15E16A7c316b67",
        wrapper: "0x5952569276eA7f7eF95B910EAd0a67067A518188",
        rpc: "https://arbitrum-sepolia.drpc.org",
        eid: 40231,
        endpoint: "0x6EDCE65403992e310A62460808c4b910D972f10f",
        sendLib: "0x4f7cd4DA19ABB31b0eC98b9066B9e857B1bf9C0E",
        receiveLib: "0x75Db67CDab2824970131D5aa9CECfC9F69c69636",
        executor: "0x5Df3a1cEbBD9c8BA7F8dF51Fd632A9aef8308897",
        dvn: "0xA85BE08A6Ce2771C730661766AACf2c8Bb24C611",
        readLib: "0x54320b901FDe49Ba98de821Ccf374BA4358a8bf6",
        blockedMessageLib: "0x0c77d8d771ab35e2e184e7ce127f19ced31ff8c0"
    },
    polygon_amoy: {
        oft: "0x865F1Dac1d8E17f492FFce578095b49f3D604ad4",
        wrapper: "0xA471c665263928021AF5aa7852724b6f757005e1",
        rpc: "https://rpc-amoy.polygon.technology",
        eid: 40267,
        endpoint: "0x6EDCE65403992e310A62460808c4b910D972f10f",
        sendLib: "0x1d186C560281B8F1AF831957ED5047fD3AB902F9",
        receiveLib: "0x53fd4C4fBBd53F6bC58CaE6704b92dB1f360A648",
        executor: "0x4Cf1B3Fa61465c2c907f82fC488B43223BA0CF93",
        blockedMessageLib: "0x0c77d8d771ab35e2e184e7ce127f19ced31ff8c0"
    }
};

function createProvider(rpc) {
    if (ethers.JsonRpcProvider) {
        return new ethers.JsonRpcProvider(rpc);
    } else if (ethers.providers && ethers.providers.JsonRpcProvider) {
        return new ethers.providers.JsonRpcProvider(rpc);
    } else {
        throw new Error("Could not create provider");
    }
}

function createWallet(privateKey, provider) {
    return new ethers.Wallet(privateKey, provider);
}

// Encode configuration data for LayerZero V2
function encodeConfig(address) {
    // Simple address encoding - LayerZero V2 typically expects addresses as 32-byte values
    return ethers.zeroPadValue ? ethers.zeroPadValue(address, 32) : ethers.utils.hexZeroPad(address, 32);
}

async function setupLayerZeroConfiguration() {
    console.log("🔧 Setting up LayerZero V2 Configuration for OFT Contracts...\n");
    
    const results = [];
    
    for (const [chainName, config] of Object.entries(NETWORKS)) {
        console.log(`\n📡 Configuring ${chainName.toUpperCase()}:`);
        console.log(`   OFT: ${config.oft}`);
        console.log(`   Wrapper: ${config.wrapper}`);
        console.log(`   Endpoint: ${config.endpoint}`);
        
        try {
            const provider = createProvider(config.rpc);
            const wallet = createWallet(PRIVATE_KEY, provider);
            const endpointContract = new ethers.Contract(config.endpoint, ENDPOINT_ABI, wallet);
            
            // Configure for each target chain
            for (const [targetChain, targetConfig] of Object.entries(NETWORKS)) {
                if (targetChain !== chainName) {
                    console.log(`\n   🎯 Setting up config for target: ${targetChain} (EID: ${targetConfig.eid})`);
                    
                    try {
                        // 1. Configure Send Library
                        console.log(`      📤 Configuring Send Library: ${config.sendLib}`);
                        const sendLibConfig = {
                            eid: targetConfig.eid,
                            configType: CONFIG_TYPES.SEND_LIBRARY,
                            config: encodeConfig(config.sendLib)
                        };
                        
                        const sendTx = await endpointContract.setConfig(config.oft, sendLibConfig, {
                            gasLimit: 500000
                        });
                        console.log(`         TX: ${sendTx.hash}`);
                        await sendTx.wait();
                        console.log(`         ✅ Send library configured`);
                        
                        // Wait between transactions
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        
                        // 2. Configure Receive Library
                        console.log(`      📥 Configuring Receive Library: ${config.receiveLib}`);
                        const receiveLibConfig = {
                            eid: targetConfig.eid,
                            configType: CONFIG_TYPES.RECEIVE_LIBRARY,
                            config: encodeConfig(config.receiveLib)
                        };
                        
                        const receiveTx = await endpointContract.setConfig(config.oft, receiveLibConfig, {
                            gasLimit: 500000
                        });
                        console.log(`         TX: ${receiveTx.hash}`);
                        await receiveTx.wait();
                        console.log(`         ✅ Receive library configured`);
                        
                        // Wait between transactions
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        
                        // 3. Configure Executor
                        console.log(`      ⚡ Configuring Executor: ${config.executor}`);
                        const executorConfig = {
                            eid: targetConfig.eid,
                            configType: CONFIG_TYPES.EXECUTOR,
                            config: encodeConfig(config.executor)
                        };
                        
                        const executorTx = await endpointContract.setConfig(config.oft, executorConfig, {
                            gasLimit: 500000
                        });
                        console.log(`         TX: ${executorTx.hash}`);
                        await executorTx.wait();
                        console.log(`         ✅ Executor configured`);
                        
                        // Wait between transactions
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        
                        // 4. Configure DVN (if available)
                        if (config.dvn) {
                            console.log(`      🔐 Configuring DVN: ${config.dvn}`);
                            const dvnConfig = {
                                eid: targetConfig.eid,
                                configType: CONFIG_TYPES.DVN,
                                config: encodeConfig(config.dvn)
                            };
                            
                            const dvnTx = await endpointContract.setConfig(config.oft, dvnConfig, {
                                gasLimit: 500000
                            });
                            console.log(`         TX: ${dvnTx.hash}`);
                            await dvnTx.wait();
                            console.log(`         ✅ DVN configured`);
                            
                            await new Promise(resolve => setTimeout(resolve, 2000));
                        }
                        
                        results.push({
                            from: chainName,
                            to: targetChain,
                            status: 'success',
                            configured: ['sendLib', 'receiveLib', 'executor', config.dvn ? 'dvn' : null].filter(Boolean)
                        });
                        
                    } catch (error) {
                        console.log(`      ❌ Error configuring for ${targetChain}: ${error.message}`);
                        results.push({
                            from: chainName,
                            to: targetChain,
                            status: 'error',
                            error: error.message
                        });
                    }
                }
            }
            
        } catch (error) {
            console.log(`   ❌ Failed to configure ${chainName}: ${error.message}`);
        }
    }
    
    console.log("\n" + "=".repeat(80));
    console.log("📊 LAYERZERO CONFIGURATION RESULTS:");
    console.log("=".repeat(80));
    
    for (const result of results) {
        const statusIcon = result.status === 'success' ? '✅' : '❌';
        console.log(`${statusIcon} ${result.from} → ${result.to}: ${result.status}`);
        if (result.configured) {
            console.log(`   Configured: ${result.configured.join(', ')}`);
        }
        if (result.error) {
            console.log(`   Error: ${result.error}`);
        }
    }
    
    const successCount = results.filter(r => r.status === 'success').length;
    console.log(`\n🎯 Successfully configured ${successCount}/${results.length} LayerZero connections`);
    
    if (successCount > 0) {
        console.log("\n🧪 Now test the fee estimation again:");
        console.log("   The quoteSend should work after proper LayerZero configuration!");
    }
}

setupLayerZeroConfiguration().catch(console.error);
