// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@layerzerolabs/oft-evm/contracts/oft/OFT.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title RealChainFlipOFT - Real LayerZero OFT with ETH Deposit/Withdraw
 * @dev Official LayerZero OFT implementation with deposit/withdraw functionality
 * Uses official @layerzerolabs/oft-evm package for real cross-chain transfers
 */
contract RealChainFlipOFT is OFT {
    
    // Events for deposit/withdraw
    event Deposit(address indexed user, uint256 ethAmount, uint256 tokensReceived);
    event Withdraw(address indexed user, uint256 tokenAmount, uint256 ethReceived);
    
    constructor(
        string memory _name,
        string memory _symbol,
        address _lzEndpoint,
        address _delegate
    ) OFT(_name, _symbol, _lzEndpoint, _delegate) {
        // Constructor automatically calls parent OFT constructor
    }
    
    /**
     * @dev Deposit ETH to receive cfWETH tokens (1:1 ratio)
     */
    function deposit() external payable {
        require(msg.value > 0, "Must send ETH");
        
        // Mint cfWETH tokens equal to ETH sent
        _mint(msg.sender, msg.value);
        
        emit Deposit(msg.sender, msg.value, msg.value);
    }
    
    /**
     * @dev Withdraw cfWETH tokens to receive ETH (1:1 ratio)
     * @param amount Amount of cfWETH tokens to withdraw
     */
    function withdraw(uint256 amount) external {
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
     * @dev Receive function to accept ETH deposits
     */
    receive() external payable {
        // Automatically convert ETH to cfWETH tokens
        if (msg.value > 0) {
            _mint(msg.sender, msg.value);
            emit Deposit(msg.sender, msg.value, msg.value);
        }
    }
}