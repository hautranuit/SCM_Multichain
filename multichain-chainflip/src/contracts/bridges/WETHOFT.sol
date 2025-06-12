// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/ILayerZeroOFT.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title WETHOFT
 * @dev LayerZero V2 OFT implementation for WETH cross-chain transfers
 * Compatible with LayerZero V2 endpoints using local interface (no npm dependency conflicts)
 */
contract WETHOFT is ERC20, OFTCore, Ownable, ReentrancyGuard {
    
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
    ) 
        ERC20(_name, _symbol) 
        OFTCore(_lzEndpoint) 
        Ownable(_delegate) 
    {
        wethToken = IERC20(_wethToken);
    }
    
    /**
     * @dev Override setPeer to add owner restriction
     */
    function setPeer(uint32 _eid, bytes32 _peer) external override onlyOwner {
        peers[_eid] = _peer;
        emit PeerSet(_eid, _peer);
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
     * @dev LayerZero V2 quoteSend implementation
     */
    function quoteSend(
        SendParam calldata _sendParam,
        bool _payInLzToken
    ) external view override returns (ILayerZeroEndpointV2.MessagingFee memory fee) {
        // Encode OFT message
        bytes memory message = abi.encodePacked(
            _sendParam.to,
            _sendParam.amountLD
        );
        
        // Quote LayerZero fee
        return endpoint.quote(
            _sendParam.dstEid,
            _sendParam.to,
            message,
            _sendParam.extraOptions,
            _payInLzToken
        );
    }
    
    /**
     * @dev LayerZero V2 send implementation
     */
    function send(
        SendParam calldata _sendParam,
        ILayerZeroEndpointV2.MessagingFee calldata _fee,
        address _refundAddress
    ) external payable override returns (ILayerZeroEndpointV2.MessagingReceipt memory receipt) {
        // Check amount and burn tokens
        require(_sendParam.amountLD > 0, "Amount must be greater than 0");
        require(balanceOf(msg.sender) >= _sendParam.amountLD, "Insufficient balance");
        
        // Burn tokens from sender
        _burn(msg.sender, _sendParam.amountLD);
        
        // Encode OFT message
        bytes memory message = abi.encodePacked(
            _sendParam.to,
            _sendParam.amountLD
        );
        
        // Send via LayerZero
        return endpoint.send{value: msg.value}(
            _sendParam.dstEid,
            _sendParam.to,
            message,
            _refundAddress,
            _sendParam.extraOptions
        );
    }
    
    /**
     * @dev Receive LayerZero message and mint tokens
     */
    function lzReceive(
        uint32 _srcEid,
        bytes32 _sender,
        uint64 _nonce,
        bytes memory _message
    ) external {
        require(msg.sender == address(endpoint), "Only endpoint");
        require(_sender == peers[_srcEid], "Invalid sender");
        
        // Decode message
        bytes32 toBytes32;
        uint256 amountLD;
        
        // Use memory for assembly
        assembly {
            toBytes32 := mload(add(_message, 32))
            amountLD := mload(add(_message, 64))
        }
        
        address to = address(uint160(uint256(toBytes32)));
        
        // Mint tokens to recipient
        _mint(to, amountLD);
        
        emit OFTReceived(bytes32(uint256(_nonce)), _srcEid, to, amountLD);
    }
}