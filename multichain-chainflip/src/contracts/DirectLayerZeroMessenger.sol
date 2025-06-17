// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title ILayerZeroEndpoint
 * @dev LayerZero endpoint interface
 */
interface ILayerZeroEndpoint {
    function send(
        uint16 _dstChainId,
        bytes calldata _destination,
        bytes calldata _payload,
        address payable _refundAddress,
        address _zroPaymentAddress,
        bytes calldata _adapterParams
    ) external payable;
    
    function estimateFees(
        uint16 _dstChainId,
        address _userApplication,
        bytes calldata _payload,
        bool _payInZRO,
        bytes calldata _adapterParam
    ) external view returns (uint nativeFee, uint zroFee);
}

/**
 * @title DirectLayerZeroMessenger
 * @dev Simplified LayerZero messaging contract for ChainFLIP multi-chain CID sync
 * Supports cross-chain messaging across 4 chains:
 * - Base Sepolia (40245): Manufacturer chain
 * - OP Sepolia (40232): Buyer chain  
 * - Arbitrum Sepolia (40231): Additional chain
 * - Polygon Amoy (40267): Hub chain
 */
contract DirectLayerZeroMessenger is AccessControl, ReentrancyGuard {
    
    // LayerZero endpoint
    ILayerZeroEndpoint public immutable lzEndpoint;
    
    // Roles
    bytes32 public constant SENDER_ROLE = keccak256("SENDER_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    
    // Chain and endpoint configurations
    struct ChainConfig {
        uint16 layerZeroEid;
        uint256 chainId;
        string name;
        bool isActive;
        bytes trustedRemote;
    }
    
    // Supported chains mapping
    mapping(uint16 => ChainConfig) public chainConfigs;
    mapping(uint256 => uint16) public chainIdToEid;
    uint16[] public supportedEids;
    
    // Message tracking
    struct CrossChainMessage {
        uint256 messageId;
        uint16 sourceEid;
        uint16 targetEid;
        bytes32 messageHash;
        bytes payload;
        uint256 timestamp;
        bool processed;
        string messageType;
    }
    
    mapping(uint256 => CrossChainMessage) public messages;
    mapping(bytes32 => bool) public processedHashes;
    uint256 private nextMessageId = 1;
    
    // Events
    event MessageSent(
        uint256 indexed messageId,
        uint16 indexed sourceEid,
        uint16 indexed targetEid,
        string messageType,
        bytes32 messageHash
    );
    
    event MessageReceived(
        uint256 indexed messageId,
        uint16 indexed sourceEid,
        bytes32 messageHash,
        string messageType
    );
    
    event CIDSynced(
        string indexed tokenId,
        string metadataCID,
        address indexed manufacturer,
        uint16 indexed sourceEid,
        uint256 timestamp
    );
    
    event TrustedRemoteSet(uint16 indexed eid, bytes trustedRemote);
    
    constructor(address _lzEndpoint, address initialAdmin) {
        lzEndpoint = ILayerZeroEndpoint(_lzEndpoint);
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(SENDER_ROLE, initialAdmin);
        _grantRole(OPERATOR_ROLE, initialAdmin);
        
        // Initialize chain configurations
        _initializeChainConfigs();
    }
    
    function _initializeChainConfigs() internal {
        // Base Sepolia - Manufacturer chain
        chainConfigs[40245] = ChainConfig({
            layerZeroEid: 40245,
            chainId: 84532,
            name: "Base Sepolia (Manufacturer)",
            isActive: true,
            trustedRemote: ""
        });
        chainIdToEid[84532] = 40245;
        supportedEids.push(40245);
        
        // OP Sepolia - Buyer chain
        chainConfigs[40232] = ChainConfig({
            layerZeroEid: 40232,
            chainId: 11155420,
            name: "OP Sepolia (Buyer)",
            isActive: true,
            trustedRemote: ""
        });
        chainIdToEid[11155420] = 40232;
        supportedEids.push(40232);
        
        // Arbitrum Sepolia - Additional chain
        chainConfigs[40231] = ChainConfig({
            layerZeroEid: 40231,
            chainId: 421614,
            name: "Arbitrum Sepolia (Additional)",
            isActive: true,
            trustedRemote: ""
        });
        chainIdToEid[421614] = 40231;
        supportedEids.push(40231);
        
        // Polygon Amoy - Hub chain
        chainConfigs[40267] = ChainConfig({
            layerZeroEid: 40267,
            chainId: 80002,
            name: "Polygon Amoy (Hub)",
            isActive: true,
            trustedRemote: ""
        });
        chainIdToEid[80002] = 40267;
        supportedEids.push(40267);
    }
    
    /**
     * @dev Send cross-chain message to specific target chain
     */
    function sendCrossChainMessage(
        uint16 targetEid,
        string memory messageType,
        bytes memory payload
    ) external payable onlyRole(SENDER_ROLE) nonReentrant {
        require(chainConfigs[targetEid].isActive, "Target chain not supported");
        require(chainConfigs[targetEid].trustedRemote.length > 0, "Trusted remote not set");
        
        uint256 messageId = nextMessageId++;
        bytes32 messageHash = keccak256(payload);
        
        // Store message
        messages[messageId] = CrossChainMessage({
            messageId: messageId,
            sourceEid: _getCurrentEid(),
            targetEid: targetEid,
            messageHash: messageHash,
            payload: payload,
            timestamp: block.timestamp,
            processed: false,
            messageType: messageType
        });
        
        // Prepare LayerZero message payload
        bytes memory lzPayload = abi.encode(messageId, messageType, messageHash, payload);
        
        // Send via LayerZero
        lzEndpoint.send{value: msg.value}(
            targetEid,
            chainConfigs[targetEid].trustedRemote,
            lzPayload,
            payable(msg.sender),
            address(0x0),
            bytes("")
        );
        
        emit MessageSent(messageId, _getCurrentEid(), targetEid, messageType, messageHash);
    }
    
    /**
     * @dev Send CID sync message to all other chains
     */
    function syncCIDToAllChains(
        string memory tokenId,
        string memory metadataCID,
        address manufacturer
    ) external payable onlyRole(SENDER_ROLE) nonReentrant {
        // Prepare CID sync payload
        bytes memory payload = abi.encode(
            "CID_SYNC",
            tokenId,
            metadataCID,
            manufacturer,
            block.chainid,
            block.timestamp
        );
        
        uint16 currentEid = _getCurrentEid();
        uint256 totalValue = msg.value;
        uint256 chainsToSend = 0;
        
        // Count chains to send to (excluding current chain and chains without trusted remotes)
        for (uint i = 0; i < supportedEids.length; i++) {
            if (supportedEids[i] != currentEid && chainConfigs[supportedEids[i]].trustedRemote.length > 0) {
                chainsToSend++;
            }
        }
        
        require(chainsToSend > 0, "No target chains available");
        uint256 valuePerMessage = totalValue / chainsToSend;
        
        // Send to all other chains
        for (uint i = 0; i < supportedEids.length; i++) {
            uint16 targetEid = supportedEids[i];
            
            // Skip current chain
            if (targetEid == currentEid) continue;
            
            // Skip if trusted remote not set
            if (chainConfigs[targetEid].trustedRemote.length == 0) continue;
            
            uint256 messageId = nextMessageId++;
            bytes32 messageHash = keccak256(payload);
            
            // Store message
            messages[messageId] = CrossChainMessage({
                messageId: messageId,
                sourceEid: currentEid,
                targetEid: targetEid,
                messageHash: messageHash,
                payload: payload,
                timestamp: block.timestamp,
                processed: false,
                messageType: "CID_SYNC"
            });
            
            // Prepare LayerZero payload
            bytes memory lzPayload = abi.encode(messageId, "CID_SYNC", messageHash, payload);
            
            // Send via LayerZero
            lzEndpoint.send{value: valuePerMessage}(
                targetEid,
                chainConfigs[targetEid].trustedRemote,
                lzPayload,
                payable(msg.sender),
                address(0x0),
                bytes("")
            );
            
            emit MessageSent(messageId, currentEid, targetEid, "CID_SYNC", messageHash);
        }
        
        emit CIDSynced(tokenId, metadataCID, manufacturer, currentEid, block.timestamp);
    }
    
    /**
     * @dev LayerZero receive function - called when message arrives from another chain
     * This function should be called by the LayerZero endpoint
     */
    function lzReceive(
        uint16 srcEid,
        bytes memory srcAddress,
        uint64 nonce,
        bytes memory payload
    ) external {
        require(msg.sender == address(lzEndpoint), "Only LayerZero endpoint");
        require(chainConfigs[srcEid].isActive, "Source chain not supported");
        
        // Verify trusted remote
        require(
            keccak256(srcAddress) == keccak256(chainConfigs[srcEid].trustedRemote),
            "Untrusted source"
        );
        
        // Decode LayerZero payload
        (uint256 messageId, string memory messageType, bytes32 messageHash, bytes memory messagePayload) = 
            abi.decode(payload, (uint256, string, bytes32, bytes));
        
        // Verify message hash
        require(keccak256(messagePayload) == messageHash, "Message hash mismatch");
        require(!processedHashes[messageHash], "Message already processed");
        
        // Mark as processed
        processedHashes[messageHash] = true;
        
        // Process based on message type
        if (keccak256(abi.encodePacked(messageType)) == keccak256(abi.encodePacked("CID_SYNC"))) {
            _processCIDSync(srcEid, messagePayload);
        }
        
        emit MessageReceived(messageId, srcEid, messageHash, messageType);
    }
    
    /**
     * @dev Process CID sync message
     */
    function _processCIDSync(uint16 srcEid, bytes memory payload) internal {
        (
            string memory messageType,
            string memory tokenId,
            string memory metadataCID,
            address manufacturer,
            uint256 sourceChainId,
            uint256 timestamp
        ) = abi.decode(payload, (string, string, string, address, uint256, uint256));
        
        emit CIDSynced(tokenId, metadataCID, manufacturer, srcEid, timestamp);
    }
    
    /**
     * @dev Get current chain's LayerZero endpoint ID
     */
    function _getCurrentEid() internal view returns (uint16) {
        return chainIdToEid[block.chainid];
    }
    
    /**
     * @dev Set trusted remote for a chain
     */
    function setTrustedRemote(uint16 eid, bytes memory trustedRemote) 
        external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(chainConfigs[eid].isActive, "Chain not supported");
        chainConfigs[eid].trustedRemote = trustedRemote;
        emit TrustedRemoteSet(eid, trustedRemote);
    }
    
    /**
     * @dev Estimate LayerZero fees
     */
    function estimateFees(
        uint16 targetEid,
        bytes memory payload,
        bool useZro,
        bytes memory adapterParams
    ) external view returns (uint256 nativeFee, uint256 zroFee) {
        return lzEndpoint.estimateFees(
            targetEid,
            address(this),
            payload,
            useZro,
            adapterParams
        );
    }
    
    /**
     * @dev Get all supported endpoint IDs
     */
    function getSupportedEids() external view returns (uint16[] memory) {
        return supportedEids;
    }
    
    /**
     * @dev Get chain configuration
     */
    function getChainConfig(uint16 eid) external view returns (ChainConfig memory) {
        return chainConfigs[eid];
    }
    
    /**
     * @dev Get message by ID
     */
    function getMessage(uint256 messageId) external view returns (CrossChainMessage memory) {
        return messages[messageId];
    }
}