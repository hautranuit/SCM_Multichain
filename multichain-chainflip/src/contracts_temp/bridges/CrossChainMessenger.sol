// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "./LayerZeroConfig.sol";
import "./FxPortalBridge.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title CrossChainMessenger
 * @dev Unified cross-chain messaging system combining LayerZero and FxPortal
 * Handles routing messages to appropriate bridge based on target chain
 */
contract CrossChainMessenger is AccessControl, ReentrancyGuard {
    
    // Bridge contracts
    LayerZeroConfig public layerZeroConfig;
    FxPortalBridge public fxPortalBridge;
    
    // Roles
    bytes32 public constant BRIDGE_OPERATOR_ROLE = keccak256("BRIDGE_OPERATOR_ROLE");
    bytes32 public constant HUB_CONTRACT_ROLE = keccak256("HUB_CONTRACT_ROLE");
    
    // Chain configuration
    struct ChainConfig {
        uint256 chainId;
        BridgeType bridgeType;
        bool isActive;
        address contractAddress;
        string name;
    }
    
    enum BridgeType {
        LAYER_ZERO,
        FX_PORTAL
    }
    
    // Chain configurations
    mapping(uint256 => ChainConfig) public chainConfigs;
    uint256[] public supportedChains;
    
    // Message tracking
    struct UnifiedMessage {
        uint256 messageId;
        uint256 sourceChain;
        uint256 targetChain;
        BridgeType bridgeType;
        bytes32 dataHash;
        bytes payload;
        bool processed;
        uint256 timestamp;
    }
    
    mapping(uint256 => UnifiedMessage) public messages;
    uint256 private nextMessageId = 1;
    
    // Events
    event MessageRouted(
        uint256 indexed messageId,
        uint256 indexed sourceChain,
        uint256 indexed targetChain,
        BridgeType bridgeType,
        bytes32 dataHash
    );
    
    event MessageProcessed(
        uint256 indexed messageId,
        bool success,
        string result
    );
    
    event ChainConfigured(
        uint256 indexed chainId,
        BridgeType bridgeType,
        address contractAddress,
        string name
    );
    
    constructor(address initialAdmin) {
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(BRIDGE_OPERATOR_ROLE, initialAdmin);
        
        // Initialize chain configurations
        _initializeChainConfigs();
    }
    
    function _initializeChainConfigs() internal {
        // Hub: Polygon Amoy (supports both bridges as source)
        chainConfigs[80002] = ChainConfig({
            chainId: 80002,
            bridgeType: BridgeType.LAYER_ZERO, // Default for hub
            isActive: true,
            contractAddress: address(0), // Will be set when deployed
            name: "Polygon Amoy Hub"
        });
        supportedChains.push(80002);
        
        // Manufacturer: zkEVM Cardona (FxPortal)
        chainConfigs[2442] = ChainConfig({
            chainId: 2442,
            bridgeType: BridgeType.FX_PORTAL,
            isActive: true,
            contractAddress: address(0), // Will be set when deployed
            name: "zkEVM Cardona Manufacturer"
        });
        supportedChains.push(2442);
        
        // Transporter: Arbitrum Sepolia (LayerZero)
        chainConfigs[421614] = ChainConfig({
            chainId: 421614,
            bridgeType: BridgeType.LAYER_ZERO,
            isActive: true,
            contractAddress: address(0), // Will be set when deployed
            name: "Arbitrum Sepolia Transporter"
        });
        supportedChains.push(421614);
        
        // Buyer: Optimism Sepolia (LayerZero)
        chainConfigs[11155420] = ChainConfig({
            chainId: 11155420,
            bridgeType: BridgeType.LAYER_ZERO,
            isActive: true,
            contractAddress: address(0), // Will be set when deployed
            name: "Optimism Sepolia Buyer"
        });
        supportedChains.push(11155420);
    }
    
    // Set bridge contract addresses
    function setBridgeContracts(
        address _layerZeroConfig,
        address _fxPortalBridge
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        layerZeroConfig = LayerZeroConfig(_layerZeroConfig);
        fxPortalBridge = FxPortalBridge(_fxPortalBridge);
    }
    
    // Send cross-chain message (unified entry point)
    function sendCrossChainMessage(
        uint256 targetChainId,
        bytes32 dataHash,
        bytes calldata payload
    ) external payable onlyRole(HUB_CONTRACT_ROLE) nonReentrant returns (uint256) {
        require(chainConfigs[targetChainId].isActive, "Target chain not supported");
        
        uint256 messageId = nextMessageId++;
        BridgeType bridgeType = chainConfigs[targetChainId].bridgeType;
        
        messages[messageId] = UnifiedMessage({
            messageId: messageId,
            sourceChain: block.chainid,
            targetChain: targetChainId,
            bridgeType: bridgeType,
            dataHash: dataHash,
            payload: payload,
            processed: false,
            timestamp: block.timestamp
        });
        
        // Route to appropriate bridge
        if (bridgeType == BridgeType.LAYER_ZERO) {
            _sendViaLayerZero(messageId, targetChainId, dataHash, payload);
        } else if (bridgeType == BridgeType.FX_PORTAL) {
            _sendViaFxPortal(messageId, targetChainId, dataHash, payload);
        } else {
            revert("Unsupported bridge type");
        }
        
        emit MessageRouted(messageId, block.chainid, targetChainId, bridgeType, dataHash);
        return messageId;
    }
    
    // Send via LayerZero
    function _sendViaLayerZero(
        uint256 messageId,
        uint256 targetChainId,
        bytes32 dataHash,
        bytes calldata payload
    ) internal {
        require(address(layerZeroConfig) != address(0), "LayerZero not configured");
        
        // Determine message type based on target chain
        LayerZeroConfig.MessageType msgType;
        if (targetChainId == 421614) { // Arbitrum Sepolia (Transporter)
            msgType = LayerZeroConfig.MessageType.SHIPMENT_UPDATE;
        } else if (targetChainId == 11155420) { // Optimism Sepolia (Buyer)
            msgType = LayerZeroConfig.MessageType.PURCHASE_UPDATE;
        } else {
            msgType = LayerZeroConfig.MessageType.PRODUCT_SYNC;
        }
        
        layerZeroConfig.sendMessage{value: msg.value}(
            targetChainId,
            msgType,
            dataHash,
            payload
        );
    }
    
    // Send via FxPortal
    function _sendViaFxPortal(
        uint256 messageId,
        uint256 targetChainId,
        bytes32 dataHash,
        bytes calldata payload
    ) internal {
        require(address(fxPortalBridge) != address(0), "FxPortal not configured");
        require(targetChainId == 2442, "FxPortal only for zkEVM Cardona");
        
        // Determine message type for manufacturer chain
        FxPortalBridge.MessageType msgType = FxPortalBridge.MessageType.PRODUCT_REGISTRATION;
        
        fxPortalBridge.sendMessageToChild(msgType, dataHash, payload);
    }
    
    // Process received message (called by bridge contracts)
    function processReceivedMessage(
        uint256 messageId,
        uint256 sourceChainId,
        bytes32 dataHash,
        bytes calldata payload
    ) external onlyRole(BRIDGE_OPERATOR_ROLE) {
        // Verify message and process
        bytes32 expectedHash = keccak256(payload);
        require(expectedHash == dataHash, "Data hash mismatch");
        
        // Mark as processed
        if (messages[messageId].messageId != 0) {
            messages[messageId].processed = true;
        }
        
        emit MessageProcessed(messageId, true, "Message processed successfully");
    }
    
    // Configuration functions
    function updateChainConfig(
        uint256 chainId,
        BridgeType bridgeType,
        bool isActive,
        address contractAddress,
        string memory name
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        chainConfigs[chainId] = ChainConfig({
            chainId: chainId,
            bridgeType: bridgeType,
            isActive: isActive,
            contractAddress: contractAddress,
            name: name
        });
        
        // Add to supported chains if not already there
        bool exists = false;
        for (uint i = 0; i < supportedChains.length; i++) {
            if (supportedChains[i] == chainId) {
                exists = true;
                break;
            }
        }
        if (!exists) {
            supportedChains.push(chainId);
        }
        
        emit ChainConfigured(chainId, bridgeType, contractAddress, name);
    }
    
    // View functions
    function getMessage(uint256 messageId) external view returns (UnifiedMessage memory) {
        return messages[messageId];
    }
    
    function getSupportedChains() external view returns (uint256[] memory) {
        return supportedChains;
    }
    
    function getChainConfig(uint256 chainId) external view returns (ChainConfig memory) {
        return chainConfigs[chainId];
    }
    
    function isChainSupported(uint256 chainId) external view returns (bool) {
        return chainConfigs[chainId].isActive;
    }
    
    function getBridgeType(uint256 chainId) external view returns (BridgeType) {
        return chainConfigs[chainId].bridgeType;
    }
}
