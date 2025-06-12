// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ChainFlipOFT - LayerZero-Compatible OFT with ETH Deposit/Withdraw
 * @dev Simplified LayerZero-compatible OFT implementation with proper ETH bridging
 * Built without external LayerZero packages to avoid dependency issues
 * Users can deposit ETH to get cfWETH tokens and withdraw cfWETH to get ETH
 */
contract ChainFlipOFT is ERC20, Ownable {
    
    // LayerZero endpoint for this chain
    address public immutable endpoint;
    
    // Mapping from destination endpoint ID to peer address
    mapping(uint32 => bytes32) public peers;
    
    // Reentrancy protection
    bool private _locked;
    
    modifier nonReentrant() {
        require(!_locked, "ReentrancyGuard: reentrant call");
        _locked = true;
        _;
        _locked = false;
    }
    
    // LayerZero structs
    struct SendParam {
        uint32 dstEid;
        bytes32 to;
        uint256 amountLD;
        uint256 minAmountLD;
        bytes extraOptions;
        bytes composeMsg;
        bytes oftCmd;
    }
    
    struct MessagingFee {
        uint256 nativeFee;
        uint256 lzTokenFee;
    }
    
    struct MessagingReceipt {
        bytes32 guid;
        uint64 nonce;
        MessagingFee fee;
    }
    
    // Events for LayerZero compatibility
    event SetPeer(uint32 eid, bytes32 peer);
    event OFTSent(bytes32 indexed guid, uint32 dstEid, address indexed toAddress, uint256 amount);
    
    // Events for deposit/withdraw
    event Deposit(address indexed user, uint256 ethAmount, uint256 tokensReceived);
    event Withdraw(address indexed user, uint256 tokenAmount, uint256 ethReceived);
    
    constructor(
        string memory _name,
        string memory _symbol,
        address _lzEndpoint,
        address _delegate
    ) ERC20(_name, _symbol) Ownable(_delegate) {
        endpoint = _lzEndpoint;
        // Owner is already set in Ownable constructor
    }
    
    /**
     * @dev Deposit ETH to receive cfWETH tokens (1:1 ratio)
     */
    function deposit() external payable nonReentrant {
        require(msg.value > 0, "Must send ETH");
        
        // Mint cfWETH tokens equal to ETH sent
        _mint(msg.sender, msg.value);
        
        emit Deposit(msg.sender, msg.value, msg.value);
    }
    
    /**
     * @dev Withdraw cfWETH tokens to receive ETH (1:1 ratio)
     * @param amount Amount of cfWETH tokens to withdraw
     */
    function withdraw(uint256 amount) external nonReentrant {
        require(amount > 0, "Amount must be greater than 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient cfWETH balance");
        require(address(this).balance >= amount, "Insufficient contract ETH balance");
        
        // Burn cfWETH tokens
        _burn(msg.sender, amount);
        
        // Send ETH to user
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "ETH transfer failed");
        
        emit Withdraw(msg.sender, amount, amount);
    }
    
    /**
     * @dev Emergency function to add ETH liquidity to contract (only owner)
     */
    function addLiquidity() external payable onlyOwner {
        // Owner can add ETH to ensure withdrawals work
    }
    
    /**
     * @dev Get contract ETH balance
     */
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
    
    /**
     * @dev Set peer for LayerZero communication
     * @param _eid Destination endpoint ID
     * @param _peer Peer address in bytes32 format
     */
    function setPeer(uint32 _eid, bytes32 _peer) external onlyOwner {
        peers[_eid] = _peer;
        emit SetPeer(_eid, _peer);
    }
    
    /**
     * @dev Simple send function for LayerZero compatibility
     * This is a simplified implementation - in production, use official LayerZero OFT
     */
    function send(
        SendParam memory _sendParam,
        MessagingFee memory _fee,
        address _refundAddress
    ) external payable returns (MessagingReceipt memory receipt) {
        require(peers[_sendParam.dstEid] != bytes32(0), "Peer not set");
        require(msg.value >= _fee.nativeFee, "Insufficient fee");
        require(balanceOf(msg.sender) >= _sendParam.amountLD, "Insufficient balance");
        
        // Burn tokens on source chain
        _burn(msg.sender, _sendParam.amountLD);
        
        // Generate mock GUID for tracking
        bytes32 guid = keccak256(abi.encodePacked(block.timestamp, msg.sender, _sendParam.dstEid, _sendParam.amountLD));
        
        // In a real implementation, this would call LayerZero endpoint
        // For now, emit event for tracking
        address toAddress = address(uint160(uint256(_sendParam.to)));
        emit OFTSent(guid, _sendParam.dstEid, toAddress, _sendParam.amountLD);
        
        // Return receipt
        return MessagingReceipt({
            guid: guid,
            nonce: uint64(block.number),
            fee: _fee
        });
    }
    
    /**
     * @dev Quote send fee for LayerZero transfer
     */
    function quoteSend(
        SendParam memory _sendParam,
        bool _payInLzToken
    ) external view returns (MessagingFee memory fee) {
        // Fixed fee structure for testing
        uint256 nativeFee = 0.001 ether; // 0.001 ETH LayerZero messaging fee
        uint256 lzTokenFee = 0;
        
        return MessagingFee({
            nativeFee: nativeFee,
            lzTokenFee: lzTokenFee
        });
    }
    
    /**
     * @dev Admin mint function (for initial setup only)
     */
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
    
    /**
     * @dev Receive function to accept ETH deposits
     */
    receive() external payable {
        // Automatically convert ETH to cfWETH tokens
        if (msg.value > 0) {
            require(!_locked, "ReentrancyGuard: reentrant call");
            _mint(msg.sender, msg.value);
            emit Deposit(msg.sender, msg.value, msg.value);
        }
    }
}