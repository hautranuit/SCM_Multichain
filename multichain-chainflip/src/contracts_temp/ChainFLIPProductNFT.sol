// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ChainFLIPProductNFT
 * @dev Simple ERC-721 contract optimized for ChainFLIP supply chain product tracking
 * This contract is designed to work seamlessly with the ChainFLIP backend metadata structure
 */
contract ChainFLIPProductNFT is ERC721URIStorage, AccessControl, Ownable {
    // Role for accounts that can mint NFTs
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    
    // Contract version for compatibility tracking
    string public constant VERSION = "1.0.0";
    
    // Contract description
    string public description = "ChainFLIP Supply Chain Product NFTs - Tracking authentic products through the supply chain";
    
    // Events for better tracking
    event ProductMinted(uint256 indexed tokenId, address indexed to, string uri, uint256 timestamp);
    event TokenURIUpdated(uint256 indexed tokenId, string newURI, uint256 timestamp);
    
    constructor(
        string memory name,
        string memory symbol,
        address initialOwner
    ) ERC721(name, symbol) {
        // Grant the contract deployer the default admin role and minter role
        _grantRole(DEFAULT_ADMIN_ROLE, initialOwner);
        _grantRole(MINTER_ROLE, initialOwner);
        
        // Transfer ownership to the initial owner
        _transferOwnership(initialOwner);
    }
    
    /**
     * @dev Mint NFT with token ID and URI (matches current backend expectation)
     * This function signature matches what the blockchain service expects
     */
    function safeMint(
        address to,
        uint256 tokenId,
        string memory uri
    ) public onlyRole(MINTER_ROLE) {
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
        
        emit ProductMinted(tokenId, to, uri, block.timestamp);
    }
    
    /**
     * @dev Alternative mint function with auto-generated token ID
     * Returns the generated token ID for better integration
     */
    function safeMint(
        address to,
        string memory uri
    ) public onlyRole(MINTER_ROLE) returns (uint256) {
        uint256 tokenId = _getNextTokenId();
        
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
        
        emit ProductMinted(tokenId, to, uri, block.timestamp);
        return tokenId;
    }
    
    /**
     * @dev Update token URI (for metadata updates)
     */
    function setTokenURI(
        uint256 tokenId,
        string memory uri
    ) public onlyRole(MINTER_ROLE) {
        require(_exists(tokenId), "ChainFLIPProductNFT: Token does not exist");
        _setTokenURI(tokenId, uri);
        
        emit TokenURIUpdated(tokenId, uri, block.timestamp);
    }
    
    /**
     * @dev Batch mint function for efficiency
     */
    function batchSafeMint(
        address[] memory recipients,
        uint256[] memory tokenIds,
        string[] memory uris
    ) public onlyRole(MINTER_ROLE) {
        require(
            recipients.length == tokenIds.length && tokenIds.length == uris.length,
            "ChainFLIPProductNFT: Arrays length mismatch"
        );
        
        for (uint256 i = 0; i < recipients.length; i++) {
            _safeMint(recipients[i], tokenIds[i]);
            _setTokenURI(tokenIds[i], uris[i]);
            emit ProductMinted(tokenIds[i], recipients[i], uris[i], block.timestamp);
        }
    }
    
    /**
     * @dev Check if a token exists
     */
    function exists(uint256 tokenId) public view returns (bool) {
        return _exists(tokenId);
    }
    
    /**
     * @dev Get total supply of minted tokens
     * Simple counter-based implementation for gas efficiency
     */
    uint256 private _tokenIdCounter = 1;
    
    function totalSupply() public view returns (uint256) {
        return _tokenIdCounter - 1;
    }
    
    /**
     * @dev Internal function to get next token ID and increment counter
     */
    function _getNextTokenId() internal returns (uint256) {
        uint256 tokenId = _tokenIdCounter;
        _tokenIdCounter++;
        return tokenId;
    }
    
    /**
     * @dev Grant minter role to an address
     */
    function grantMinterRole(address account) public onlyRole(DEFAULT_ADMIN_ROLE) {
        _grantRole(MINTER_ROLE, account);
    }
    
    /**
     * @dev Revoke minter role from an address
     */
    function revokeMinterRole(address account) public onlyRole(DEFAULT_ADMIN_ROLE) {
        _revokeRole(MINTER_ROLE, account);
    }
    
    /**
     * @dev Update contract description
     */
    function setDescription(string memory newDescription) public onlyOwner {
        description = newDescription;
    }
    
    /**
     * @dev Emergency pause functionality (for contract upgrades)
     */
    bool public paused = false;
    
    function pause() public onlyOwner {
        paused = true;
    }
    
    function unpause() public onlyOwner {
        paused = false;
    }
    
    modifier whenNotPaused() {
        require(!paused, "ChainFLIPProductNFT: Contract is paused");
        _;
    }
    
    // Override transfers to add pause functionality  
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal whenNotPaused override(ERC721) {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }
    
    /**
     * @dev Support for ERC165 interface detection
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721URIStorage, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
    
    /**
     * @dev Contract metadata for better compatibility with NFT marketplaces
     */
    function contractURI() public view returns (string memory) {
        return string(abi.encodePacked(
            "data:application/json;base64,",
            Base64.encode(bytes(abi.encodePacked(
                '{"name":"ChainFLIP Product NFTs","description":"',
                description,
                '","image":"","external_link":"","seller_fee_basis_points":0,"fee_recipient":""}'
            )))
        ));
    }
}

