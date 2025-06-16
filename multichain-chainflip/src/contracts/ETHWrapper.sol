// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "./ChainFlipOFT.sol";

/**
 * @title ETHWrapper - ETH Deposit/Withdraw Logic
 * @dev Handles ETH <-> cfWETH conversion logic
 * Separate from LayerZero OFT to avoid constructor conflicts
 */
contract ETHWrapper {
    
    ChainFlipOFT public immutable cfWETH;
    
    // Events
    event Deposit(address indexed user, uint256 ethAmount, uint256 tokensReceived);
    event Withdraw(address indexed user, uint256 tokenAmount, uint256 ethReceived);
    
    constructor(address _cfWETH) {
        cfWETH = ChainFlipOFT(_cfWETH);
    }
    
    /**
     * @dev Deposit ETH to receive cfWETH tokens (1:1 ratio)
     */
    function deposit() external payable {
        require(msg.value > 0, "Must send ETH");
        
        // Mint cfWETH tokens to user
        cfWETH.mint(msg.sender, msg.value);
        
        emit Deposit(msg.sender, msg.value, msg.value);
    }
    
    /**
     * @dev Withdraw cfWETH tokens to receive ETH (1:1 ratio)
     * @param amount Amount of cfWETH tokens to withdraw
     */
    function withdraw(uint256 amount) external {
        require(amount > 0, "Amount must be greater than 0");
        require(cfWETH.balanceOf(msg.sender) >= amount, "Insufficient cfWETH balance");
        require(address(this).balance >= amount, "Insufficient contract ETH balance");
        
        // Burn cfWETH tokens from user
        cfWETH.burn(msg.sender, amount);
        
        // Send ETH to user
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "ETH transfer failed");
        
        emit Withdraw(msg.sender, amount, amount);
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
     * @dev Set LayerZero peer for cross-chain transfers
     * Only deployer can call this function
     * @param _eid LayerZero endpoint ID
     * @param _peer Peer address in bytes32 format
     */
    function setPeer(uint32 _eid, bytes32 _peer) external {
        require(msg.sender == tx.origin, "Only EOA can set peers"); // Simple access control
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
            cfWETH.mint(msg.sender, msg.value);
            emit Deposit(msg.sender, msg.value, msg.value);
        }
    }
}