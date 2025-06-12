// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title SimpleChainFlipOFT
 * @dev Simplified LayerZero-compatible OFT implementation
 * Built without external LayerZero packages to avoid dependency issues
 */
contract SimpleChainFlipOFT is ERC20, Ownable {
    
    // LayerZero endpoint for this chain
    address public immutable lzEndpoint;
    
    // Mapping from chain ID to peer address
    mapping(uint32 => bytes32) public peers;
    
    // Events
    event PeerSet(uint32 eid, bytes32 peer);
    event OFTSent(bytes32 indexed guid, uint32 dstEid, address indexed fromAddress, uint256 amount);
    event OFTReceived(bytes32 indexed guid, uint32 srcEid, address indexed toAddress, uint256 amount);
    
    constructor(
        string memory _name,
        string memory _symbol,
        address _lzEndpoint,
        address _delegate
    ) ERC20(_name, _symbol) Ownable(_delegate) {
        lzEndpoint = _lzEndpoint;
        _mint(_delegate, 1000000 * 10**decimals()); // Mint initial supply for testing
    }
    
    /**
     * @dev Set peer address for a destination chain
     */
    function setPeer(uint32 _eid, bytes32 _peer) external onlyOwner {
        peers[_eid] = _peer;
        emit PeerSet(_eid, _peer);
    }
    
    /**
     * @dev Get peer address for a destination chain
     */
    function getPeer(uint32 _eid) external view returns (bytes32) {
        return peers[_eid];
    }
    
    /**
     * @dev Simple send function for LayerZero compatibility
     * This is a simplified implementation for testing purposes
     */
    function send(
        uint32 _dstEid,
        bytes32 _to,
        uint256 _amountLD,
        uint256 _minAmountLD,
        bytes calldata _extraOptions
    ) external payable {
        require(_amountLD >= _minAmountLD, "Amount below minimum");
        require(balanceOf(msg.sender) >= _amountLD, "Insufficient balance");
        require(peers[_dstEid] != bytes32(0), "Peer not set");
        
        // Burn tokens from sender
        _burn(msg.sender, _amountLD);
        
        // Generate a simple GUID for tracking
        bytes32 guid = keccak256(abi.encodePacked(block.timestamp, msg.sender, _dstEid, _amountLD));
        
        emit OFTSent(guid, _dstEid, msg.sender, _amountLD);
        
        // In a real implementation, this would call LayerZero endpoint
        // For testing, we just emit the event
    }
    
    /**
     * @dev Estimate send fee (simplified)
     */
    function quoteSend(
        uint32 _dstEid,
        bytes32 _to,
        uint256 _amountLD,
        bool _payInLzToken
    ) external view returns (uint256 nativeFee, uint256 lzTokenFee) {
        // Return fixed fees for testing
        nativeFee = 0.001 ether; // 0.001 ETH
        lzTokenFee = 0;
    }
    
    /**
     * @dev Mint tokens for testing
     */
    function mint(address _to, uint256 _amount) external onlyOwner {
        _mint(_to, _amount);
    }
    
    /**
     * @dev Get endpoint address
     */
    function endpoint() external view returns (address) {
        return lzEndpoint;
    }
}