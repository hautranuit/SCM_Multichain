// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { OFT } from "@layerzerolabs/oft-evm/contracts/OFT.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title WETHOFT
 * @dev Official LayerZero V2 OFT implementation for WETH cross-chain transfers
 * Compatible with LayerZero V2 endpoints and official OFT standards
 */
contract WETHOFT is OFT, ReentrancyGuard {
    
    // WETH contract on this chain
    IERC20 public immutable wethToken;
    
    // Events
    event WETHDeposited(address indexed user, uint256 amount);
    event WETHWithdrawn(address indexed user, uint256 amount);
    event OFTSent(
        bytes32 indexed guid,
        uint32 dstEid,
        address indexed fromAddress,
        uint256 amountSentLD,
        uint256 amountReceivedLD
    );
    event OFTReceived(
        bytes32 indexed guid,
        uint32 srcEid,
        address indexed toAddress,
        uint256 amountReceivedLD
    );
    
    constructor(
        string memory _name,
        string memory _symbol,
        address _lzEndpoint,
        address _wethToken,
        address _delegate
    ) OFT(_name, _symbol, _lzEndpoint, _delegate) Ownable(_delegate) {
        wethToken = IERC20(_wethToken);
    }
    
    /**
     * @dev Deposit WETH to mint OFT tokens
     */
    function depositWETH(uint256 amount) external nonReentrant {
        require(amount > 0, "Amount must be greater than 0");
        require(wethToken.transferFrom(msg.sender, address(this), amount), "WETH transfer failed");
        
        // Mint OFT tokens 1:1 with WETH
        _mint(msg.sender, amount);
        
        emit WETHDeposited(msg.sender, amount);
    }
    
    /**
     * @dev Withdraw WETH by burning OFT tokens
     */
    function withdrawWETH(uint256 amount) external nonReentrant {
        require(amount > 0, "Amount must be greater than 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient OFT balance");
        
        // Burn OFT tokens
        _burn(msg.sender, amount);
        
        // Transfer WETH back to user
        require(wethToken.transfer(msg.sender, amount), "WETH transfer failed");
        
        emit WETHWithdrawn(msg.sender, amount);
    }
    
    /**
     * @dev Wrap ETH to WETH and deposit to get OFT tokens (convenience function)
     */
    function wrapAndDeposit() external payable nonReentrant {
        require(msg.value > 0, "Must send ETH");
        
        // First wrap ETH to WETH (assuming WETH contract has deposit function)
        (bool success,) = address(wethToken).call{value: msg.value}("");
        require(success, "ETH to WETH wrap failed");
        
        // Then mint OFT tokens
        _mint(msg.sender, msg.value);
        
        emit WETHDeposited(msg.sender, msg.value);
    }
    
    /**
     * @dev Get the total WETH backing
     */
    function getTotalWETHBacking() external view returns (uint256) {
        return wethToken.balanceOf(address(this));
    }
    
    /**
     * @dev Emergency function to rescue tokens (only owner)
     */
    function rescueTokens(address token, uint256 amount) external onlyOwner {
        require(token != address(wethToken), "Cannot rescue WETH");
        IERC20(token).transfer(owner(), amount);
    }
    
    /**
     * @dev Override _lzSend to add custom logging
     */
    function _lzSend(
        uint32 _dstEid,
        bytes memory _message,
        bytes memory _options,
        MessagingFee memory _fee,
        address _refundAddress
    ) internal virtual override returns (MessagingReceipt memory receipt) {
        receipt = super._lzSend(_dstEid, _message, _options, _fee, _refundAddress);
        
        // Decode message to get recipient and amount for logging
        // This assumes standard OFT message format
        if (_message.length >= 32) {
            bytes32 toAddress;
            uint256 amountLD;
            assembly {
                toAddress := mload(add(_message, 32))
                amountLD := mload(add(_message, 64))
            }
            
            emit OFTSent(receipt.guid, _dstEid, msg.sender, amountLD, amountLD);
        }
        
        return receipt;
    }
    
    /**
     * @dev Override _lzReceive to add custom logging
     */
    function _lzReceive(
        Origin calldata _origin,
        bytes32 _guid,
        bytes calldata _message,
        address /*_executor*/,
        bytes calldata /*_extraData*/
    ) internal virtual override {
        super._lzReceive(_origin, _guid, _message, address(0), "");
        
        // Decode message to get recipient and amount for logging
        if (_message.length >= 32) {
            bytes32 toAddressBytes32;
            uint256 amountLD;
            assembly {
                toAddressBytes32 := mload(add(_message, 32))
                amountLD := mload(add(_message, 64))
            }
            
            address toAddress = address(uint160(uint256(toAddressBytes32)));
            emit OFTReceived(_guid, _origin.srcEid, toAddress, amountLD);
        }
    }
}
