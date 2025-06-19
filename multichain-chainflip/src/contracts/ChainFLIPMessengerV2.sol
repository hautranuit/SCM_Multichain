// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@layerzerolabs/oapp-evm/contracts/oapp/OApp.sol";
import "@layerzerolabs/lz-evm-protocol-v2/contracts/interfaces/ILayerZeroEndpointV2.sol";

/**
 * @title ChainFLIPMessengerV2 - Updated LayerZero V2 Compatible Messenger
 * @dev Fixed LayerZero V2 implementation with proper extraOptions format
 * Based on the working OFT system patterns for reliable cross-chain messaging
 */
contract ChainFLIPMessengerV2 is OApp {
    
    // Received CID data
    struct CIDData {
        string tokenId;
        string metadataCID;
        address manufacturer;
        uint256 timestamp;
        uint32 sourceEid;
    }
    
    // Storage for received CID data
    mapping(string => CIDData) public receivedCIDs;
    string[] public cidList;
    
    // Chain configurations with LayerZero V2 endpoint IDs
    mapping(uint32 => bool) public supportedChains;
    
    // Events
    event CIDSynced(string indexed tokenId, string metadataCID, address indexed manufacturer, uint32 indexed destEid, uint256 timestamp);
    event CIDReceived(string indexed tokenId, string metadataCID, address indexed manufacturer, uint32 indexed sourceEid, uint256 timestamp);
    
    constructor(address _endpoint, address _owner) OApp(_endpoint, _owner) {
        // Set supported destination chains based on current chain
        _setupSupportedChains();
    }
    
    function _setupSupportedChains() internal {
        // LayerZero V2 Endpoint IDs for testnets
        uint32 BASE_SEPOLIA_EID = 40245;
        uint32 POLYGON_AMOY_EID = 40267;
        uint32 OPTIMISM_SEPOLIA_EID = 40232;
        uint32 ARBITRUM_SEPOLIA_EID = 40231;
        
        // Determine current chain and set supported chains
        uint256 chainId = block.chainid;
        
        if (chainId == 84532) { // Base Sepolia
            supportedChains[POLYGON_AMOY_EID] = true;
            supportedChains[OPTIMISM_SEPOLIA_EID] = true;
            supportedChains[ARBITRUM_SEPOLIA_EID] = true;
        } else if (chainId == 80002) { // Polygon Amoy
            supportedChains[BASE_SEPOLIA_EID] = true;
            supportedChains[OPTIMISM_SEPOLIA_EID] = true;
            supportedChains[ARBITRUM_SEPOLIA_EID] = true;
        } else if (chainId == 11155420) { // Optimism Sepolia
            supportedChains[BASE_SEPOLIA_EID] = true;
            supportedChains[POLYGON_AMOY_EID] = true;
            supportedChains[ARBITRUM_SEPOLIA_EID] = true;
        } else if (chainId == 421614) { // Arbitrum Sepolia
            supportedChains[BASE_SEPOLIA_EID] = true;
            supportedChains[POLYGON_AMOY_EID] = true;
            supportedChains[OPTIMISM_SEPOLIA_EID] = true;
        }
    }
    
    // LayerZero V2 receive function
    function _lzReceive(
        Origin calldata _origin,
        bytes32, // guid
        bytes calldata _message,
        address, // executor
        bytes calldata // extraData
    ) internal override {
        (string memory tokenId, string memory metadataCID, address manufacturer, uint256 timestamp) = 
            abi.decode(_message, (string, string, address, uint256));
        
        // Store received CID data
        receivedCIDs[tokenId] = CIDData({
            tokenId: tokenId,
            metadataCID: metadataCID,
            manufacturer: manufacturer,
            timestamp: timestamp,
            sourceEid: _origin.srcEid
        });
        
        // Add to list if not exists
        bool exists = false;
        for (uint i = 0; i < cidList.length; i++) {
            if (keccak256(bytes(cidList[i])) == keccak256(bytes(tokenId))) {
                exists = true;
                break;
            }
        }
        if (!exists) {
            cidList.push(tokenId);
        }
        
        emit CIDReceived(tokenId, metadataCID, manufacturer, _origin.srcEid, timestamp);
    }
    
    // Send CID to specific chain - FIXED WITH PROPER LAYERZERO V2 PATTERNS
    function sendCIDToChain(
        uint32 _destEid,
        string memory _tokenId,
        string memory _metadataCID,
        address _manufacturer
    ) public payable {
        require(supportedChains[_destEid], "Unsupported destination chain");
        
        bytes memory _message = abi.encode(_tokenId, _metadataCID, _manufacturer, block.timestamp);
        
        // ✅ FIXED: Use proper LayerZero V2 extraOptions format from working OFT system
        // This is the WORKING format: 0x0003010011010000000000000000000000000000ea60
        bytes memory _options = hex"0003010011010000000000000000000000000000ea60";
        
        // Get fee quote using the correct OApp V2 method signature
        MessagingFee memory fee = _quote(_destEid, _message, _options, false);
        require(msg.value >= fee.nativeFee, "Insufficient fee provided");
        
        // Send using the correct OApp V2 method signature
        _lzSend(_destEid, _message, _options, MessagingFee(msg.value, 0), payable(msg.sender));
        
        emit CIDSynced(_tokenId, _metadataCID, _manufacturer, _destEid, block.timestamp);
    }
    
    // Send CID to all supported chains (main function for ChainFLIP)
    function syncCIDToAllChains(
        string memory _tokenId,
        string memory _metadataCID,
        address _manufacturer
    ) public payable {
        uint256 totalValue = msg.value;
        uint256 chainCount = 0;
        
        // Count supported chains
        for (uint32 eid = 40230; eid <= 40270; eid++) {
            if (supportedChains[eid]) {
                chainCount++;
            }
        }
        
        require(chainCount > 0, "No supported chains configured");
        require(totalValue > 0, "Must send ETH for LayerZero fees");
        
        uint256 valuePerChain = totalValue / chainCount;
        bytes memory _message = abi.encode(_tokenId, _metadataCID, _manufacturer, block.timestamp);
        
        // ✅ FIXED: Use proper LayerZero V2 extraOptions format from working OFT system
        bytes memory _options = hex"0003010011010000000000000000000000000000ea60";
        
        // Send to all supported chains
        for (uint32 eid = 40230; eid <= 40270; eid++) {
            if (supportedChains[eid]) {
                _lzSend(eid, _message, _options, MessagingFee(valuePerChain, 0), payable(msg.sender));
                emit CIDSynced(_tokenId, _metadataCID, _manufacturer, eid, block.timestamp);
            }
        }
    }
    
    // Get quote for sending message - UPDATED FOR V2
    function quote(
        uint32 _destEid,
        string memory _tokenId,
        string memory _metadataCID,
        address _manufacturer,
        bytes memory _options,
        bool _payInLzToken
    ) public view returns (MessagingFee memory fee) {
        bytes memory _message = abi.encode(_tokenId, _metadataCID, _manufacturer, block.timestamp);
        return _quote(_destEid, _message, _options, _payInLzToken);
    }
    
    // Get received CID data
    function getCIDData(string memory _tokenId) public view returns (CIDData memory) {
        return receivedCIDs[_tokenId];
    }
    
    // Get all received CIDs
    function getAllCIDs() public view returns (string[] memory) {
        return cidList;
    }
    
    // Get number of received CIDs
    function getCIDCount() public view returns (uint256) {
        return cidList.length;
    }
    
    // Check if CID exists
    function hasCID(string memory _tokenId) public view returns (bool) {
        return bytes(receivedCIDs[_tokenId].tokenId).length > 0;
    }
    
    // Get supported chains
    function getSupportedChains() public view returns (uint32[] memory) {
        uint32[] memory chains = new uint32[](4);
        uint256 index = 0;
        
        for (uint32 eid = 40230; eid <= 40270; eid++) {
            if (supportedChains[eid]) {
                chains[index] = eid;
                index++;
            }
        }
        
        return chains;
    }
}