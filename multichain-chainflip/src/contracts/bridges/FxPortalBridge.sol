// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

// FxPortal interfaces for Polygon ecosystem cross-chain communication
interface IFxStateSender {
    function sendMessageToChild(address _receiver, bytes calldata _data) external;
}

interface IFxMessageProcessor {
    function processMessageFromRoot(
        uint256 stateId,
        address sender,
        bytes calldata message
    ) external;
}

/**
 * @title FxPortalBridge
 * @dev FxPortal bridge implementation for Polygon ecosystem communication
 * Handles Hub (Polygon Amoy) ↔ Manufacturer (zkEVM Cardona) communication
 */
contract FxPortalBridge is Ownable, ReentrancyGuard {
    
    // FxPortal contracts
    IFxStateSender public fxStateSender;
    address public fxChildTunnel; // Child contract address on zkEVM Cardona
    
    // Message types for cross-chain communication
    enum MessageType {
        PRODUCT_REGISTRATION,
        QUALITY_APPROVAL,
        MANUFACTURING_UPDATE,
        FL_MODEL_SYNC,
        INCENTIVE_UPDATE
    }
    
    struct FxMessage {
        MessageType msgType;
        uint256 sourceChain;
        uint256 targetChain;
        bytes32 dataHash;
        bytes payload;
        uint256 timestamp;
        uint256 stateId;
    }
    
    // State variables
    mapping(uint256 => bool) public processedStateIds;
    mapping(bytes32 => FxMessage) public messages;
    
    // Events
    event MessageSentToChild(
        address indexed receiver,
        bytes32 indexed messageHash,
        bytes data
    );
    
    event MessageReceivedFromChild(
        uint256 indexed stateId,
        address indexed sender,
        bytes32 indexed messageHash,
        bytes data
    );
    
    event FxChildTunnelSet(address indexed childTunnel);
    
    constructor(
        address _fxStateSender,
        address initialOwner
    ) Ownable(initialOwner) {
        fxStateSender = IFxStateSender(_fxStateSender);
    }
    
    // Set child tunnel contract address on zkEVM Cardona
    function setFxChildTunnel(address _fxChildTunnel) external onlyOwner {
        fxChildTunnel = _fxChildTunnel;
        emit FxChildTunnelSet(_fxChildTunnel);
    }
    
    // Send message to child chain (zkEVM Cardona)
    function sendMessageToChild(
        MessageType msgType,
        bytes32 dataHash,
        bytes calldata payload
    ) external nonReentrant {
        require(fxChildTunnel != address(0), "Child tunnel not set");
        
        FxMessage memory message = FxMessage({
            msgType: msgType,
            sourceChain: block.chainid, // Polygon Amoy
            targetChain: 2442, // zkEVM Cardona
            dataHash: dataHash,
            payload: payload,
            timestamp: block.timestamp,
            stateId: 0 // Will be assigned by FxPortal
        });
        
        bytes32 messageHash = keccak256(abi.encode(message));
        messages[messageHash] = message;
        
        bytes memory encodedMessage = abi.encode(message);
        
        // Send via FxPortal
        fxStateSender.sendMessageToChild(fxChildTunnel, encodedMessage);
        
        emit MessageSentToChild(fxChildTunnel, messageHash, encodedMessage);
    }
    
    // Process message from child chain (called by FxPortal)
    function processMessageFromRoot(
        uint256 stateId,
        address sender,
        bytes calldata message
    ) external {
        require(!processedStateIds[stateId], "State already processed");
        require(sender == fxChildTunnel, "Invalid sender");
        
        processedStateIds[stateId] = true;
        
        FxMessage memory fxMessage = abi.decode(message, (FxMessage));
        fxMessage.stateId = stateId;
        
        bytes32 messageHash = keccak256(abi.encode(fxMessage));
        messages[messageHash] = fxMessage;
        
        // Process the message based on type
        _processMessage(fxMessage);
        
        emit MessageReceivedFromChild(stateId, sender, messageHash, message);
    }
    
    // Process received message
    function _processMessage(FxMessage memory message) internal virtual {
        // Override in implementing contracts to handle specific message types
        // Base implementation just stores the message for verification
        
        if (message.msgType == MessageType.PRODUCT_REGISTRATION) {
            _handleProductRegistration(message);
        } else if (message.msgType == MessageType.QUALITY_APPROVAL) {
            _handleQualityApproval(message);
        } else if (message.msgType == MessageType.MANUFACTURING_UPDATE) {
            _handleManufacturingUpdate(message);
        } else if (message.msgType == MessageType.FL_MODEL_SYNC) {
            _handleFLModelSync(message);
        } else if (message.msgType == MessageType.INCENTIVE_UPDATE) {
            _handleIncentiveUpdate(message);
        }
    }
    
    // Handle product registration from manufacturer chain
    function _handleProductRegistration(FxMessage memory message) internal virtual {
        // Decode product data and register on hub
        // Implementation will be in the Hub contract that inherits this
    }
    
    // Handle quality approval updates
    function _handleQualityApproval(FxMessage memory message) internal virtual {
        // Process quality approval from manufacturer chain
    }
    
    // Handle manufacturing updates
    function _handleManufacturingUpdate(FxMessage memory message) internal virtual {
        // Process manufacturing metrics and incentives
    }
    
    // Handle FL model synchronization
    function _handleFLModelSync(FxMessage memory message) internal virtual {
        // Sync federated learning models between chains
    }
    
    // Handle incentive updates
    function _handleIncentiveUpdate(FxMessage memory message) internal virtual {
        // Process incentive payments and reputation updates
    }
    
    // View functions
    function getMessage(bytes32 messageHash) external view returns (FxMessage memory) {
        return messages[messageHash];
    }
    
    function isStateProcessed(uint256 stateId) external view returns (bool) {
        return processedStateIds[stateId];
    }
    
    // Emergency functions
    function setFxStateSender(address _fxStateSender) external onlyOwner {
        fxStateSender = IFxStateSender(_fxStateSender);
    }
}
