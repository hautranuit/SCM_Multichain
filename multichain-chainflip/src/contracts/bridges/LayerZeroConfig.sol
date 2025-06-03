// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

// Simplified LayerZero interfaces
interface ILayerZeroEndpoint {
    function send(
        uint16 _dstChainId,
        bytes calldata _destination,
        bytes calldata _payload,
        address payable _refundAddress,
        address _zroPaymentAddress,
        bytes calldata _adapterParams
    ) external payable;

    function receivePayload(
        uint16 _srcChainId,
        bytes calldata _srcAddress,
        address _dstAddress,
        uint64 _nonce,
        uint _gasLimit,
        bytes calldata _payload
    ) external;

    function getInboundNonce(uint16 _srcChainId, bytes calldata _srcAddress) external view returns (uint64);
    function getOutboundNonce(uint16 _dstChainId, address _srcAddress) external view returns (uint64);
    function estimateFees(uint16 _dstChainId, address _userApplication, bytes calldata _payload, bool _payInZRO, bytes calldata _adapterParam) external view returns (uint nativeFee, uint zroFee);
    function getChainId() external view returns (uint16);
    function retryPayload(uint16 _srcChainId, bytes calldata _srcAddress, bytes calldata _payload) external;
    function hasStoredPayload(uint16 _srcChainId, bytes calldata _srcAddress) external view returns (bool);
    function getSendLibraryAddress(address _userApplication) external view returns (address);
    function getReceiveLibraryAddress(address _userApplication) external view returns (address);
    function isSendingPayload() external view returns (bool);
    function isReceivingPayload() external view returns (bool);
    function getConfig(uint16 _version, uint16 _chainId, address _userApplication, uint _configType) external view returns (bytes memory);
    function getSendVersion(address _userApplication) external view returns (uint16);
    function getReceiveVersion(address _userApplication) external view returns (uint16);
    function setConfig(uint16 _version, uint16 _chainId, uint _configType, bytes calldata _config) external;
    function setSendVersion(uint16 _version) external;
    function setReceiveVersion(uint16 _version) external;
    function forceResumeReceive(uint16 _srcChainId, bytes calldata _srcAddress) external;
}

interface ILayerZeroReceiver {
    function lzReceive(uint16 _srcChainId, bytes calldata _srcAddress, uint64 _nonce, bytes calldata _payload) external;
}

/**
 * @title LayerZeroConfig
 * @dev Simplified LayerZero configuration and cross-chain messaging for ChainFLIP
 * Handles cross-ecosystem communication between Hub and L2 chains
 */