library Base64 {
    string internal constant TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    function encode(bytes memory data) internal pure returns (string memory) {
        if (data.length == 0) return "";
        
        string memory table = TABLE;
        uint256 encodedLen = 4 * ((data.length + 2) / 3);
        string memory result = new string(encodedLen + 32);

        assembly {
            let tablePtr := add(table, 1)
            let resultPtr := add(result, 32)
            
            for {
                let i := 0
            } lt(i, div(mload(data), 3)) {
                i := add(i, 1)
            } {
                let input := shl(248, mload(add(data, mul(3, i))))
                let out := mload(add(tablePtr, and(shr(18, input), 0x3F)))
                out := shl(8, out)
                out := add(out, and(mload(add(tablePtr, and(shr(12, input), 0x3F))), 0xFF))
                out := shl(8, out)
                out := add(out, and(mload(add(tablePtr, and(shr(6, input), 0x3F))), 0xFF))
                out := shl(8, out)
                out := add(out, and(mload(add(tablePtr, and(input, 0x3F))), 0xFF))
                out := shl(224, out)
                
                mstore(resultPtr, out)
                resultPtr := add(resultPtr, 4)
            }
            
            switch mod(mload(data), 3)
            case 1 {
                let input := shl(248, mload(add(data, div(mload(data), 3))))
                let out := mload(add(tablePtr, and(shr(18, input), 0x3F)))
                out := shl(8, out)
                out := add(out, and(mload(add(tablePtr, and(shr(12, input), 0x3F))), 0xFF))
                out := shl(16, out)
                out := add(out, 0x3d3d)
                out := shl(224, out)
                mstore(resultPtr, out)
                resultPtr := add(resultPtr, 4)
            }
            case 2 {
                let input := shl(248, mload(add(data, div(mload(data), 3))))
                let out := mload(add(tablePtr, and(shr(18, input), 0x3F)))
                out := shl(8, out)
                out := add(out, and(mload(add(tablePtr, and(shr(12, input), 0x3F))), 0xFF))
                out := shl(8, out)
                out := add(out, and(mload(add(tablePtr, and(shr(6, input), 0x3F))), 0xFF))
                out := shl(8, out)
                out := add(out, 0x3d)
                out := shl(224, out)
                mstore(resultPtr, out)
                resultPtr := add(resultPtr, 4)
            }
            
            mstore(result, encodedLen)
        }
        
        return result;
    }
}