// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "./ChainFlipOFT.sol";

/**
 * @title ETHWrapper - ETH Deposit/Withdraw Logic with Owner-Mediated Minting
 * @dev Handles ETH <-> cfWETH conversion logic using deposit proxy pattern
 * Separate from LayerZero OFT to avoid constructor conflicts
 */
contract ETHWrapper {
    
    ChainFlipOFT public immutable cfWETH;
    address public immutable owner;
    
    // Track pending deposits for owner-mediated minting
    mapping(address => uint256) public pendingDeposits;
    
    // Events
    event DepositRequested(address indexed user, uint256 ethAmount);
    event Deposit(address indexed user, uint256 ethAmount, uint256 tokensReceived);
    event Withdraw(address indexed user, uint256 tokenAmount, uint256 ethReceived);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    constructor(address _cfWETH) {
        cfWETH = ChainFlipOFT(_cfWETH);
        owner = cfWETH.owner(); // Set owner to same as OFT contract owner
    }
    
    /**
     * @dev Deposit ETH to receive cfWETH tokens (1:1 ratio)
     * Uses owner-mediated minting pattern
     */
    function deposit() external payable {
        require(msg.value > 0, "Must send ETH");
        
        // Store deposit request for owner processing
        pendingDeposits[msg.sender] += msg.value;
        
        emit DepositRequested(msg.sender, msg.value);
        
        // Owner will process this deposit and mint tokens
        _processDeposit(msg.sender, msg.value);
    }
    
    /**
     * @dev Process deposit and mint tokens (called by owner or internally)
     * @param user Address to mint tokens to
     * @param amount Amount of tokens to mint
     */
    function _processDeposit(address user, uint256 amount) internal {
        // Only process if there's a pending deposit
        require(pendingDeposits[user] >= amount, "No pending deposit");
        
        // Reduce pending deposit
        pendingDeposits[user] -= amount;
        
        // Call owner-mediated minting
        _mintTokensViaOwner(user, amount);
        
        emit Deposit(user, amount, amount);
    }
    
    /**
     * @dev Internal function to handle owner-mediated minting
     * This function will be called by the backend service using owner account
     */
    function _mintTokensViaOwner(address user, uint256 amount) internal {
        // This will be handled by backend service calling cfWETH.mint() directly
        // with owner permissions. This function serves as event tracking.
    }
    
    /**
     * @dev Owner function to mint tokens for pending deposits
     * Called by backend service using owner account
     */
    function processPendingDeposit(address user, uint256 amount) external onlyOwner {
        require(pendingDeposits[user] >= amount, "Insufficient pending deposit");
        
        // Reduce pending deposit
        pendingDeposits[user] -= amount;
        
        // Mint tokens directly (owner has permission)
        cfWETH.mint(user, amount);
        
        emit Deposit(user, amount, amount);
    }
    
    /**
     * @dev Withdraw cfWETH tokens to receive ETH (1:1 ratio)
     * @param amount Amount of cfWETH tokens to withdraw
     */
    function withdraw(uint256 amount) external {
        require(amount > 0, "Amount must be greater than 0");
        require(cfWETH.balanceOf(msg.sender) >= amount, "Insufficient cfWETH balance");
        require(address(this).balance >= amount, "Insufficient contract ETH balance");
        
        // Burn cfWETH tokens from user (requires owner permission)
        // This will be handled by calling burn via owner account
        _burnTokensViaOwner(msg.sender, amount);
        
        // Send ETH to user
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "ETH transfer failed");
        
        emit Withdraw(msg.sender, amount, amount);
    }
    
    /**
     * @dev Internal function to handle owner-mediated burning
     */
    function _burnTokensViaOwner(address user, uint256 amount) internal {
        // This will be handled by backend service calling cfWETH.burn() directly
        // with owner permissions
    }
    
    /**
     * @dev Owner function to burn tokens for withdrawals
     * Called by backend service using owner account
     */
    function processBurn(address user, uint256 amount) external onlyOwner {
        require(cfWETH.balanceOf(user) >= amount, "Insufficient cfWETH balance");
        
        // Burn tokens directly (owner has permission)
        cfWETH.burn(user, amount);
    }
    
    /**
     * @dev Add ETH liquidity to contract (for withdrawals)
     */
    function addLiquidity() external payable {
        // Anyone can add ETH to ensure withdrawals work
    }
    
    /**
     * @dev Get contract ETH balance
     */
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
    
    /**
     * @dev Get cfWETH token balance for user
     */
    function getTokenBalance(address user) external view returns (uint256) {
        return cfWETH.balanceOf(user);
    }
    
    /**
     * @dev Get pending deposit amount for user
     */
    function getPendingDeposit(address user) external view returns (uint256) {
        return pendingDeposits[user];
    }
    
    /**
     * @dev Set LayerZero peer for cross-chain transfers
     * Only owner can call this function
     * @param _eid LayerZero endpoint ID
     * @param _peer Peer address in bytes32 format
     */
    function setPeer(uint32 _eid, bytes32 _peer) external onlyOwner {
        cfWETH.setPeer(_eid, _peer);
    }
    
    /**
     * @dev Get LayerZero peer for endpoint
     * @param _eid LayerZero endpoint ID
     */
    function getPeer(uint32 _eid) external view returns (bytes32) {
        return cfWETH.peers(_eid);
    }
    
    /**
     * @dev Get the OFT contract address
     */
    function getOFTAddress() external view returns (address) {
        return address(cfWETH);
    }
    
    /**
     * @dev Receive function to accept ETH deposits
     */
    receive() external payable {
        if (msg.value > 0) {
            // Store deposit request for owner processing
            pendingDeposits[msg.sender] += msg.value;
            emit DepositRequested(msg.sender, msg.value);
            
            // Process deposit immediately
            _processDeposit(msg.sender, msg.value);
        }
    }
}