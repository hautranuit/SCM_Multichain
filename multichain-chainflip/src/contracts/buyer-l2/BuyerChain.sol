// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title BuyerChain
 * @dev Specialized L2 contract for buyers implementing:
 * - Algorithm 5: Post Supply Chain Management for NFT-based Product Sale
 * - Algorithm 2: Dispute Resolution and Voting Mechanism (Purchase disputes)
 * - Algorithm 1: Payment Release and Incentive Mechanism (Purchase payments)
 */
contract BuyerChain is AccessControl, ReentrancyGuard, Pausable {
    
    // --- Core Data Structures ---
    struct Purchase {
        uint256 purchaseId;
        uint256 productTokenId;
        bytes32 productHash; // From manufacturer chain
        bytes32 shipmentHash; // From transporter chain
        address buyer;
        address seller;
        uint256 price;
        uint256 collateral;
        PurchaseStatus status;
        uint256 purchaseTime;
        uint256 deliveryTime;
        uint256 confirmationDeadline;
        bool paymentReleased;
        string deliveryLocation;
        bytes32 crossChainHash;
    }

    enum PurchaseStatus {
        Created,
        Paid,
        InTransit,
        Delivered,
        Confirmed,
        Disputed,
        Completed,
        Refunded
    }

    struct Dispute {
        uint256 disputeId;
        uint256 purchaseId;
        address plaintiff;
        address defendant;
        string reason;
        string evidenceCID;
        DisputeStatus status;
        address[] arbitrators;
        mapping(address => bool) votes; // arbitrator => vote (true = favor plaintiff)
        uint256 votesFor;
        uint256 votesAgainst;
        string resolution;
        uint256 openedTime;
        uint256 resolvedTime;
        bytes32 crossChainHash;
    }

    enum DisputeStatus {
        Open,
        UnderReview,
        Resolved,
        Escalated
    }

    struct Marketplace {
        uint256 listingId;
        uint256 productTokenId;
        bytes32 productHash;
        address seller;
        uint256 price;
        string productDescription;
        string metadataCID;
        bool isActive;
        uint256 listedTime;
        MarketplaceCategory category;
    }

    enum MarketplaceCategory {
        Electronics,
        Clothing,
        Food,
        Medicine,
        Other
    }

    struct BuyerIncentive {
        address buyer;
        uint256 totalPurchases;
        uint256 totalSpent;
        uint256 loyaltyPoints;
        uint256 incentivePool;
        uint256 lastClaim;
    }

    // --- FL Integration for Buyer Behavior ---
    struct FLBuyerMetrics {
        uint256 purchasePatternScore;
        uint256 fraudRiskScore;
        uint256 anomalyScore;
        uint256 lastModelUpdate;
    }

    // --- State Variables ---
    uint256 private _nextPurchaseId = 1;
    uint256 private _nextDisputeId = 1;
    uint256 private _nextListingId = 1;
    
    mapping(uint256 => Purchase) public purchases;
    mapping(uint256 => Dispute) public disputes;
    mapping(uint256 => Marketplace) public marketplaceListings;
    mapping(address => BuyerIncentive) public buyerIncentives;
    mapping(address => FLBuyerMetrics) public buyerFLMetrics;
    mapping(bytes32 => bool) public processedCrossChainActions;
    mapping(uint256 => uint256) public purchaseToDispute; // purchaseId => disputeId
    
    address[] public registeredArbitrators;
    uint256 public disputeResolutionFee = 0.001 ether;
    uint256 public confirmationPeriod = 7 days;
    uint256 public hubChainId = 80002;
    address public hubContract;

    // --- Roles ---
    bytes32 public constant BUYER_ROLE = keccak256("BUYER_ROLE");
    bytes32 public constant SELLER_ROLE = keccak256("SELLER_ROLE");
    bytes32 public constant ARBITRATOR_ROLE = keccak256("ARBITRATOR_ROLE");
    bytes32 public constant HUB_COORDINATOR_ROLE = keccak256("HUB_COORDINATOR_ROLE");

    // --- Events ---
    event PurchaseCreated(
        uint256 indexed purchaseId,
        uint256 indexed productTokenId,
        address indexed buyer,
        address seller,
        uint256 price,
        uint256 timestamp
    );
    
    event PurchaseStatusUpdated(
        uint256 indexed purchaseId,
        PurchaseStatus oldStatus,
        PurchaseStatus newStatus,
        address updatedBy,
        uint256 timestamp
    );
    
    event PaymentReleased(
        uint256 indexed purchaseId,
        address indexed seller,
        uint256 amount,
        uint256 timestamp
    );
    
    event DisputeOpened(
        uint256 indexed disputeId,
        uint256 indexed purchaseId,
        address indexed plaintiff,
        string reason,
        uint256 timestamp
    );
    
    event DisputeResolved(
        uint256 indexed disputeId,
        address winner,
        string resolution,
        uint256 timestamp
    );
    
    event MarketplaceListing(
        uint256 indexed listingId,
        uint256 indexed productTokenId,
        address indexed seller,
        uint256 price,
        MarketplaceCategory category,
        uint256 timestamp
    );
    
    event BuyerIncentivePaid(
        address indexed buyer,
        uint256 amount,
        uint256 loyaltyPoints,
        uint256 timestamp
    );
    
    event FLFraudAlert(
        address indexed buyer,
        uint256 fraudRiskScore,
        string reason,
        uint256 timestamp
    );

    constructor(
        address initialAdmin,
        address _hubContract
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(BUYER_ROLE, initialAdmin);
        _grantRole(SELLER_ROLE, initialAdmin);
        _grantRole(ARBITRATOR_ROLE, initialAdmin);
        _grantRole(HUB_COORDINATOR_ROLE, initialAdmin);
        hubContract = _hubContract;
    }

    // --- Algorithm 5: Post Supply Chain Management for NFT-based Product Sale ---
    function createMarketplaceListing(
        uint256 productTokenId,
        bytes32 productHash,
        uint256 price,
        string memory productDescription,
        string memory metadataCID,
        MarketplaceCategory category
    ) external onlyRole(SELLER_ROLE) whenNotPaused returns (uint256) {
        require(price > 0, "Price must be greater than 0");
        
        uint256 listingId = _nextListingId++;
        
        marketplaceListings[listingId] = Marketplace({
            listingId: listingId,
            productTokenId: productTokenId,
            productHash: productHash,
            seller: msg.sender,
            price: price,
            productDescription: productDescription,
            metadataCID: metadataCID,
            isActive: true,
            listedTime: block.timestamp,
            category: category
        });

        emit MarketplaceListing(listingId, productTokenId, msg.sender, price, category, block.timestamp);
        return listingId;
    }

    function createPurchase(
        uint256 listingId,
        string memory deliveryLocation
    ) external payable onlyRole(BUYER_ROLE) whenNotPaused returns (uint256) {
        require(marketplaceListings[listingId].isActive, "Listing not active");
        
        Marketplace storage listing = marketplaceListings[listingId];
        require(msg.value >= listing.price, "Insufficient payment");
        require(msg.sender != listing.seller, "Cannot buy your own product");
        
        uint256 purchaseId = _nextPurchaseId++;
        
        bytes32 crossChainHash = keccak256(abi.encodePacked(
            purchaseId,
            listing.productTokenId,
            listing.productHash,
            msg.sender,
            listing.seller,
            block.chainid,
            block.timestamp
        ));

        purchases[purchaseId] = Purchase({
            purchaseId: purchaseId,
            productTokenId: listing.productTokenId,
            productHash: listing.productHash,
            shipmentHash: bytes32(0), // Will be updated from transporter chain
            buyer: msg.sender,
            seller: listing.seller,
            price: listing.price,
            collateral: msg.value - listing.price, // Extra payment as collateral
            status: PurchaseStatus.Paid,
            purchaseTime: block.timestamp,
            deliveryTime: 0,
            confirmationDeadline: block.timestamp + confirmationPeriod,
            paymentReleased: false,
            deliveryLocation: deliveryLocation,
            crossChainHash: crossChainHash
        });

        // Update buyer incentive metrics
        BuyerIncentive storage incentive = buyerIncentives[msg.sender];
        incentive.buyer = msg.sender;
        incentive.totalPurchases++;
        incentive.totalSpent += listing.price;
        incentive.loyaltyPoints += listing.price / 1000; // 1 point per 1000 wei spent

        // FL fraud detection
        _updateBuyerFLMetrics(msg.sender, listing.price);

        // Deactivate listing
        listing.isActive = false;

        emit PurchaseCreated(purchaseId, listing.productTokenId, msg.sender, listing.seller, listing.price, block.timestamp);
        return purchaseId;
    }

    function confirmDelivery(uint256 purchaseId) external onlyRole(BUYER_ROLE) whenNotPaused {
        require(purchases[purchaseId].buyer == msg.sender, "Not the buyer");
        require(purchases[purchaseId].status == PurchaseStatus.Delivered, "Product not delivered");
        require(block.timestamp <= purchases[purchaseId].confirmationDeadline, "Confirmation period expired");
        
        _updatePurchaseStatus(purchaseId, PurchaseStatus.Confirmed);
        _releasePurchasePayment(purchaseId);
    }

    // --- Algorithm 1: Payment Release and Incentive Mechanism ---
    function _releasePurchasePayment(uint256 purchaseId) internal {
        Purchase storage purchase = purchases[purchaseId];
        require(!purchase.paymentReleased, "Payment already released");
        require(purchase.status == PurchaseStatus.Confirmed, "Purchase not confirmed");
        
        purchase.paymentReleased = true;
        purchase.status = PurchaseStatus.Completed;
        
        // Calculate seller payment (price + performance bonus)
        uint256 sellerPayment = purchase.price;
        uint256 performanceBonus = 0;
        
        // Early delivery bonus
        if (purchase.deliveryTime > 0 && purchase.deliveryTime < purchase.confirmationDeadline - 2 days) {
            performanceBonus = purchase.price / 20; // 5% bonus for early delivery
        }
        
        uint256 totalPayment = sellerPayment + performanceBonus;
        
        // Return collateral to buyer
        if (purchase.collateral > 0) {
            (bool collateralSuccess, ) = payable(purchase.buyer).call{value: purchase.collateral}("");
            require(collateralSuccess, "Collateral return failed");
        }
        
        // Pay seller
        (bool paymentSuccess, ) = payable(purchase.seller).call{value: totalPayment}("");
        require(paymentSuccess, "Payment to seller failed");
        
        emit PaymentReleased(purchaseId, purchase.seller, totalPayment, block.timestamp);
        emit PurchaseStatusUpdated(purchaseId, PurchaseStatus.Confirmed, PurchaseStatus.Completed, msg.sender, block.timestamp);
    }

    function calculateBuyerIncentive(address buyer) public view returns (uint256) {
        BuyerIncentive memory incentive = buyerIncentives[buyer];
        
        if (incentive.totalPurchases == 0) return 0;
        
        // Base incentive: loyalty points converted to ETH
        uint256 baseIncentive = incentive.loyaltyPoints * 1000; // 1 point = 1000 wei
        
        // Volume bonus: extra incentive for high-volume buyers
        uint256 volumeBonus = 0;
        if (incentive.totalPurchases >= 10) {
            volumeBonus = baseIncentive / 10; // 10% bonus
        }
        
        // FL behavior bonus
        FLBuyerMetrics memory flMetrics = buyerFLMetrics[buyer];
        uint256 behaviorBonus = 0;
        if (flMetrics.fraudRiskScore < 20) { // Low fraud risk
            behaviorBonus = baseIncentive / 20; // 5% behavior bonus
        }
        
        return baseIncentive + volumeBonus + behaviorBonus;
    }

    function claimBuyerIncentive() external onlyRole(BUYER_ROLE) nonReentrant {
        uint256 incentiveAmount = calculateBuyerIncentive(msg.sender);
        require(incentiveAmount > 0, "No incentive available");
        require(address(this).balance >= incentiveAmount, "Insufficient contract balance");
        
        BuyerIncentive storage incentive = buyerIncentives[msg.sender];
        require(block.timestamp > incentive.lastClaim + 1 days, "Can only claim once per day");
        
        incentive.lastClaim = block.timestamp;
        incentive.incentivePool += incentiveAmount;
        incentive.loyaltyPoints = 0; // Reset after claim
        
        (bool success, ) = payable(msg.sender).call{value: incentiveAmount}("");
        require(success, "Incentive transfer failed");
        
        emit BuyerIncentivePaid(msg.sender, incentiveAmount, incentive.loyaltyPoints, block.timestamp);
    }

    // --- Algorithm 2: Dispute Resolution and Voting Mechanism ---
    function openDispute(
        uint256 purchaseId,
        string memory reason,
        string memory evidenceCID
    ) external payable onlyRole(BUYER_ROLE) whenNotPaused returns (uint256) {
        require(msg.value >= disputeResolutionFee, "Insufficient dispute fee");
        require(purchases[purchaseId].buyer == msg.sender, "Not the buyer");
        require(purchases[purchaseId].status != PurchaseStatus.Completed, "Purchase already completed");
        require(purchaseToDispute[purchaseId] == 0, "Dispute already exists");
        
        uint256 disputeId = _nextDisputeId++;
        
        Dispute storage dispute = disputes[disputeId];
        dispute.disputeId = disputeId;
        dispute.purchaseId = purchaseId;
        dispute.plaintiff = msg.sender;
        dispute.defendant = purchases[purchaseId].seller;
        dispute.reason = reason;
        dispute.evidenceCID = evidenceCID;
        dispute.status = DisputeStatus.Open;
        dispute.openedTime = block.timestamp;
        dispute.crossChainHash = keccak256(abi.encodePacked(
            disputeId,
            purchaseId,
            msg.sender,
            block.chainid,
            block.timestamp
        ));

        // Assign random arbitrators
        _assignArbitrators(disputeId);
        
        purchaseToDispute[purchaseId] = disputeId;
        _updatePurchaseStatus(purchaseId, PurchaseStatus.Disputed);

        emit DisputeOpened(disputeId, purchaseId, msg.sender, reason, block.timestamp);
        return disputeId;
    }

    function _assignArbitrators(uint256 disputeId) internal {
        require(registeredArbitrators.length >= 3, "Not enough arbitrators");
        
        Dispute storage dispute = disputes[disputeId];
        
        // Select 3 random arbitrators
        uint256 seed = uint256(keccak256(abi.encodePacked(block.timestamp, disputeId)));
        for (uint i = 0; i < 3; i++) {
            uint256 index = (seed + i) % registeredArbitrators.length;
            dispute.arbitrators.push(registeredArbitrators[index]);
        }
        
        dispute.status = DisputeStatus.UnderReview;
    }

    function voteOnDispute(
        uint256 disputeId,
        bool favorPlaintiff,
        string memory reasoning
    ) external onlyRole(ARBITRATOR_ROLE) whenNotPaused {
        Dispute storage dispute = disputes[disputeId];
        require(dispute.status == DisputeStatus.UnderReview, "Dispute not under review");
        require(_isArbitratorAssigned(disputeId, msg.sender), "Not assigned to this dispute");
        require(!dispute.votes[msg.sender], "Already voted");
        
        dispute.votes[msg.sender] = true;
        
        if (favorPlaintiff) {
            dispute.votesFor++;
        } else {
            dispute.votesAgainst++;
        }
        
        // Check if voting is complete
        if (dispute.votesFor + dispute.votesAgainst >= dispute.arbitrators.length) {
            _resolveDispute(disputeId);
        }
    }

    function _resolveDispute(uint256 disputeId) internal {
        Dispute storage dispute = disputes[disputeId];
        
        bool plaintiffWins = dispute.votesFor > dispute.votesAgainst;
        address winner = plaintiffWins ? dispute.plaintiff : dispute.defendant;
        
        dispute.status = DisputeStatus.Resolved;
        dispute.resolvedTime = block.timestamp;
        dispute.resolution = plaintiffWins ? "Favor buyer" : "Favor seller";
        
        Purchase storage purchase = purchases[dispute.purchaseId];
        
        if (plaintiffWins) {
            // Refund buyer
            uint256 refundAmount = purchase.price + purchase.collateral;
            purchase.status = PurchaseStatus.Refunded;
            
            (bool success, ) = payable(purchase.buyer).call{value: refundAmount}("");
            require(success, "Refund failed");
        } else {
            // Release payment to seller
            _releasePurchasePayment(dispute.purchaseId);
        }
        
        emit DisputeResolved(disputeId, winner, dispute.resolution, block.timestamp);
    }

    function _isArbitratorAssigned(uint256 disputeId, address arbitrator) internal view returns (bool) {
        Dispute storage dispute = disputes[disputeId];
        for (uint i = 0; i < dispute.arbitrators.length; i++) {
            if (dispute.arbitrators[i] == arbitrator) {
                return true;
            }
        }
        return false;
    }

    // --- FL Integration Functions ---
    function _updateBuyerFLMetrics(address buyer, uint256 purchaseAmount) internal {
        FLBuyerMetrics storage metrics = buyerFLMetrics[buyer];
        
        // Update purchase pattern score
        metrics.purchasePatternScore += 1;
        
        // Fraud risk detection based on purchase patterns
        BuyerIncentive memory incentive = buyerIncentives[buyer];
        if (incentive.totalPurchases > 0) {
            uint256 avgPurchase = incentive.totalSpent / incentive.totalPurchases;
            
            // Flag unusually large purchases
            if (purchaseAmount > avgPurchase * 10) {
                metrics.fraudRiskScore += 20;
                metrics.anomalyScore += 15;
                
                if (metrics.fraudRiskScore > 70) {
                    emit FLFraudAlert(buyer, metrics.fraudRiskScore, "Unusually large purchase detected", block.timestamp);
                }
            }
        }
        
        metrics.lastModelUpdate = block.timestamp;
    }

    function updateFLModel(address buyer, uint256 newFraudScore) external onlyRole(HUB_COORDINATOR_ROLE) {
        buyerFLMetrics[buyer].fraudRiskScore = newFraudScore;
        buyerFLMetrics[buyer].lastModelUpdate = block.timestamp;
    }

    // --- Cross-Chain Coordination ---
    function updatePurchaseFromShipment(
        uint256 purchaseId,
        bytes32 shipmentHash,
        PurchaseStatus newStatus
    ) external onlyRole(HUB_COORDINATOR_ROLE) {
        require(purchases[purchaseId].purchaseId != 0, "Purchase does not exist");
        
        purchases[purchaseId].shipmentHash = shipmentHash;
        if (newStatus == PurchaseStatus.Delivered) {
            purchases[purchaseId].deliveryTime = block.timestamp;
        }
        
        _updatePurchaseStatus(purchaseId, newStatus);
    }

    function _updatePurchaseStatus(uint256 purchaseId, PurchaseStatus newStatus) internal {
        PurchaseStatus oldStatus = purchases[purchaseId].status;
        purchases[purchaseId].status = newStatus;
        
        emit PurchaseStatusUpdated(purchaseId, oldStatus, newStatus, msg.sender, block.timestamp);
    }

    // --- View Functions ---
    function getPurchase(uint256 purchaseId) external view returns (Purchase memory) {
        require(purchases[purchaseId].purchaseId != 0, "Purchase does not exist");
        return purchases[purchaseId];
    }

    function getDispute(uint256 disputeId) external view returns (
        uint256, uint256, address, address, string memory, string memory,
        DisputeStatus, address[] memory, uint256, uint256, string memory,
        uint256, uint256
    ) {
        Dispute storage dispute = disputes[disputeId];
        return (
            dispute.disputeId,
            dispute.purchaseId,
            dispute.plaintiff,
            dispute.defendant,
            dispute.reason,
            dispute.evidenceCID,
            dispute.status,
            dispute.arbitrators,
            dispute.votesFor,
            dispute.votesAgainst,
            dispute.resolution,
            dispute.openedTime,
            dispute.resolvedTime
        );
    }

    function getMarketplaceListing(uint256 listingId) external view returns (Marketplace memory) {
        return marketplaceListings[listingId];
    }

    function getBuyerMetrics(address buyer) external view returns (BuyerIncentive memory, FLBuyerMetrics memory) {
        return (buyerIncentives[buyer], buyerFLMetrics[buyer]);
    }

    // --- Admin Functions ---
    function registerArbitrator(address arbitrator) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(!hasRole(ARBITRATOR_ROLE, arbitrator), "Already an arbitrator");
        
        _grantRole(ARBITRATOR_ROLE, arbitrator);
        registeredArbitrators.push(arbitrator);
    }

    function setDisputeResolutionFee(uint256 newFee) external onlyRole(DEFAULT_ADMIN_ROLE) {
        disputeResolutionFee = newFee;
    }

    function setConfirmationPeriod(uint256 newPeriod) external onlyRole(DEFAULT_ADMIN_ROLE) {
        confirmationPeriod = newPeriod;
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    function updateHubContract(address newHub) external onlyRole(DEFAULT_ADMIN_ROLE) {
        hubContract = newHub;
    }

    // --- Funding ---
    receive() external payable {}
    
    function withdrawFunds(uint256 amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(address(this).balance >= amount, "Insufficient balance");
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Withdrawal failed");
    }
}