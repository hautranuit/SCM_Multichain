const { ethers } = require("hardhat");

const LAYERZERO_ENDPOINTS = {
    optimismSepolia: "0x6Ac7bdc07A0583A362F1497252872AE6c0A5F5B8",
    arbitrumSepolia: "0x6EDCE65403992e310A62460808c4b910D972f10f",
    amoy: "0x6Ac7bdc07A0583A362F1497252872AE6c0A5F5B8",
    cardona: "0x6098e96a28E02f27B1e6BD381f870F1C8Bd169d3"
};

async function main() {
    console.log("🚀 Deploying REAL LayerZero OFT Contract...");

    const [deployer] = await ethers.getSigners();
    const network = hre.network.name;

    console.log(`Network: ${network}`);
    console.log(`Deployer: ${deployer.address}`);

    const lzEndpoint = LAYERZERO_ENDPOINTS[network];
    if (!lzEndpoint) {
        console.log(`❌ Unsupported network: ${network}`);
        return;
    }

    console.log(`LayerZero Endpoint: ${lzEndpoint}`);

    const RealChainFlipOFT = await ethers.getContractFactory("RealChainFlipOFT");
    const oft = await RealChainFlipOFT.deploy(
        "ChainFLIP WETH",
        "cfWETH",
        lzEndpoint,
        deployer.address
    );

    await oft.waitForDeployment();
    const oftAddress = await oft.getAddress();

    console.log(`✅ Deployed at: ${oftAddress}`);
    console.log(`✅ Real LayerZero OFT with deposit/withdraw functionality!`);
}

main().catch(console.error);