contract LayerZeroConfig is ILayerZeroReceiver, Ownable, ReentrancyGuard {
    
    // LayerZero endpoint for this chain
    ILayerZeroEndpoint public immutable lzEndpoint;
    
    // Mapping from chain ID to LayerZero chain ID
    mapping(uint256 => uint16) public chainIdToLzChainId;
    mapping(uint16 => uint256) public lzChainIdToChainId;
    
    // Trusted remote contracts on other chains
    mapping(uint16 => bytes) public trustedRemoteLookup;
    
    // Message types for cross-chain communication
    enum MessageType {
        PRODUCT_SYNC,
        SHIPMENT_UPDATE,
        PURCHASE_UPDATE,
        FL_MODEL_UPDATE,
        REPUTATION_UPDATE
    }
    
    struct CrossChainMessage {
        MessageType msgType;
        uint256 sourceChain;
        uint256 targetChain;
        bytes32 dataHash;
        bytes payload;
        uint256 timestamp;
    }
    
    // Events
    event MessageSent(
        uint16 indexed dstChainId,
        bytes indexed dstAddress,
        uint256 nonce,
        bytes payload
    );
    
    event MessageReceived(
        uint16 indexed srcChainId,
        bytes indexed srcAddress,
        uint256 nonce,
        bytes payload
    );
    
    event TrustedRemoteSet(uint16 indexed chainId, bytes remoteAddress);
    
    constructor(address _lzEndpoint, address initialOwner) Ownable(initialOwner) {
        lzEndpoint = ILayerZeroEndpoint(_lzEndpoint);
        
        // Initialize LayerZero chain ID mappings
        _initializeChainMappings();
    }
    
    function _initializeChainMappings() internal {
        // Polygon Amoy (Hub) - ChainID: 80002, LZ ChainID: 10267
        chainIdToLzChainId[80002] = 10267;
        lzChainIdToChainId[10267] = 80002;
        
        // Arbitrum Sepolia (Transporter) - ChainID: 421614, LZ ChainID: 10231
        chainIdToLzChainId[421614] = 10231;
        lzChainIdToChainId[10231] = 421614;
        
        // Optimism Sepolia (Buyer) - ChainID: 11155420, LZ ChainID: 10232
        chainIdToLzChainId[11155420] = 10232;
        lzChainIdToChainId[10232] = 11155420;
    }
    
    // Set trusted remote contract address
    function setTrustedRemote(uint16 _srcChainId, bytes calldata _srcAddress) external onlyOwner {
        trustedRemoteLookup[_srcChainId] = _srcAddress;
        emit TrustedRemoteSet(_srcChainId, _srcAddress);
    }
    
    // Send cross-chain message
    function sendMessage(
        uint256 targetChainId,
        MessageType msgType,
        bytes32 dataHash,
        bytes calldata payload
    ) external payable nonReentrant {
        uint16 dstChainId = chainIdToLzChainId[targetChainId];
        require(dstChainId != 0, "Target chain not supported");
        require(trustedRemoteLookup[dstChainId].length > 0, "Trusted remote not set");
        
        CrossChainMessage memory message = CrossChainMessage({
            msgType: msgType,
            sourceChain: block.chainid,
            targetChain: targetChainId,
            dataHash: dataHash,
            payload: payload,
            timestamp: block.timestamp
        });
        
        bytes memory encodedMessage = abi.encode(message);
        
        // Send message via LayerZero
        lzEndpoint.send{value: msg.value}(
            dstChainId,
            trustedRemoteLookup[dstChainId],
            encodedMessage,
            payable(msg.sender),
            address(0),
            bytes("")
        );
        
        emit MessageSent(dstChainId, trustedRemoteLookup[dstChainId], 0, encodedMessage);
    }
    
    // Receive cross-chain message from LayerZero
    function lzReceive(
        uint16 _srcChainId,
        bytes calldata _srcAddress,
        uint64 _nonce,
        bytes calldata _payload
    ) external override {
        require(msg.sender == address(lzEndpoint), "Only LayerZero endpoint");
        require(
            keccak256(_srcAddress) == keccak256(trustedRemoteLookup[_srcChainId]),
            "Untrusted source"
        );
        
        CrossChainMessage memory message = abi.decode(_payload, (CrossChainMessage));
        
        // Process the message based on type
        _processMessage(message);
        
        emit MessageReceived(_srcChainId, _srcAddress, _nonce, _payload);
    }
    
    // Process received cross-chain message
    function _processMessage(CrossChainMessage memory message) internal virtual {
        // Override in implementing contracts to handle specific message types
        // Base implementation just stores the message hash for verification
        bytes32 messageHash = keccak256(abi.encode(message));
        
        // Emit event for processing by backend services
        emit MessageReceived(
            chainIdToLzChainId[message.sourceChain],
            trustedRemoteLookup[chainIdToLzChainId[message.sourceChain]],
            0,
            abi.encode(message)
        );
    }
    
    // Estimate cross-chain message fee
    function estimateFee(
        uint256 targetChainId,
        bytes calldata payload,
        bool useZro,
        bytes calldata adapterParams
    ) external view returns (uint256 nativeFee, uint256 zroFee) {
        uint16 dstChainId = chainIdToLzChainId[targetChainId];
        require(dstChainId != 0, "Target chain not supported");
        
        return lzEndpoint.estimateFees(
            dstChainId,
            address(this),
            payload,
            useZro,
            adapterParams
        );
    }
    
    // Get LayerZero chain ID for a given chain ID
    function getLzChainId(uint256 chainId) external view returns (uint16) {
        return chainIdToLzChainId[chainId];
    }
    
    // Check if chain is supported
    function isChainSupported(uint256 chainId) external view returns (bool) {
        return chainIdToLzChainId[chainId] != 0;
    }
    
    // Emergency functions
    function forceResumeReceive(uint16 _srcChainId, bytes calldata _srcAddress) external onlyOwner {
        lzEndpoint.forceResumeReceive(_srcChainId, _srcAddress);
    }
    
    function setConfig(
        uint16 _version,
        uint16 _chainId,
        uint256 _configType,
        bytes calldata _config
    ) external onlyOwner {
        lzEndpoint.setConfig(_version, _chainId, _configType, _config);
    }
    
    function setSendVersion(uint16 _version) external onlyOwner {
        lzEndpoint.setSendVersion(_version);
    }
    
    function setReceiveVersion(uint16 _version) external onlyOwner {
        lzEndpoint.setReceiveVersion(_version);
    }
}
