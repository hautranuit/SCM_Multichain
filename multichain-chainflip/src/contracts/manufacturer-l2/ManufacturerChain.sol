// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title ManufacturerChain
 * @dev Specialized L2 contract for manufacturers implementing:
 * - Algorithm 4: Product Authenticity Verification Using RFID and NFT
 * - Algorithm 1: Payment Release and Incentive Mechanism (Manufacturing)
 * - Algorithm 3: Supply Chain Consensus Algorithm (Product Creation)
 */
contract ManufacturerChain is ERC721URIStorage, AccessControl, ReentrancyGuard, Pausable {
    
    // --- Core Data Structures ---
    struct Product {
        uint256 tokenId;
        string uniqueProductID;
        string batchNumber;
        string manufacturingDate;
        string expirationDate;
        string productType;
        string manufacturerID;
        string metadataCID;
        string imageCID;          // New: IPFS CID for product image
        string videoCID;          // New: IPFS CID for product video
        address manufacturer;
        uint256 createdAt;
        bool qualityApproved;
        uint256 manufacturingCost;
        uint256 priceInWei;       // New: Price in ETH (wei)
        string location;          // New: Manufacturing location
        string category;          // New: Product category
        bytes32 crossChainHash;
    }

    struct QualityCheck {
        uint256 productId;
        address inspector;
        bool passed;
        string reportCID;
        uint256 timestamp;
        uint256 score; // 0-100
    }

    struct ManufacturingIncentive {
        address manufacturer;
        uint256 totalProduced;
        uint256 qualityScore;
        uint256 incentivePool;
        uint256 lastClaim;
    }

    // --- FL Integration for Manufacturing ---
    struct FLManufacturingMetrics {
        uint256 defectRate;
        uint256 qualityTrend;
        uint256 anomalyScore;
        uint256 lastModelUpdate;
    }

    // --- State Variables ---
    uint256 private _nextTokenId = 1;
    uint256 private _nextQualityCheckId = 1;
    
    mapping(uint256 => Product) public products;
    mapping(uint256 => QualityCheck) public qualityChecks;
    mapping(address => ManufacturingIncentive) public manufacturerIncentives;
    mapping(string => uint256) public productIdMapping; // uniqueProductID => tokenId
    mapping(address => FLManufacturingMetrics) public manufacturerFLMetrics;
    
    // Cross-chain coordination
    mapping(bytes32 => bool) public processedCrossChainActions;
    uint256 public hubChainId = 80002; // Polygon Amoy testnet
    address public hubContract;

    // --- Roles ---
    bytes32 public constant MANUFACTURER_ROLE = keccak256("MANUFACTURER_ROLE");
    bytes32 public constant QUALITY_INSPECTOR_ROLE = keccak256("QUALITY_INSPECTOR_ROLE");
    bytes32 public constant HUB_COORDINATOR_ROLE = keccak256("HUB_COORDINATOR_ROLE");

    // --- Events ---
    event ProductMinted(
        uint256 indexed tokenId,
        address indexed manufacturer,
        string uniqueProductID,
        string batchNumber,
        string metadataCID,
        string imageCID,
        string videoCID,
        uint256 priceInWei,
        string location,
        string category,
        uint256 timestamp
    );
    
    event QualityCheckCompleted(
        uint256 indexed productId,
        address indexed inspector,
        bool passed,
        uint256 score,
        string reportCID,
        uint256 timestamp
    );
    
    event ManufacturingIncentivePaid(
        address indexed manufacturer,
        uint256 amount,
        uint256 qualityScore,
        uint256 timestamp
    );
    
    event ProductApprovedForShipment(
        uint256 indexed tokenId,
        address indexed manufacturer,
        bytes32 crossChainHash,
        uint256 timestamp
    );
    
    event FLAnomalyDetected(
        address indexed manufacturer,
        uint256 anomalyScore,
        string reason,
        uint256 timestamp
    );

    constructor(
        address initialAdmin,
        address _hubContract
    ) ERC721("ChainFLIP_Manufacturer_NFT", "CFM") {
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(MANUFACTURER_ROLE, initialAdmin);
        _grantRole(QUALITY_INSPECTOR_ROLE, initialAdmin);
        _grantRole(HUB_COORDINATOR_ROLE, initialAdmin);
        hubContract = _hubContract;
    }

    // --- Algorithm 4: Product Authenticity Verification ---
    function mintProduct(
        string memory uniqueProductID,
        string memory batchNumber,
        string memory manufacturingDate,
        string memory expirationDate,
        string memory productType,
        string memory manufacturerID,
        string memory metadataCID,
        string memory imageCID,
        string memory videoCID,
        uint256 manufacturingCost,
        uint256 priceInWei,
        string memory location,
        string memory category
    ) external onlyRole(MANUFACTURER_ROLE) whenNotPaused returns (uint256) {
        require(productIdMapping[uniqueProductID] == 0, "Product ID already exists");
        require(bytes(uniqueProductID).length > 0, "Product ID cannot be empty");
        require(bytes(metadataCID).length > 0, "Metadata CID cannot be empty");
        
        uint256 tokenId = _nextTokenId++;
        
        // Generate cross-chain hash for verification
        bytes32 crossChainHash = keccak256(abi.encodePacked(
            tokenId,
            uniqueProductID,
            batchNumber,
            msg.sender,
            block.chainid,
            block.timestamp
        ));

        products[tokenId] = Product({
            tokenId: tokenId,
            uniqueProductID: uniqueProductID,
            batchNumber: batchNumber,
            manufacturingDate: manufacturingDate,
            expirationDate: expirationDate,
            productType: productType,
            manufacturerID: manufacturerID,
            metadataCID: metadataCID,
            imageCID: imageCID,
            videoCID: videoCID,
            manufacturer: msg.sender,
            createdAt: block.timestamp,
            qualityApproved: false,
            manufacturingCost: manufacturingCost,
            priceInWei: priceInWei,
            location: location,
            category: category,
            crossChainHash: crossChainHash
        });

        productIdMapping[uniqueProductID] = tokenId;
        _safeMint(msg.sender, tokenId);
        _setTokenURI(tokenId, metadataCID);

        // Update manufacturer metrics
        ManufacturingIncentive storage incentive = manufacturerIncentives[msg.sender];
        incentive.manufacturer = msg.sender;
        incentive.totalProduced++;

        emit ProductMinted(
            tokenId, 
            msg.sender, 
            uniqueProductID, 
            batchNumber, 
            metadataCID, 
            imageCID,
            videoCID,
            priceInWei,
            location,
            category,
            block.timestamp
        );
        return tokenId;
    }

    function verifyProductAuthenticity(
        uint256 tokenId,
        string memory expectedCID,
        address expectedOwner
    ) external view returns (bool isAuthentic, string memory status) {
        if (!_exists(tokenId)) {
            return (false, "Product does not exist");
        }
        
        Product memory product = products[tokenId];
        
        if (ownerOf(tokenId) != expectedOwner) {
            return (false, "Ownership mismatch");
        }
        
        if (keccak256(bytes(product.metadataCID)) != keccak256(bytes(expectedCID))) {
            return (false, "Metadata CID mismatch");
        }
        
        if (!product.qualityApproved) {
            return (false, "Product not quality approved");
        }
        
        return (true, "Product is authentic and approved");
    }

    // --- Algorithm 3: Supply Chain Consensus (Quality Control) ---
    function performQualityCheck(
        uint256 productId,
        bool passed,
        uint256 score,
        string memory reportCID
    ) external onlyRole(QUALITY_INSPECTOR_ROLE) whenNotPaused {
        require(_exists(productId), "Product does not exist");
        require(score <= 100, "Score must be between 0-100");
        
        uint256 checkId = _nextQualityCheckId++;
        
        qualityChecks[checkId] = QualityCheck({
            productId: productId,
            inspector: msg.sender,
            passed: passed,
            reportCID: reportCID,
            timestamp: block.timestamp,
            score: score
        });

        Product storage product = products[productId];
        if (passed && score >= 70) { // Minimum quality threshold
            product.qualityApproved = true;
            
            // Update manufacturer incentive metrics
            ManufacturingIncentive storage incentive = manufacturerIncentives[product.manufacturer];
            incentive.qualityScore = (incentive.qualityScore + score) / 2; // Moving average
            
            // FL-based anomaly detection
            _updateManufacturerFLMetrics(product.manufacturer, score);
            
            emit ProductApprovedForShipment(productId, product.manufacturer, product.crossChainHash, block.timestamp);
        } else {
            // FL anomaly detection for failed quality checks
            FLManufacturingMetrics storage flMetrics = manufacturerFLMetrics[product.manufacturer];
            flMetrics.defectRate++;
            flMetrics.anomalyScore += 20;
            
            if (flMetrics.anomalyScore > 80) {
                emit FLAnomalyDetected(product.manufacturer, flMetrics.anomalyScore, "High defect rate detected", block.timestamp);
            }
        }

        emit QualityCheckCompleted(productId, msg.sender, passed, score, reportCID, block.timestamp);
    }

    // --- Algorithm 1: Manufacturing Incentive Mechanism ---
    function calculateManufacturingIncentive(address manufacturer) public view returns (uint256) {
        ManufacturingIncentive memory incentive = manufacturerIncentives[manufacturer];
        
        if (incentive.totalProduced == 0) return 0;
        
        // Base incentive: 0.01 ETH per product
        uint256 baseIncentive = incentive.totalProduced * 0.01 ether;
        
        // Quality bonus: up to 50% extra for high quality
        uint256 qualityBonus = (baseIncentive * incentive.qualityScore) / 200; // Max 50% bonus
        
        // FL-based efficiency bonus
        FLManufacturingMetrics memory flMetrics = manufacturerFLMetrics[manufacturer];
        uint256 efficiencyBonus = 0;
        if (flMetrics.anomalyScore < 30) { // Low anomaly score = high efficiency
            efficiencyBonus = baseIncentive / 10; // 10% efficiency bonus
        }
        
        return baseIncentive + qualityBonus + efficiencyBonus;
    }

    function claimManufacturingIncentive() external onlyRole(MANUFACTURER_ROLE) nonReentrant {
        uint256 incentiveAmount = calculateManufacturingIncentive(msg.sender);
        require(incentiveAmount > 0, "No incentive available");
        require(address(this).balance >= incentiveAmount, "Insufficient contract balance");
        
        ManufacturingIncentive storage incentive = manufacturerIncentives[msg.sender];
        require(block.timestamp > incentive.lastClaim + 1 days, "Can only claim once per day");
        
        incentive.lastClaim = block.timestamp;
        incentive.incentivePool += incentiveAmount;
        
        (bool success, ) = payable(msg.sender).call{value: incentiveAmount}("");
        require(success, "Incentive transfer failed");
        
        emit ManufacturingIncentivePaid(msg.sender, incentiveAmount, incentive.qualityScore, block.timestamp);
    }

    // --- Cross-Chain Coordination ---
    function syncProductToHub(uint256 tokenId) external onlyRole(HUB_COORDINATOR_ROLE) {
        require(_exists(tokenId), "Product does not exist");
        require(products[tokenId].qualityApproved, "Product not approved for shipping");
        
        Product memory product = products[tokenId];
        
        // This would typically interact with a cross-chain bridge
        // For now, we emit an event that the hub can listen to
        emit ProductApprovedForShipment(tokenId, product.manufacturer, product.crossChainHash, block.timestamp);
    }

    // --- FL Integration Functions ---
    function _updateManufacturerFLMetrics(address manufacturer, uint256 qualityScore) internal {
        FLManufacturingMetrics storage metrics = manufacturerFLMetrics[manufacturer];
        
        // Update quality trend
        if (qualityScore >= 80) {
            if (metrics.qualityTrend > 0) metrics.qualityTrend--;
        } else if (qualityScore < 60) {
            metrics.qualityTrend++;
        }
        
        // Update anomaly score based on trends
        if (metrics.qualityTrend > 5) {
            metrics.anomalyScore += 10;
        } else if (metrics.qualityTrend == 0 && metrics.anomalyScore > 0) {
            metrics.anomalyScore -= 5; // Gradual improvement
        }
        
        metrics.lastModelUpdate = block.timestamp;
    }

    function updateFLModel(address manufacturer, uint256 newAnomalyScore) external onlyRole(HUB_COORDINATOR_ROLE) {
        manufacturerFLMetrics[manufacturer].anomalyScore = newAnomalyScore;
        manufacturerFLMetrics[manufacturer].lastModelUpdate = block.timestamp;
    }

    // --- View Functions ---
    function getProduct(uint256 tokenId) external view returns (Product memory) {
        require(_exists(tokenId), "Product does not exist");
        return products[tokenId];
    }

    function getProductByUniqueId(string memory uniqueProductID) external view returns (Product memory) {
        uint256 tokenId = productIdMapping[uniqueProductID];
        require(tokenId != 0, "Product not found");
        return products[tokenId];
    }

    function getManufacturerMetrics(address manufacturer) external view returns (ManufacturingIncentive memory, FLManufacturingMetrics memory) {
        return (manufacturerIncentives[manufacturer], manufacturerFLMetrics[manufacturer]);
    }

    function _exists(uint256 tokenId) internal view returns (bool) {
        return _ownerOf(tokenId) != address(0);
    }

    // --- Admin Functions ---
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

    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC721URIStorage, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}