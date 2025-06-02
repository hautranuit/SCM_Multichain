// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title EnhancedPolygonPoSHub
 * @dev Enhanced central hub contract on Polygon PoS for ChainFLIP multi-chain supply chain management
 * Coordinates all 5 algorithms across manufacturer, transporter, and buyer L2 chains
 */
contract EnhancedPolygonPoSHub is ERC721, Ownable, ReentrancyGuard, Pausable {
    
    // --- Enhanced Structures ---
    struct Product {
        uint256 tokenId;
        address manufacturer;
        string metadataCID;
        uint256 createdAt;
        address currentOwner;
        ProductStatus status;
        bool isActive;
        uint256 manufacturerChainId;
        bytes32 manufacturerHash;
        bool qualityApproved;
    }

    enum ProductStatus {
        Manufactured,
        QualityApproved,
        Listed,
        Sold,
        InTransit,
        Delivered,
        Completed
    }
    
    struct Participant {
        address participantAddress;
        string participantType; // "manufacturer", "transporter", "buyer"
        uint256 registeredAt;
        uint256 reputationScore;
        bool isVerified;
        bool isActive;
        address l2ContractAddress;
        uint256 assignedChainId;
        ParticipantMetrics metrics;
    }

    struct ParticipantMetrics {
        uint256 totalTransactions;
        uint256 successfulTransactions;
        uint256 totalValue;
        uint256 lastActivityTime;
    }
    
    struct CrossChainTransaction {
        uint256 transactionId;
        uint256 sourceChain;
        uint256 targetChain;
        address initiator;
        bytes32 dataHash;
        TransactionType txType;
        uint256 timestamp;
        bool processed;
        bool verified;
    }

    enum TransactionType {
        ProductTransfer,
        ShipmentUpdate,
        PaymentRelease,
        DisputeSync,
        FLModelUpdate
    }
    
    // --- FL Model Aggregation (Enhanced) ---
    struct FLModel {
        string modelType;
        bytes32 modelHash;
        uint256 trainingRound;
        uint256 participantCount;
        string modelCID;
        uint256 lastUpdated;
        uint256 accuracyScore;
        bool isActive;
        mapping(uint256 => uint256) chainContributions; // chainId => contribution count
    }

    struct FLAggregationMetrics {
        uint256 totalModels;
        uint256 activeChains;
        uint256 avgAccuracy;
        uint256 lastGlobalUpdate;
    }
    
    // --- State Variables ---
    uint256 private _nextTokenId = 1;
    uint256 private _nextTransactionId = 1;
    uint256 private _nextParticipantId = 1;
    
    mapping(uint256 => Product) public products;
    mapping(address => Participant) public participants;
    mapping(uint256 => CrossChainTransaction) public crossChainTransactions;
    mapping(address => uint256[]) public participantProducts;
    mapping(uint256 => address[]) public chainParticipants;
    mapping(string => FLModel) public globalFLModels;
    mapping(address => mapping(string => bytes32)) public participantModelContributions;
    
    // Multi-chain coordination
    mapping(uint256 => address) public chainContracts; // chainId => contract address
    mapping(bytes32 => bool) public processedHashes;
    
    FLAggregationMetrics public flMetrics;

    // Chain IDs for L2 networks
    uint256 public constant MANUFACTURER_CHAIN_ID = 2001;
    uint256 public constant TRANSPORTER_CHAIN_ID = 2002;
    uint256 public constant BUYER_CHAIN_ID = 2003;
    
    // --- Events ---
    event ProductRegistered(
        uint256 indexed tokenId,
        address indexed manufacturer,
        string metadataCID,
        uint256 manufacturerChainId,
        bytes32 manufacturerHash,
        uint256 timestamp
    );
    
    event ProductStatusUpdated(
        uint256 indexed tokenId,
        ProductStatus oldStatus,
        ProductStatus newStatus,
        address updatedBy,
        uint256 timestamp
    );
    
    event ParticipantRegistered(
        address indexed participant,
        string participantType,
        uint256 chainId,
        address l2Contract
    );
    
    event CrossChainTransactionCreated(
        uint256 indexed transactionId,
        uint256 sourceChain,
        uint256 targetChain,
        address indexed initiator,
        TransactionType txType,
        bytes32 dataHash
    );
    
    event CrossChainTransactionProcessed(
        uint256 indexed transactionId,
        bool success,
        string result
    );
    
    event FLModelAggregated(
        string indexed modelType,
        bytes32 modelHash,
        uint256 trainingRound,
        uint256 participantCount,
        string modelCID,
        uint256 accuracyScore
    );
    
    event FLGlobalUpdate(
        uint256 totalModels,
        uint256 activeChains,
        uint256 avgAccuracy,
        uint256 timestamp
    );
    
    event ReputationUpdated(
        address indexed participant,
        uint256 oldScore,
        uint256 newScore,
        string reason
    );

    event ChainContractRegistered(
        uint256 indexed chainId,
        address contractAddress,
        string chainType
    );
    
    // --- Modifiers ---
    modifier onlyVerifiedParticipant() {
        require(participants[msg.sender].isVerified, "Not a verified participant");
        require(participants[msg.sender].isActive, "Participant not active");
        _;
    }
    
    modifier onlyChainContract() {
        bool isChainContract = false;
        for (uint256 i = 1; i <= 3; i++) {
            if (chainContracts[i] == msg.sender) {
                isChainContract = true;
                break;
            }
        }
        require(isChainContract, "Not an authorized chain contract");
        _;
    }
    
    modifier productExists(uint256 tokenId) {
        require(products[tokenId].isActive, "Product does not exist or is inactive");
        _;
    }
    
    constructor(address initialOwner) ERC721("ChainFLIP Enhanced Supply Chain NFT", "CFESC") Ownable(initialOwner) {
        // Initialize enhanced FL models
        _initializeFLModels();
    }

    function _initializeFLModels() internal {
        // Anomaly Detection Model
        FLModel storage anomalyModel = globalFLModels["anomaly_detection"];
        anomalyModel.modelType = "anomaly_detection";
        anomalyModel.modelHash = bytes32(0);
        anomalyModel.trainingRound = 0;
        anomalyModel.participantCount = 0;
        anomalyModel.modelCID = "";
        anomalyModel.lastUpdated = block.timestamp;
        anomalyModel.accuracyScore = 0;
        anomalyModel.isActive = true;
        
        // Counterfeit Detection Model
        FLModel storage counterModel = globalFLModels["counterfeit_detection"];
        counterModel.modelType = "counterfeit_detection";
        counterModel.modelHash = bytes32(0);
        counterModel.trainingRound = 0;
        counterModel.participantCount = 0;
        counterModel.modelCID = "";
        counterModel.lastUpdated = block.timestamp;
        counterModel.accuracyScore = 0;
        counterModel.isActive = true;

        // Quality Prediction Model
        FLModel storage qualityModel = globalFLModels["quality_prediction"];
        qualityModel.modelType = "quality_prediction";
        qualityModel.modelHash = bytes32(0);
        qualityModel.trainingRound = 0;
        qualityModel.participantCount = 0;
        qualityModel.modelCID = "";
        qualityModel.lastUpdated = block.timestamp;
        qualityModel.accuracyScore = 0;
        qualityModel.isActive = true;

        // Route Optimization Model
        FLModel storage routeModel = globalFLModels["route_optimization"];
        routeModel.modelType = "route_optimization";
        routeModel.modelHash = bytes32(0);
        routeModel.trainingRound = 0;
        routeModel.participantCount = 0;
        routeModel.modelCID = "";
        routeModel.lastUpdated = block.timestamp;
        routeModel.accuracyScore = 0;
        routeModel.isActive = true;

        // Fraud Detection Model
        FLModel storage fraudModel = globalFLModels["fraud_detection"];
        fraudModel.modelType = "fraud_detection";
        fraudModel.modelHash = bytes32(0);
        fraudModel.trainingRound = 0;
        fraudModel.participantCount = 0;
        fraudModel.modelCID = "";
        fraudModel.lastUpdated = block.timestamp;
        fraudModel.accuracyScore = 0;
        fraudModel.isActive = true;
        
        flMetrics.totalModels = 5;
        flMetrics.lastGlobalUpdate = block.timestamp;
    }
    
    // --- Enhanced Participant Management ---
    function registerParticipant(
        address participantAddress,
        string memory participantType,
        uint256 chainId,
        address l2ContractAddress
    ) external onlyOwner {
        require(!participants[participantAddress].isActive, "Participant already registered");
        require(chainId >= MANUFACTURER_CHAIN_ID && chainId <= BUYER_CHAIN_ID, "Invalid chain ID");
        
        participants[participantAddress] = Participant({
            participantAddress: participantAddress,
            participantType: participantType,
            registeredAt: block.timestamp,
            reputationScore: 100,
            isVerified: true,
            isActive: true,
            l2ContractAddress: l2ContractAddress,
            assignedChainId: chainId,
            metrics: ParticipantMetrics({
                totalTransactions: 0,
                successfulTransactions: 0,
                totalValue: 0,
                lastActivityTime: block.timestamp
            })
        });
        
        chainParticipants[chainId].push(_nextParticipantId);
        _nextParticipantId++;
        
        emit ParticipantRegistered(participantAddress, participantType, chainId, l2ContractAddress);
    }

    // --- Chain Contract Registration ---
    function registerChainContract(
        uint256 chainId,
        address contractAddress,
        string memory chainType
    ) external onlyOwner {
        require(chainId >= MANUFACTURER_CHAIN_ID && chainId <= BUYER_CHAIN_ID, "Invalid chain ID");
        require(contractAddress != address(0), "Invalid contract address");
        
        chainContracts[chainId] = contractAddress;
        
        emit ChainContractRegistered(chainId, contractAddress, chainType);
    }
    
    // --- Enhanced Product Management ---
    function registerProductFromChain(
        uint256 productTokenId,
        address manufacturer,
        string memory metadataCID,
        uint256 manufacturerChainId,
        bytes32 manufacturerHash
    ) external onlyChainContract whenNotPaused returns (uint256) {
        require(participants[manufacturer].isActive, "Manufacturer not registered");
        
        uint256 hubTokenId = _nextTokenId;
        _nextTokenId++;
        
        products[hubTokenId] = Product({
            tokenId: hubTokenId,
            manufacturer: manufacturer,
            metadataCID: metadataCID,
            createdAt: block.timestamp,
            currentOwner: manufacturer,
            status: ProductStatus.Manufactured,
            isActive: true,
            manufacturerChainId: manufacturerChainId,
            manufacturerHash: manufacturerHash,
            qualityApproved: false
        });
        
        participantProducts[manufacturer].push(hubTokenId);
        
        // Update manufacturer metrics
        participants[manufacturer].metrics.totalTransactions++;
        participants[manufacturer].metrics.lastActivityTime = block.timestamp;
        
        _mint(manufacturer, hubTokenId);
        
        emit ProductRegistered(hubTokenId, manufacturer, metadataCID, manufacturerChainId, manufacturerHash, block.timestamp);
        
        return hubTokenId;
    }

    function updateProductStatus(
        uint256 tokenId,
        ProductStatus newStatus,
        bytes32 verificationHash
    ) external onlyChainContract productExists(tokenId) whenNotPaused {
        require(!processedHashes[verificationHash], "Hash already processed");
        
        Product storage product = products[tokenId];
        ProductStatus oldStatus = product.status;
        product.status = newStatus;
        
        if (newStatus == ProductStatus.QualityApproved) {
            product.qualityApproved = true;
        }
        
        processedHashes[verificationHash] = true;
        
        emit ProductStatusUpdated(tokenId, oldStatus, newStatus, msg.sender, block.timestamp);
    }
    
    // --- Cross-Chain Transaction Management ---
    function createCrossChainTransaction(
        uint256 sourceChain,
        uint256 targetChain,
        bytes32 dataHash,
        TransactionType txType
    ) external onlyChainContract returns (uint256) {
        uint256 transactionId = _nextTransactionId;
        _nextTransactionId++;
        
        crossChainTransactions[transactionId] = CrossChainTransaction({
            transactionId: transactionId,
            sourceChain: sourceChain,
            targetChain: targetChain,
            initiator: msg.sender,
            dataHash: dataHash,
            txType: txType,
            timestamp: block.timestamp,
            processed: false,
            verified: false
        });
        
        emit CrossChainTransactionCreated(transactionId, sourceChain, targetChain, msg.sender, txType, dataHash);
        
        return transactionId;
    }

    function processCrossChainTransaction(
        uint256 transactionId,
        bool success,
        string memory result
    ) external onlyOwner {
        require(crossChainTransactions[transactionId].transactionId != 0, "Transaction does not exist");
        require(!crossChainTransactions[transactionId].processed, "Transaction already processed");
        
        crossChainTransactions[transactionId].processed = true;
        crossChainTransactions[transactionId].verified = success;
        
        emit CrossChainTransactionProcessed(transactionId, success, result);
    }
    
    // --- Enhanced FL Model Aggregation ---
    function aggregateEnhancedFLModel(
        string memory modelType,
        bytes32 modelHash,
        string memory modelCID,
        address[] memory contributors,
        uint256[] memory chainIds,
        uint256 accuracyScore
    ) external onlyOwner {
        require(_isValidModelType(modelType), "Invalid model type");
        require(contributors.length == chainIds.length, "Contributors and chains length mismatch");
        require(accuracyScore <= 100, "Accuracy score must be 0-100");
        
        FLModel storage model = globalFLModels[modelType];
        model.modelHash = modelHash;
        model.trainingRound++;
        model.participantCount = contributors.length;
        model.modelCID = modelCID;
        model.lastUpdated = block.timestamp;
        model.accuracyScore = accuracyScore;
        
        // Record chain contributions
        for (uint256 i = 0; i < chainIds.length; i++) {
            model.chainContributions[chainIds[i]]++;
        }
        
        // Record contributor participation
        for (uint256 i = 0; i < contributors.length; i++) {
            participantModelContributions[contributors[i]][modelType] = modelHash;
            
            // Reward participation with reputation increase
            _updateReputation(contributors[i], 3, "FL model contribution");
        }
        
        // Update global FL metrics
        _updateGlobalFLMetrics();
        
        emit FLModelAggregated(modelType, modelHash, model.trainingRound, contributors.length, modelCID, accuracyScore);
    }

    function _updateGlobalFLMetrics() internal {
        uint256 totalAccuracy = 0;
        uint256 activeModelCount = 0;
        
        string[5] memory modelTypes = ["anomaly_detection", "counterfeit_detection", "quality_prediction", "route_optimization", "fraud_detection"];
        
        for (uint256 i = 0; i < 5; i++) {
            FLModel storage model = globalFLModels[modelTypes[i]];
            if (model.isActive) {
                totalAccuracy += model.accuracyScore;
                activeModelCount++;
            }
        }
        
        if (activeModelCount > 0) {
            flMetrics.avgAccuracy = totalAccuracy / activeModelCount;
        }
        
        flMetrics.activeChains = _countActiveChains();
        flMetrics.lastGlobalUpdate = block.timestamp;
        
        emit FLGlobalUpdate(flMetrics.totalModels, flMetrics.activeChains, flMetrics.avgAccuracy, block.timestamp);
    }

    function _countActiveChains() internal view returns (uint256) {
        uint256 activeChains = 0;
        for (uint256 i = MANUFACTURER_CHAIN_ID; i <= BUYER_CHAIN_ID; i++) {
            if (chainContracts[i] != address(0)) {
                activeChains++;
            }
        }
        return activeChains;
    }

    function _isValidModelType(string memory modelType) internal pure returns (bool) {
        bytes32 modelHash = keccak256(abi.encodePacked(modelType));
        return (
            modelHash == keccak256(abi.encodePacked("anomaly_detection")) ||
            modelHash == keccak256(abi.encodePacked("counterfeit_detection")) ||
            modelHash == keccak256(abi.encodePacked("quality_prediction")) ||
            modelHash == keccak256(abi.encodePacked("route_optimization")) ||
            modelHash == keccak256(abi.encodePacked("fraud_detection"))
        );
    }
    
    // --- Enhanced Reputation Management ---
    function updateParticipantReputation(
        address participant,
        int256 scoreChange,
        string memory reason
    ) external onlyChainContract {
        _updateReputation(participant, scoreChange, reason);
    }

    function _updateReputation(address participant, int256 scoreChange, string memory reason) internal {
        require(participants[participant].isActive, "Participant not active");
        
        uint256 oldScore = participants[participant].reputationScore;
        
        if (scoreChange > 0) {
            participants[participant].reputationScore += uint256(scoreChange);
            if (participants[participant].reputationScore > 1000) {
                participants[participant].reputationScore = 1000; // Cap at 1000
            }
        } else {
            uint256 decrease = uint256(-scoreChange);
            if (decrease >= participants[participant].reputationScore) {
                participants[participant].reputationScore = 0;
            } else {
                participants[participant].reputationScore -= decrease;
            }
        }
        
        emit ReputationUpdated(participant, oldScore, participants[participant].reputationScore, reason);
    }
    
    // --- View Functions ---
    function getProduct(uint256 tokenId) external view returns (Product memory) {
        require(products[tokenId].isActive, "Product does not exist");
        return products[tokenId];
    }
    
    function getParticipant(address participantAddress) external view returns (Participant memory) {
        return participants[participantAddress];
    }
    
    function getFLModel(string memory modelType) external view returns (
        string memory, bytes32, uint256, uint256, string memory, uint256, uint256, bool
    ) {
        FLModel storage model = globalFLModels[modelType];
        return (
            model.modelType,
            model.modelHash,
            model.trainingRound,
            model.participantCount,
            model.modelCID,
            model.lastUpdated,
            model.accuracyScore,
            model.isActive
        );
    }

    function getFLModelChainContribution(string memory modelType, uint256 chainId) external view returns (uint256) {
        return globalFLModels[modelType].chainContributions[chainId];
    }
    
    function getParticipantProducts(address participant) external view returns (uint256[] memory) {
        return participantProducts[participant];
    }
    
    function getCrossChainTransaction(uint256 transactionId) external view returns (CrossChainTransaction memory) {
        return crossChainTransactions[transactionId];
    }

    function getChainContract(uint256 chainId) external view returns (address) {
        return chainContracts[chainId];
    }

    function getFLAggregationMetrics() external view returns (FLAggregationMetrics memory) {
        return flMetrics;
    }
    
    // --- Admin Functions ---
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
    
    function deactivateProduct(uint256 tokenId) external onlyOwner {
        products[tokenId].isActive = false;
    }
    
    function deactivateParticipant(address participant) external onlyOwner {
        participants[participant].isActive = false;
    }

    function updateFLModelStatus(string memory modelType, bool isActive) external onlyOwner {
        require(_isValidModelType(modelType), "Invalid model type");
        globalFLModels[modelType].isActive = isActive;
    }

    function emergencyWithdraw() external onlyOwner {
        (bool success, ) = payable(owner()).call{value: address(this).balance}("");
        require(success, "Withdrawal failed");
    }

    // --- Funding ---
    receive() external payable {}
}