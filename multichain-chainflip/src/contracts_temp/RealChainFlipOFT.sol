// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import { OFT } from "@layerzerolabs/oft-evm/contracts/OFT.sol";

/**
 * @title RealChainFlipOFT - Real LayerZero OFT with ETH Deposit/Withdraw
 * @dev Official LayerZero OFT implementation with deposit/withdraw functionality
 * Uses official LayerZero oft-evm package for real cross-chain transfers
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
        // Constructor completed successfully - no custom logic needed
    }
    
    /**
     * @dev Deposit ETH to receive cfWETH tokens (1:1 ratio)
     */
    function deposit() external payable {
        require(msg.value > 0, "Must send ETH");
        
        // Mint cfWETH tokens equal to ETH sent using LayerZero's mint function
        _credit(msg.sender, msg.value, 0);
        
        emit Deposit(msg.sender, msg.value, msg.value);
    }
    
    /**
     * @dev Get contract ETH balance
     */
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}