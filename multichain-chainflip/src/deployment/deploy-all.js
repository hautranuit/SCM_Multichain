const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 Starting complete multi-chain deployment...");
    console.log("=" * 60);
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    console.log("Account balance:", ethers.utils.formatEther(await deployer.getBalance()), "ETH");
    
    const deploymentAddresses = {};
    
    try {
        // Step 1: Deploy Hub Contract
        console.log("\n🌐 Step 1: Deploying EnhancedPolygonPoSHub...");
        const EnhancedHub = await ethers.getContractFactory("EnhancedPolygonPoSHub");
        const enhancedHub = await EnhancedHub.deploy(deployer.address);
        await enhancedHub.deployed();
        
        deploymentAddresses.hub = enhancedHub.address;
        console.log("✅ Hub deployed at:", enhancedHub.address);
        
        // Step 2: Deploy Manufacturer Chain
        console.log("\n🏭 Step 2: Deploying ManufacturerChain...");
        const ManufacturerChain = await ethers.getContractFactory("ManufacturerChain");
        const manufacturerChain = await ManufacturerChain.deploy(
            deployer.address,
            enhancedHub.address
        );
        await manufacturerChain.deployed();
        
        deploymentAddresses.manufacturer = manufacturerChain.address;
        console.log("✅ ManufacturerChain deployed at:", manufacturerChain.address);
        
        // Step 3: Deploy Transporter Chain
        console.log("\n🚛 Step 3: Deploying TransporterChain...");
        const TransporterChain = await ethers.getContractFactory("TransporterChain");
        const transporterChain = await TransporterChain.deploy(
            deployer.address,
            enhancedHub.address
        );
        await transporterChain.deployed();
        
        deploymentAddresses.transporter = transporterChain.address;
        console.log("✅ TransporterChain deployed at:", transporterChain.address);
        
        // Step 4: Deploy Buyer Chain
        console.log("\n🛒 Step 4: Deploying BuyerChain...");
        const BuyerChain = await ethers.getContractFactory("BuyerChain");
        const buyerChain = await BuyerChain.deploy(
            deployer.address,
            enhancedHub.address
        );
        await buyerChain.deployed();
        
        deploymentAddresses.buyer = buyerChain.address;
        console.log("✅ BuyerChain deployed at:", buyerChain.address);
        
        // Step 5: Register L2 contracts with Hub
        console.log("\n🔗 Step 5: Registering L2 contracts with Hub...");
        
        const MANUFACTURER_CHAIN_ID = 2001;
        const TRANSPORTER_CHAIN_ID = 2002;
        const BUYER_CHAIN_ID = 2003;
        
        await enhancedHub.registerChainContract(MANUFACTURER_CHAIN_ID, manufacturerChain.address, "manufacturer");
        console.log("✅ Registered ManufacturerChain");
        
        await enhancedHub.registerChainContract(TRANSPORTER_CHAIN_ID, transporterChain.address, "transporter");
        console.log("✅ Registered TransporterChain");
        
        await enhancedHub.registerChainContract(BUYER_CHAIN_ID, buyerChain.address, "buyer");
        console.log("✅ Registered BuyerChain");
        
        // Step 6: Setup initial roles and permissions
        console.log("\n⚙️  Step 6: Setting up roles and permissions...");
        
        // Manufacturer setup
        const MANUFACTURER_ROLE = await manufacturerChain.MANUFACTURER_ROLE();
        const QUALITY_INSPECTOR_ROLE = await manufacturerChain.QUALITY_INSPECTOR_ROLE();
        await manufacturerChain.grantRole(MANUFACTURER_ROLE, deployer.address);
        await manufacturerChain.grantRole(QUALITY_INSPECTOR_ROLE, deployer.address);
        console.log("✅ Granted roles on ManufacturerChain");
        
        // Transporter setup
        const TRANSPORTER_ROLE = await transporterChain.TRANSPORTER_ROLE();
        const VALIDATOR_ROLE = await transporterChain.VALIDATOR_ROLE();
        await transporterChain.grantRole(TRANSPORTER_ROLE, deployer.address);
        await transporterChain.grantRole(VALIDATOR_ROLE, deployer.address);
        await transporterChain.registerTransportNode(deployer.address, "primary", "Default Location");
        console.log("✅ Granted roles and registered node on TransporterChain");
        
        // Buyer setup
        const BUYER_ROLE = await buyerChain.BUYER_ROLE();
        const SELLER_ROLE = await buyerChain.SELLER_ROLE();
        const ARBITRATOR_ROLE = await buyerChain.ARBITRATOR_ROLE();
        await buyerChain.grantRole(BUYER_ROLE, deployer.address);
        await buyerChain.grantRole(SELLER_ROLE, deployer.address);
        await buyerChain.registerArbitrator(deployer.address);
        console.log("✅ Granted roles and registered arbitrator on BuyerChain");
        
        // Step 7: Register participants in Hub
        console.log("\n👥 Step 7: Registering participants in Hub...");
        
        await enhancedHub.registerParticipant(
            deployer.address,
            "manufacturer",
            MANUFACTURER_CHAIN_ID,
            manufacturerChain.address
        );
        console.log("✅ Registered deployer as manufacturer");
        
        // Step 8: Fund contracts for incentives
        console.log("\n💰 Step 8: Funding contracts...");
        
        const hubFunding = ethers.utils.parseEther("2.0");
        const manufacturerFunding = ethers.utils.parseEther("1.0");
        const transporterFunding = ethers.utils.parseEther("2.0");
        const buyerFunding = ethers.utils.parseEther("5.0");
        
        await deployer.sendTransaction({ to: enhancedHub.address, value: hubFunding });
        await deployer.sendTransaction({ to: manufacturerChain.address, value: manufacturerFunding });
        await deployer.sendTransaction({ to: transporterChain.address, value: transporterFunding });
        await deployer.sendTransaction({ to: buyerChain.address, value: buyerFunding });
        
        console.log("✅ All contracts funded");
        
        // Step 9: Verify deployments
        console.log("\n🔍 Step 9: Verifying deployments...");
        
        const hubName = await enhancedHub.name();
        const manufacturerName = await manufacturerChain.name();
        
        console.log("✅ Hub contract name:", hubName);
        console.log("✅ Manufacturer contract name:", manufacturerName);
        
        // Final Summary
        console.log("\n🎉 DEPLOYMENT COMPLETE!");
        console.log("=" * 60);
        console.log("📝 Deployment Summary:");
        console.log("Network:", network.name);
        console.log("Chain ID:", network.config.chainId);
        console.log("Deployer:", deployer.address);
        console.log("");
        console.log("📍 Contract Addresses:");
        console.log("Hub (EnhancedPolygonPoSHub):", deploymentAddresses.hub);
        console.log("Manufacturer (ManufacturerChain):", deploymentAddresses.manufacturer);
        console.log("Transporter (TransporterChain):", deploymentAddresses.transporter);
        console.log("Buyer (BuyerChain):", deploymentAddresses.buyer);
        console.log("");
        console.log("🔗 Chain IDs:");
        console.log("Manufacturer Chain ID:", MANUFACTURER_CHAIN_ID);
        console.log("Transporter Chain ID:", TRANSPORTER_CHAIN_ID);
        console.log("Buyer Chain ID:", BUYER_CHAIN_ID);
        console.log("=" * 60);
        
        // Save comprehensive deployment info
        const fullDeploymentInfo = {
            network: network.name,
            chainId: network.config.chainId,
            deployer: deployer.address,
            timestamp: new Date().toISOString(),
            contracts: {
                hub: {
                    address: deploymentAddresses.hub,
                    name: "EnhancedPolygonPoSHub",
                    chainId: network.config.chainId
                },
                manufacturer: {
                    address: deploymentAddresses.manufacturer,
                    name: "ManufacturerChain",
                    assignedChainId: MANUFACTURER_CHAIN_ID
                },
                transporter: {
                    address: deploymentAddresses.transporter,
                    name: "TransporterChain",
                    assignedChainId: TRANSPORTER_CHAIN_ID
                },
                buyer: {
                    address: deploymentAddresses.buyer,
                    name: "BuyerChain",
                    assignedChainId: BUYER_CHAIN_ID
                }
            },
            algorithms: {
                "Algorithm 1": "Payment Release and Incentive Mechanism - Implemented across all chains",
                "Algorithm 2": "Dispute Resolution and Voting Mechanism - Implemented in BuyerChain and TransporterChain",
                "Algorithm 3": "Supply Chain Consensus Algorithm - Implemented in TransporterChain",
                "Algorithm 4": "Product Authenticity Verification - Implemented in ManufacturerChain",
                "Algorithm 5": "Post Supply Chain Management - Implemented in BuyerChain"
            },
            flModels: [
                "anomaly_detection",
                "counterfeit_detection",
                "quality_prediction", 
                "route_optimization",
                "fraud_detection"
            ]
        };
        
        console.log("\n💾 Saving complete deployment info...");
        const fs = require('fs');
        fs.writeFileSync('deployment-complete.json', JSON.stringify(fullDeploymentInfo, null, 2));
        
        return deploymentAddresses;
        
    } catch (error) {
        console.error("❌ Deployment failed:", error);
        throw error;
    }
}

main()
    .then((addresses) => {
        console.log("\n🚀 Multi-chain deployment successful!");
        console.log("📋 Save these addresses for your .env file:");
        console.log(`HUB_CONTRACT_ADDRESS=${addresses.hub}`);
        console.log(`MANUFACTURER_CONTRACT_ADDRESS=${addresses.manufacturer}`);
        console.log(`TRANSPORTER_CONTRACT_ADDRESS=${addresses.transporter}`);
        console.log(`BUYER_CONTRACT_ADDRESS=${addresses.buyer}`);
        process.exit(0);
    })
    .catch((error) => {
        console.error("💥 Complete deployment failed:", error);
        process.exit(1);
    });