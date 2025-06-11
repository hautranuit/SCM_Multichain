// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

// Simplified LayerZero V2 interfaces (no external dependencies)
interface ILayerZeroEndpointV2 {
    struct MessagingParams {
        uint32 dstEid;
        bytes32 receiver;
        bytes message;
        bytes options;
        bool payInLzToken;
    }
    
    struct MessagingReceipt {
        bytes32 guid;
        uint64 nonce;
        MessagingFee fee;
    }
    
    struct MessagingFee {
        uint256 nativeFee;
        uint256 lzTokenFee;
    }
    
    function send(
        MessagingParams calldata _params,
        address _refundAddress
    ) external payable returns (MessagingReceipt memory);
    
    function quote(
        MessagingParams calldata _params,
        address _sender
    ) external view returns (MessagingFee memory);
}

interface ILayerZeroReceiver {
    function lzReceive(
        Origin calldata _origin,
        bytes32 _guid,
        bytes calldata _message,
        address _executor,
        bytes calldata _extraData
    ) external payable;
}

struct Origin {
    uint32 srcEid;
    bytes32 sender;
    uint64 nonce;
}

/**
 * @title WETHOFT
 * @dev Simplified LayerZero OFT implementation for WETH cross-chain transfers
 * Compatible with existing LayerZero infrastructure without external dependencies
 */
contract WETHOFT is ERC20, Ownable, ReentrancyGuard, ILayerZeroReceiver {
    
    // LayerZero endpoint
    ILayerZeroEndpointV2 public immutable lzEndpoint;
    
    // WETH contract on this chain
    IERC20 public immutable wethToken;
    
    // Peer addresses on other chains (eid => peer address)
    mapping(uint32 => bytes32) public peers;
    
    // Message types
    uint8 constant SEND = 1;
    uint8 constant SEND_AND_CALL = 2;
    
    // Events
    event WETHDeposited(address indexed user, uint256 amount);
    event WETHWithdrawn(address indexed user, uint256 amount);
    event PeerSet(uint32 indexed eid, bytes32 peer);
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
    ) ERC20(_name, _symbol) Ownable(_delegate) {
        lzEndpoint = ILayerZeroEndpointV2(_lzEndpoint);
        wethToken = IERC20(_wethToken);
    }
    
    /**
     * @dev Set peer address for a destination chain
     */
    function setPeer(uint32 _eid, bytes32 _peer) external onlyOwner {
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
     * @dev Send OFT tokens cross-chain (Backend-compatible signature)
     */
    function send(
        uint32 _dstEid,
        bytes32 _to,
        uint256 _amountLD,
        uint256 _minAmountLD,
        bytes calldata _extraOptions,
        ILayerZeroEndpointV2.MessagingFee calldata _fee,
        address _refundAddress
    ) external payable nonReentrant returns (ILayerZeroEndpointV2.MessagingReceipt memory) {
        require(peers[_dstEid] != bytes32(0), "Peer not set");
        require(balanceOf(msg.sender) >= _amountLD, "Insufficient balance");
        require(_amountLD >= _minAmountLD, "Amount less than minimum");
        require(msg.value >= _fee.nativeFee, "Insufficient fee");
        
        // Burn tokens on source chain
        _burn(msg.sender, _amountLD);
        
        // Prepare message
        bytes memory message = abi.encode(SEND, _to, _amountLD);
        
        // Send LayerZero message
        ILayerZeroEndpointV2.MessagingParams memory params = ILayerZeroEndpointV2.MessagingParams({
            dstEid: _dstEid,
            receiver: peers[_dstEid],
            message: message,
            options: _extraOptions,
            payInLzToken: false
        });
        
        ILayerZeroEndpointV2.MessagingReceipt memory receipt = lzEndpoint.send{value: _fee.nativeFee}(
            params,
            payable(_refundAddress)
        );
        
        emit OFTSent(receipt.guid, _dstEid, msg.sender, _amountLD, _amountLD);
        
        return receipt;
    }
    
    /**
     * @dev Get quote for cross-chain send (Backend-compatible signature)
     */
    function quoteSend(
        uint32 _dstEid,
        bytes32 _to,
        uint256 _amountLD,
        uint256 _minAmountLD,
        bytes calldata _extraOptions,
        bool _payInLzToken
    ) external view returns (ILayerZeroEndpointV2.MessagingFee memory) {
        require(peers[_dstEid] != bytes32(0), "Peer not set");
        
        bytes memory message = abi.encode(SEND, _to, _amountLD);
        
        ILayerZeroEndpointV2.MessagingParams memory params = ILayerZeroEndpointV2.MessagingParams({
            dstEid: _dstEid,
            receiver: peers[_dstEid],
            message: message,
            options: _extraOptions,
            payInLzToken: _payInLzToken
        });
        
        return lzEndpoint.quote(params, address(this));
    }
    
    /**
     * @dev Legacy send function for backward compatibility
     */
    function send(
        uint32 _dstEid,
        bytes32 _to,
        uint256 _amountLD,
        uint256 _minAmountLD,
        bytes calldata _extraOptions
    ) external payable nonReentrant returns (ILayerZeroEndpointV2.MessagingReceipt memory) {
        // Use default fee structure
        ILayerZeroEndpointV2.MessagingFee memory fee = ILayerZeroEndpointV2.MessagingFee({
            nativeFee: msg.value,
            lzTokenFee: 0
        });
        
        return this.send(_dstEid, _to, _amountLD, _minAmountLD, _extraOptions, fee, msg.sender);
    }
    
    /**
     * @dev Receive LayerZero message
     */
    function lzReceive(
        Origin calldata _origin,
        bytes32 _guid,
        bytes calldata _message,
        address /* _executor */,
        bytes calldata /* _extraData */
    ) external payable override {
        require(msg.sender == address(lzEndpoint), "Only endpoint");
        require(_origin.sender == peers[_origin.srcEid], "Invalid sender");
        
        (uint8 msgType, bytes32 to, uint256 amountLD) = abi.decode(_message, (uint8, bytes32, uint256));
        
        if (msgType == SEND) {
            address toAddress = address(uint160(uint256(to)));
            
            // Mint tokens on destination chain
            _mint(toAddress, amountLD);
            
            emit OFTReceived(_guid, _origin.srcEid, toAddress, amountLD);
        }
    }
    
    /**
     * @dev Check if peer is set
     */
    function isPeer(uint32 _eid, bytes32 _peer) external view returns (bool) {
        return peers[_eid] == _peer;
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
}
