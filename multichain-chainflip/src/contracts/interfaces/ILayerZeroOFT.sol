// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title ILayerZeroOFT
 * @dev Local LayerZero V2 interface to avoid npm dependency conflicts
 * Compatible with LayerZero V2 endpoint structure
 */

interface ILayerZeroEndpointV2 {
    struct MessagingFee {
        uint256 nativeFee;
        uint256 lzTokenFee;
    }
    
    struct MessagingReceipt {
        bytes32 guid;
        uint64 nonce;
        MessagingFee fee;
    }
    
    struct Origin {
        uint32 srcEid;
        bytes32 sender;
        uint64 nonce;
    }
    
    function send(
        uint32 _dstEid,
        bytes32 _to,
        bytes calldata _message,
        address _refundAddress,
        bytes calldata _options
    ) external payable returns (MessagingReceipt memory);
    
    function quote(
        uint32 _dstEid,
        bytes32 _to,
        bytes calldata _message,
        bytes calldata _options,
        bool _payInLzToken
    ) external view returns (MessagingFee memory);
    
    function eid() external view returns (uint32);
}

/**
 * @title OFTCore
 * @dev Simplified LayerZero OFT core functionality
 */
abstract contract OFTCore {
    ILayerZeroEndpointV2 public immutable endpoint;
    mapping(uint32 => bytes32) public peers;
    
    event PeerSet(uint32 eid, bytes32 peer);
    
    struct SendParam {
        uint32 dstEid;
        bytes32 to;
        uint256 amountLD;
        uint256 minAmountLD;
        bytes extraOptions;
        bytes composeMsg;
        bytes oftCmd;
    }
    
    // Use ILayerZeroEndpointV2 types directly to avoid conflicts
    
    constructor(address _endpoint) {
        endpoint = ILayerZeroEndpointV2(_endpoint);
    }
    
    function setPeer(uint32 _eid, bytes32 _peer) external virtual {
        peers[_eid] = _peer;
        emit PeerSet(_eid, _peer);
    }
    
    function quoteSend(
        SendParam calldata _sendParam,
        bool _payInLzToken
    ) external view virtual returns (ILayerZeroEndpointV2.MessagingFee memory fee);
    
    function send(
        SendParam calldata _sendParam,
        ILayerZeroEndpointV2.MessagingFee calldata _fee,
        address _refundAddress
    ) external payable virtual returns (ILayerZeroEndpointV2.MessagingReceipt memory receipt);
}