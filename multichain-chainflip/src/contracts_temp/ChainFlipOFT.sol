// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import { OFT } from "@layerzerolabs/oft-evm/contracts/OFT.sol";

/**
 * @title ChainFlipOFT - Pure LayerZero OFT
 * @dev Clean LayerZero OFT implementation without custom logic
 * This contract handles only cross-chain transfers via LayerZero
 */
contract ChainFlipOFT is OFT {
    
    constructor(
        string memory _name,
        string memory _symbol,
        address _lzEndpoint,
        address _delegate
    ) OFT(_name, _symbol, _lzEndpoint, _delegate) {
        // Pure LayerZero OFT - no custom logic
    }
    
    /**
     * @dev Allow wrapper contract to mint tokens
     * Only the wrapper contract should be able to mint
     */
    function mint(address _to, uint256 _amount) external onlyOwner {
        _mint(_to, _amount);
    }
    
    /**
     * @dev Allow wrapper contract to burn tokens
     * Only the wrapper contract should be able to burn
     */
    function burn(address _from, uint256 _amount) external onlyOwner {
        _burn(_from, _amount);
    }
}