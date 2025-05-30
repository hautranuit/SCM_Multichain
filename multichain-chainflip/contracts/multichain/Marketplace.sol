// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "./NFTCore.sol";

/**
* @title Marketplace - Multi-Chain Compatible
* @dev Abstract contract for marketplace functionality with cross-chain trading support
*/
abstract contract Marketplace is NFTCore {
    mapping(uint256 => uint256) public listingPrice;
    
    // --- Cross-Chain Trading Support ---
    mapping(uint256 => uint256) public listingChainId; // Track which chain a product is listed on
    mapping(bytes32 => bool) public processedCrossChainTrades;
    
    // --- FL Integration for Market Analysis ---
    struct MarketMetrics {
        uint256 totalVolume;
        uint256 averagePrice;
        uint256 anomalyScore; // FL-based market anomaly detection
        uint256 lastUpdated;
    }
    
    mapping(uint256 => MarketMetrics) public chainMarketMetrics; // chainId => metrics

    // --- Events ---
    event ProductListedForSale(uint256 indexed tokenId, address indexed seller, uint256 price, uint256 chainId, uint256 timestamp);
    event PurchaseInitiated(uint256 indexed tokenId, address indexed buyer, address indexed seller, uint256 price, uint256 timestamp);
    event TransportStarted(uint256 indexed tokenId, address indexed owner, address[] transporters, string startLocation, string endLocation, uint256 distance, uint256 timestamp);
    event TransportCompleted(uint256 indexed tokenId, address indexed completer, uint256 timestamp);
    event ProductDelisted(uint256 indexed tokenId, address indexed seller, uint256 timestamp);
    event ProductPriceChanged(uint256 indexed tokenId, address indexed seller, uint256 oldPrice, uint256 newPrice, uint256 timestamp);
    
    // --- Cross-Chain Events ---
    event CrossChainListingSync(uint256 indexed tokenId, uint256 targetChainId, uint256 price, bytes32 syncHash, uint256 timestamp);
    event CrossChainTradeCompleted(uint256 indexed tokenId, uint256 sourceChainId, uint256 targetChainId, address buyer, address seller, uint256 price, uint256 timestamp);
    event MarketAnomalyDetected(uint256 chainId, uint256 anomalyScore, string reason, uint256 timestamp);
    event CrossChainPriceSync(uint256 indexed tokenId, uint256[] chainIds, uint256[] prices, uint256 timestamp);

    function sellProduct(uint256 tokenId, uint256 price) public virtual {
        require(ownerOf(tokenId) == msg.sender, "Marketplace: You do not own this NFT");
        require(price > 0, "Marketplace: Price must be > 0");

        listingPrice[tokenId] = price;
        listingChainId[tokenId] = block.chainid;

        // Update market metrics for FL analysis
        _updateMarketMetrics(block.chainid, price);

        emit ProductListedForSale(tokenId, msg.sender, price, block.chainid, block.timestamp);
    }

    function sellProductCrossChain(uint256 tokenId, uint256 price, uint256[] memory targetChainIds) public virtual {
        require(ownerOf(tokenId) == msg.sender, "Marketplace: You do not own this NFT");
        require(price > 0, "Marketplace: Price must be > 0");
        require(targetChainIds.length > 0, "Marketplace: Must specify target chains");

        listingPrice[tokenId] = price;
        listingChainId[tokenId] = block.chainid;

        // Update market metrics
        _updateMarketMetrics(block.chainid, price);

        // Sync listing to target chains
        for (uint256 i = 0; i < targetChainIds.length; i++) {
            bytes32 syncHash = keccak256(abi.encodePacked(
                tokenId,
                block.chainid,
                targetChainIds[i],
                price,
                block.timestamp
            ));
            
            emit CrossChainListingSync(tokenId, targetChainIds[i], price, syncHash, block.timestamp);
        }

        emit ProductListedForSale(tokenId, msg.sender, price, block.chainid, block.timestamp);
        emit CrossChainPriceSync(tokenId, targetChainIds, _createPriceArray(price, targetChainIds.length), block.timestamp);
    }

    function delistProduct(uint256 tokenId) public virtual {
        require(ownerOf(tokenId) == msg.sender, "Marketplace: You do not own this NFT");
        require(listingPrice[tokenId] > 0, "Marketplace: Product not listed for sale");

        listingPrice[tokenId] = 0;
        listingChainId[tokenId] = 0;
        emit ProductDelisted(tokenId, msg.sender, block.timestamp);
    }

    function changeProductPrice(uint256 tokenId, uint256 newPrice) public virtual {
        require(ownerOf(tokenId) == msg.sender, "Marketplace: You do not own this NFT");
        require(listingPrice[tokenId] > 0, "Marketplace: Product not listed for sale");
        require(newPrice > 0, "Marketplace: New price must be > 0");

        uint256 oldPrice = listingPrice[tokenId];
        listingPrice[tokenId] = newPrice;
        
        // Update market metrics
        _updateMarketMetrics(block.chainid, newPrice);

        emit ProductPriceChanged(tokenId, msg.sender, oldPrice, newPrice, block.timestamp);
    }

    function initiatePurchase(uint256 tokenId, string memory CIDHash) public {
        uint256 price = listingPrice[tokenId];
        require(price > 0, "Marketplace: Product not listed for sale");

        address currentOwner = ownerOf(tokenId);

        string memory result = verifyProductAuthenticity(tokenId, CIDHash, currentOwner);
        require(keccak256(bytes(result)) == keccak256(bytes("Product is Authentic")), result);

        PurchaseInfo storage purchase = purchaseInfos[tokenId];
        require(purchase.status == PurchaseStatus.Listed || purchase.status == PurchaseStatus.Idle, "Marketplace: Purchase already in progress or not listed");

        purchase.buyer = msg.sender;
        purchase.seller = currentOwner;
        purchase.price = price;
        purchase.status = PurchaseStatus.AwaitingCollateral;
        purchase.chainId = block.chainid;

        listingPrice[tokenId] = 0; // Mark as no longer listed at this price

        // Update market metrics
        _updateMarketMetrics(block.chainid, price);

        emit PurchaseInitiated(tokenId, msg.sender, currentOwner, price, block.timestamp);
    }

    function initiateCrossChainPurchase(
        uint256 tokenId, 
        string memory CIDHash, 
        uint256 targetChainId
    ) public payable {
        uint256 price = listingPrice[tokenId];
        require(price > 0, "Marketplace: Product not listed for sale");
        require(msg.value >= price, "Marketplace: Insufficient payment for cross-chain purchase");

        address currentOwner = ownerOf(tokenId);
        string memory result = verifyProductAuthenticity(tokenId, CIDHash, currentOwner);
        require(keccak256(bytes(result)) == keccak256(bytes("Product is Authentic")), result);

        bytes32 tradeHash = keccak256(abi.encodePacked(
            tokenId,
            block.chainid,
            targetChainId,
            msg.sender,
            currentOwner,
            price,
            block.timestamp
        ));

        require(!processedCrossChainTrades[tradeHash], "Cross-chain trade already processed");
        processedCrossChainTrades[tradeHash] = true;

        PurchaseInfo storage purchase = purchaseInfos[tokenId];
        purchase.buyer = msg.sender;
        purchase.seller = currentOwner;
        purchase.price = price;
        purchase.status = PurchaseStatus.AwaitingCollateral;
        purchase.chainId = targetChainId; // Set target chain

        listingPrice[tokenId] = 0;

        emit CrossChainTradeCompleted(tokenId, block.chainid, targetChainId, msg.sender, currentOwner, price, block.timestamp);
        emit PurchaseInitiated(tokenId, msg.sender, currentOwner, price, block.timestamp);
    }

    function startTransport(
        uint256 tokenId,
        address[] memory transporters,
        string memory startLocation,
        string memory endLocation,
        uint256 distance
    ) public {
        require(ownerOf(tokenId) == msg.sender, "Marketplace: Only owner can start transport");
        uint256 numTransporters = transporters.length;
        require(numTransporters > 0, "Marketplace: Must specify at least one transporter");

        PurchaseInfo storage purchase = purchaseInfos[tokenId];
        require(purchase.status == PurchaseStatus.CollateralDeposited, "Marketplace: Collateral not deposited or transport already handled");

        PurchaseStatus oldStatus = purchase.status;
        purchase.status = PurchaseStatus.InTransit;

        emit TransportStarted(tokenId, msg.sender, transporters, startLocation, endLocation, distance, block.timestamp);
        emit PurchaseStatusUpdated(tokenId, oldStatus, PurchaseStatus.InTransit, msg.sender, block.timestamp);
    }

    function completeTransport(uint256 tokenId) public {
        PurchaseInfo storage purchase = purchaseInfos[tokenId];
        require(purchase.status == PurchaseStatus.InTransit, "Marketplace: Transport not started or already completed");

        purchase.status = PurchaseStatus.TransportCompleted;
        emit TransportCompleted(tokenId, msg.sender, block.timestamp);
        emit PurchaseStatusUpdated(tokenId, PurchaseStatus.InTransit, PurchaseStatus.TransportCompleted, msg.sender, block.timestamp);
    }

    // --- FL Integration Functions ---
    function _updateMarketMetrics(uint256 chainId, uint256 price) internal {
        MarketMetrics storage metrics = chainMarketMetrics[chainId];
        
        if (metrics.lastUpdated == 0) {
            metrics.totalVolume = price;
            metrics.averagePrice = price;
        } else {
            metrics.totalVolume += price;
            // Simple moving average (could be enhanced with more sophisticated algorithms)
            metrics.averagePrice = (metrics.averagePrice + price) / 2;
        }
        
        metrics.lastUpdated = block.timestamp;
        
        // Simple anomaly detection (would be enhanced by FL model)
        if (price > metrics.averagePrice * 3) { // Price is 3x higher than average
            metrics.anomalyScore += 10;
            if (metrics.anomalyScore > 50) {
                emit MarketAnomalyDetected(chainId, metrics.anomalyScore, "Price significantly above average", block.timestamp);
            }
        } else if (metrics.anomalyScore > 0) {
            metrics.anomalyScore -= 1; // Gradual decay
        }
    }

    function updateMarketAnomalyScore(uint256 chainId, uint256 newScore, string memory reason) external onlyRole(UPDATER_ROLE) {
        MarketMetrics storage metrics = chainMarketMetrics[chainId];
        metrics.anomalyScore = newScore;
        
        if (newScore > 70) {
            emit MarketAnomalyDetected(chainId, newScore, reason, block.timestamp);
        }
    }

    // --- Helper Functions ---
    function _createPriceArray(uint256 price, uint256 length) internal pure returns (uint256[] memory) {
        uint256[] memory prices = new uint256[](length);
        for (uint256 i = 0; i < length; i++) {
            prices[i] = price;
        }
        return prices;
    }

    // --- View Functions ---
    function getMarketMetrics(uint256 chainId) public view returns (MarketMetrics memory) {
        return chainMarketMetrics[chainId];
    }

    function isListedOnChain(uint256 tokenId, uint256 chainId) public view returns (bool) {
        return listingChainId[tokenId] == chainId && listingPrice[tokenId] > 0;
    }

    function getCrossChainListingStatus(uint256 tokenId) public view returns (uint256 chainId, uint256 price) {
        return (listingChainId[tokenId], listingPrice[tokenId]);
    }
}