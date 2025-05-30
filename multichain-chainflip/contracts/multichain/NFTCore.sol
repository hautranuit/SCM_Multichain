// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
* @title NFTCore - Multi-Chain Compatible
* @dev Core contract for minting, transferring NFTs and managing dynamic QR data, collateral, and payment release.
* Enhanced for multi-chain support with cross-chain messaging capability.
*/
contract NFTCore is ERC721URIStorage, AccessControl {
    uint256 internal _nextTokenId = 1;
    mapping(uint256 => string) public cidMapping; // Store the CID of ProductHistory file in IPFS

    // --- Dynamic QR Data Storage (Enhanced from RFID) ---
    struct ProductData {
        string uniqueProductID;
        string batchNumber;
        string manufacturingDate;
        string expirationDate;
        string productType;
        string manufacturerID;
        string quickAccessURL;
        string nftReference;
        uint256 sourceChainId; // Track origin chain
        bytes32 crossChainHash; // For cross-chain verification
    }
    
    enum PurchaseStatus {
        Idle,             
        Listed,           
        AwaitingCollateral,
        CollateralDeposited,
        InTransit,
        TransportCompleted,
        AwaitingRelease,  
        ReceiptConfirmed,
        Complete,         
        Disputed          
    }

    struct PurchaseInfo {
        address buyer;
        address seller;
        uint256 price;
        uint256 collateral;
        PurchaseStatus status;
        uint256 chainId; // Track which chain the purchase is on
    }

    mapping(uint256 => ProductData) public productDataMapping; // Enhanced from rfidDataMapping
    mapping(uint256 => PurchaseInfo) public purchaseInfos;
    mapping(bytes32 => bool) public crossChainHashes; // Prevent duplicate cross-chain operations

    // --- Roles ---
    bytes32 public constant UPDATER_ROLE = keccak256("UPDATER_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant CROSS_CHAIN_ROLE = keccak256("CROSS_CHAIN_ROLE");

    // --- Multi-Chain Events ---
    event ProductMinted(uint256 indexed tokenId, address indexed owner, string uniqueProductID, string batchNumber, string manufacturingDate, uint256 sourceChainId, uint256 timestamp);
    event ProductTransferred(uint256 indexed tokenId, address indexed from, address indexed to, uint256 timestamp);
    event CrossChainTransferInitiated(uint256 indexed tokenId, uint256 targetChainId, address targetAddress, bytes32 crossChainHash, uint256 timestamp);
    event CrossChainTransferCompleted(uint256 indexed tokenId, uint256 sourceChainId, bytes32 crossChainHash, uint256 timestamp);
    event PaymentReleased(uint256 indexed tokenId, address indexed seller, uint256 amount, uint256 timestamp);
    event TransporterIncentivePaid(uint256 indexed tokenId, address indexed transporter, uint256 amount, uint256 timestamp);
    event DisputeInitiated(uint256 indexed tokenId, address indexed initiator, address currentOwner, uint256 timestamp);
    event CIDStored(uint256 indexed tokenId, string cid, address indexed actor, uint256 timestamp);
    event InitialCIDStored(uint256 indexed tokenId, string initialCID, address indexed actor, uint256 timestamp);
    event CIDToHistoryStored(uint256 indexed tokenId, string newCid, address indexed actor, uint256 timestamp);
    event CollateralDepositedForPurchase(uint256 indexed tokenId, address indexed buyer, uint256 amount, uint256 timestamp);
    event PurchaseCompleted(uint256 indexed tokenId, address indexed buyer, address indexed seller, uint256 price, uint256 timestamp);
    event ReceiptConfirmed(uint256 indexed tokenId, address indexed confirmer, uint256 timestamp);
    event PaymentAndTransferCompleted(uint256 indexed tokenId, address indexed buyer, address indexed seller, uint256 price, uint256 timestamp);
    event PurchaseStatusUpdated(uint256 indexed tokenId, PurchaseStatus oldStatus, PurchaseStatus newStatus, address indexed actor, uint256 timestamp);
    event DynamicQRGenerated(uint256 indexed tokenId, string encryptedPayload, uint256 timestamp);

    constructor(address initialAdmin)
        ERC721("ChainFLIP_MultiChain_NFT", "CFMC") 
    {
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(UPDATER_ROLE, initialAdmin); 
        _grantRole(MINTER_ROLE, initialAdmin);
        _grantRole(CROSS_CHAIN_ROLE, initialAdmin);
    }

    struct MintNFTParams {
        address recipient;
        string uniqueProductID;
        string batchNumber;
        string manufacturingDate;
        string expirationDate;
        string productType;
        string manufacturerID;
        string quickAccessURL;
        string nftReference;
    }

    function mintNFT(
        MintNFTParams memory params
    ) public onlyRole(MINTER_ROLE) returns (uint256) {
        uint256 tokenId = _nextTokenId++;
        uint256 currentChainId = block.chainid;
        
        // Generate cross-chain hash for uniqueness
        bytes32 crossChainHash = keccak256(abi.encodePacked(
            currentChainId, 
            tokenId, 
            params.uniqueProductID, 
            block.timestamp
        ));

        _safeMint(params.recipient, tokenId);

        productDataMapping[tokenId] = ProductData({
            uniqueProductID: params.uniqueProductID,
            batchNumber: params.batchNumber,
            manufacturingDate: params.manufacturingDate,
            expirationDate: params.expirationDate,
            productType: params.productType,
            manufacturerID: params.manufacturerID,
            quickAccessURL: params.quickAccessURL,
            nftReference: params.nftReference,
            sourceChainId: currentChainId,
            crossChainHash: crossChainHash
        });

        crossChainHashes[crossChainHash] = true;

        emit ProductMinted(tokenId, params.recipient, params.uniqueProductID, params.batchNumber, params.manufacturingDate, currentChainId, block.timestamp);
        return tokenId;
    }

    // --- Cross-Chain Functions ---
    function initiateCrossChainTransfer(
        uint256 tokenId,
        uint256 targetChainId,
        address targetAddress
    ) external onlyRole(CROSS_CHAIN_ROLE) {
        require(_exists(tokenId), "NFTCore: Token does not exist");
        require(ownerOf(tokenId) == msg.sender, "NFTCore: Not token owner");
        
        ProductData memory productData = productDataMapping[tokenId];
        bytes32 crossChainHash = keccak256(abi.encodePacked(
            block.chainid,
            targetChainId,
            tokenId,
            targetAddress,
            block.timestamp
        ));

        emit CrossChainTransferInitiated(tokenId, targetChainId, targetAddress, crossChainHash, block.timestamp);
        
        // In a full implementation, this would interact with a cross-chain bridge
        // For now, we emit the event for the backend to handle
    }

    function completeCrossChainTransfer(
        uint256 tokenId,
        uint256 sourceChainId,
        bytes32 crossChainHash,
        address newOwner
    ) external onlyRole(CROSS_CHAIN_ROLE) {
        require(!crossChainHashes[crossChainHash], "NFTCore: Cross-chain hash already used");
        
        crossChainHashes[crossChainHash] = true;
        
        if (_exists(tokenId)) {
            _transfer(ownerOf(tokenId), newOwner, tokenId);
        }
        
        emit CrossChainTransferCompleted(tokenId, sourceChainId, crossChainHash, block.timestamp);
    }

    // --- Dynamic QR Code Integration ---
    function generateDynamicQR(uint256 tokenId, string memory encryptedPayload) 
        external onlyRole(UPDATER_ROLE) {
        require(_exists(tokenId), "NFTCore: Token does not exist");
        emit DynamicQRGenerated(tokenId, encryptedPayload, block.timestamp);
    }

    // Helper function to check if a token exists
    function _exists(uint256 tokenId) internal view returns (bool) {
        return _ownerOf(tokenId) != address(0);
    }

    function storeInitialCID(uint256 tokenId, string memory cid) public onlyRole(UPDATER_ROLE) {
        require(_exists(tokenId), "NFTCore: Token does not exist");
        cidMapping[tokenId] = cid;
        emit InitialCIDStored(tokenId, cid, msg.sender, block.timestamp);
    }

    function storeCIDToHistory(uint256 tokenId, string memory newCid) public onlyRole(UPDATER_ROLE) {
        require(_exists(tokenId), "NFTCore: Token does not exist");
        cidMapping[tokenId] = newCid; 
        emit CIDToHistoryStored(tokenId, newCid, msg.sender, block.timestamp);
    }

    function verifyProductAuthenticity(
        uint256 tokenId,
        string memory expectedCID,
        address currentOwner
    ) public view returns (string memory) {
        address actualOwner = ownerOf(tokenId);
        if (actualOwner != currentOwner) {
            return "Ownership Mismatch"; 
        }
        string memory storedCID = cidMapping[tokenId];
        if (bytes(storedCID).length == 0) { 
            return "Stored CID not found for this token";
        }
        if (keccak256(bytes(expectedCID)) != keccak256(bytes(storedCID))) {
            return "CID Mismatch"; 
        }
        return "Product is Authentic";
    }
    
    function _transferNFTInternal(address from, address to, uint256 tokenId) internal virtual {
        _transfer(from, to, tokenId);
        emit ProductTransferred(tokenId, from, to, block.timestamp);
    }

    function depositPurchaseCollateral(uint256 tokenId) public payable {
        PurchaseInfo storage purchase = purchaseInfos[tokenId];
        require(purchase.status == PurchaseStatus.AwaitingCollateral, "NFTCore: Not awaiting collateral");
        require(msg.value > 0, "NFTCore: Collateral amount must be greater than 0");
        require(msg.sender == purchase.buyer, "NFTCore: Only buyer can deposit collateral");

        purchase.collateral = msg.value;
        purchase.status = PurchaseStatus.CollateralDeposited;
        purchase.chainId = block.chainid;
        
        emit CollateralDepositedForPurchase(tokenId, msg.sender, msg.value, block.timestamp);
        emit PurchaseStatusUpdated(tokenId, PurchaseStatus.AwaitingCollateral, PurchaseStatus.CollateralDeposited, msg.sender, block.timestamp);
    }

    function triggerDispute(uint256 tokenId) internal virtual {
        emit DisputeInitiated(tokenId, msg.sender, ownerOf(tokenId), block.timestamp);
    }

    function _releasePurchasePaymentInternal(uint256 tokenId, bool meetsIncentiveCriteria, address actor) internal { 
        PurchaseInfo storage purchase = purchaseInfos[tokenId];
        require(purchase.status == PurchaseStatus.TransportCompleted, "NFTCore: Payment can only be released after delivery confirmation");

        uint256 paymentAmount = purchase.price;
        (bool success, ) = payable(purchase.seller).call{value: paymentAmount}("");
        require(success, "NFTCore: Payment transfer to seller failed");

        emit PaymentReleased(tokenId, purchase.seller, paymentAmount, block.timestamp);

        PurchaseStatus oldStatus = purchase.status;
        purchase.status = PurchaseStatus.Complete; 
        emit PurchaseStatusUpdated(tokenId, oldStatus, PurchaseStatus.Complete, actor, block.timestamp);
    }

    function confirmReceipt(uint256 tokenId) public {
        PurchaseInfo storage purchase = purchaseInfos[tokenId];
        require(purchase.status == PurchaseStatus.TransportCompleted, "NFTCore: Transport not completed or purchase not in correct status");
        require(msg.sender == purchase.buyer, "NFTCore: Only buyer can confirm receipt");

        purchase.status = PurchaseStatus.ReceiptConfirmed;
        emit ReceiptConfirmed(tokenId, msg.sender, block.timestamp);
        emit PurchaseStatusUpdated(tokenId, PurchaseStatus.TransportCompleted, PurchaseStatus.ReceiptConfirmed, msg.sender, block.timestamp);
    }

    function updateProductHistoryCID(uint256 tokenId, string memory newCid) public onlyRole(UPDATER_ROLE) {
        require(bytes(cidMapping[tokenId]).length > 0, "NFTCore: Initial CID not set, cannot update history");
        cidMapping[tokenId] = newCid;
        emit CIDToHistoryStored(tokenId, newCid, msg.sender, block.timestamp);
    }

    function confirmDeliveryAndFinalize(uint256 tokenId, bool meetsIncentiveCriteria) public {
        PurchaseInfo storage purchase = purchaseInfos[tokenId];

        require(purchase.status == PurchaseStatus.TransportCompleted, "NFTCore: Product not yet marked as transport completed by transporter"); 
        require(msg.sender == purchase.buyer || hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "NFTCore: Only buyer or admin can confirm delivery");

        address currentOwner = ownerOf(tokenId); 

        if (currentOwner != purchase.buyer) {
            require(currentOwner != address(0), "NFTCore: Invalid current owner for transfer");
            _transferNFTInternal(currentOwner, purchase.buyer, tokenId);
        }

        _releasePurchasePaymentInternal(tokenId, meetsIncentiveCriteria, msg.sender);

        emit PaymentAndTransferCompleted(tokenId, purchase.buyer, purchase.seller, purchase.price, block.timestamp);
    }

    function sellerReleaseFunds(uint256 tokenId, bool meetsIncentiveCriteria) public {
        PurchaseInfo storage purchase = purchaseInfos[tokenId];
        require(msg.sender == purchase.seller, "NFTCore: Only seller can release payment");
        require(purchase.status == PurchaseStatus.TransportCompleted || purchase.status == PurchaseStatus.ReceiptConfirmed, "NFTCore: Invalid status for seller to release funds");

        _releasePurchasePaymentInternal(tokenId, meetsIncentiveCriteria, msg.sender);
    }

    // --- Multi-Chain Helper Functions ---
    function getProductData(uint256 tokenId) external view returns (ProductData memory) {
        return productDataMapping[tokenId];
    }

    function isFromChain(uint256 tokenId, uint256 chainId) external view returns (bool) {
        return productDataMapping[tokenId].sourceChainId == chainId;
    }

    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC721URIStorage, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}