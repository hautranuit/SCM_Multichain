// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title PolygonPoSHub
 * @dev Central hub contract on Polygon PoS for ChainFLIP multi-chain supply chain management
 */
contract PolygonPoSHub is ERC721, Ownable, ReentrancyGuard, Pausable {
    
    // Structs
    struct Product {
        uint256 tokenId;
        address manufacturer;
        string metadataCID;
        uint256 createdAt;
        address currentOwner;
        string status; // "manufactured", "in_transit", "delivered", "sold"
        bool isActive;
    }
    
    struct Participant {
        address participantAddress;
        string participantType; // "manufacturer", "distributor", "retailer", etc.
        uint256 registeredAt;
        uint256 reputationScore;
        bool isVerified;
        bool isActive;
        address l2ContractAddress; // Associated L2 contract address
    }
    
    struct CrossChainMessage {
        uint256 messageId;
        uint256 sourceChain;
        uint256 targetChain;
        address sender;
        bytes messageData;
        uint256 timestamp;
        bool processed;
    }
    
    // State variables
    uint256 private _nextTokenId = 1;
    uint256 private _nextMessageId = 1;
    uint256 private _nextParticipantId = 1;
    
    mapping(uint256 => Product) public products;
    mapping(address => Participant) public participants;
    mapping(uint256 => CrossChainMessage) public crossChainMessages;
    mapping(address => uint256[]) public participantProducts; // participant => tokenIds
    mapping(uint256 => uint256[]) public chainParticipants; // chainId => participantIds
    
    // FL Model aggregation
    struct FLModel {
        string modelType; // "anomaly_detection", "counterfeit_detection"
        bytes32 modelHash;
        uint256 trainingRound;
        uint256 participantCount;
        string modelCID; // IPFS CID of aggregated model
        uint256 lastUpdated;
    }
    
    mapping(string => FLModel) public globalFLModels;
    mapping(address => mapping(string => bytes32)) public participantModelContributions;
    
    // Events
    event ProductMinted(
        uint256 indexed tokenId,
        address indexed manufacturer,
        string metadataCID,
        uint256 timestamp
    );
    
    event ProductTransferred(
        uint256 indexed tokenId,
        address indexed from,
        address indexed to,
        uint256 timestamp
    );
    
    event ParticipantRegistered(
        address indexed participant,
        string participantType,
        uint256 chainId,
        address l2Contract
    );
    
    event CrossChainMessageSent(
        uint256 indexed messageId,
        uint256 sourceChain,
        uint256 targetChain,
        address indexed sender,
        bytes messageData
    );
    
    event FLModelAggregated(
        string indexed modelType,
        bytes32 modelHash,
        uint256 trainingRound,
        uint256 participantCount,
        string modelCID
    );
    
    event ReputationUpdated(
        address indexed participant,
        uint256 oldScore,
        uint256 newScore,
        string reason
    );
    
    // Modifiers
    modifier onlyVerifiedParticipant() {
        require(participants[msg.sender].isVerified, "Not a verified participant");
        require(participants[msg.sender].isActive, "Participant not active");
        _;
    }
    
    modifier productExists(uint256 tokenId) {
        require(products[tokenId].isActive, "Product does not exist or is inactive");
        _;
    }
    
    constructor(address initialOwner) ERC721("ChainFLIP Supply Chain NFT", "CFSC") Ownable(initialOwner) {
        // Initialize default FL models
        globalFLModels["anomaly_detection"] = FLModel({
            modelType: "anomaly_detection",
            modelHash: bytes32(0),
            trainingRound: 0,
            participantCount: 0,
            modelCID: "",
            lastUpdated: block.timestamp
        });
        
        globalFLModels["counterfeit_detection"] = FLModel({
            modelType: "counterfeit_detection",
            modelHash: bytes32(0),
            trainingRound: 0,
            participantCount: 0,
            modelCID: "",
            lastUpdated: block.timestamp
        });
    }
    
    /**
     * @dev Register a new participant in the multi-chain system
     */
    function registerParticipant(
        address participantAddress,
        string memory participantType,
        uint256 chainId,
        address l2ContractAddress
    ) external onlyOwner {
        require(!participants[participantAddress].isActive, "Participant already registered");
        
        participants[participantAddress] = Participant({
            participantAddress: participantAddress,
            participantType: participantType,
            registeredAt: block.timestamp,
            reputationScore: 100, // Starting reputation
            isVerified: true,
            isActive: true,
            l2ContractAddress: l2ContractAddress
        });
        
        chainParticipants[chainId].push(_nextParticipantId);
        _nextParticipantId++;
        
        emit ParticipantRegistered(participantAddress, participantType, chainId, l2ContractAddress);
    }
    
    /**
     * @dev Mint a new product NFT
     */
    function mintProduct(
        address manufacturer,
        string memory metadataCID
    ) external onlyVerifiedParticipant whenNotPaused returns (uint256) {
        require(
            keccak256(abi.encodePacked(participants[manufacturer].participantType)) == 
            keccak256(abi.encodePacked("manufacturer")),
            "Only manufacturers can mint products"
        );
        
        uint256 tokenId = _nextTokenId;
        _nextTokenId++;
        
        products[tokenId] = Product({
            tokenId: tokenId,
            manufacturer: manufacturer,
            metadataCID: metadataCID,
            createdAt: block.timestamp,
            currentOwner: manufacturer,
            status: "manufactured",
            isActive: true
        });
        
        participantProducts[manufacturer].push(tokenId);
        
        _mint(manufacturer, tokenId);
        
        emit ProductMinted(tokenId, manufacturer, metadataCID, block.timestamp);
        
        return tokenId;
    }
    
    /**
     * @dev Transfer product ownership
     */
    function transferProduct(
        uint256 tokenId,
        address to,
        string memory newStatus
    ) external productExists(tokenId) whenNotPaused {
        require(ownerOf(tokenId) == msg.sender, "Not the owner of this product");
        require(participants[to].isActive, "Recipient is not an active participant");
        
        address from = msg.sender;
        
        // Update product ownership and status
        products[tokenId].currentOwner = to;
        products[tokenId].status = newStatus;
        
        // Update participant product lists
        _removeFromParticipantProducts(from, tokenId);
        participantProducts[to].push(tokenId);
        
        // Transfer NFT
        _transfer(from, to, tokenId);
        
        emit ProductTransferred(tokenId, from, to, block.timestamp);
    }
    
    /**
     * @dev Send cross-chain message to L2 CDK
     */
    function sendCrossChainMessage(
        uint256 targetChain,
        bytes memory messageData
    ) external onlyVerifiedParticipant returns (uint256) {
        uint256 messageId = _nextMessageId;
        _nextMessageId++;
        
        crossChainMessages[messageId] = CrossChainMessage({
            messageId: messageId,
            sourceChain: block.chainid,
            targetChain: targetChain,
            sender: msg.sender,
            messageData: messageData,
            timestamp: block.timestamp,
            processed: false
        });
        
        emit CrossChainMessageSent(messageId, block.chainid, targetChain, msg.sender, messageData);
        
        return messageId;
    }
    
    /**
     * @dev Aggregate FL model contributions
     */
    function aggregateFLModel(
        string memory modelType,
        bytes32 modelHash,
        string memory modelCID,
        address[] memory contributors
    ) external onlyOwner {
        require(
            keccak256(abi.encodePacked(modelType)) == keccak256(abi.encodePacked("anomaly_detection")) ||
            keccak256(abi.encodePacked(modelType)) == keccak256(abi.encodePacked("counterfeit_detection")),
            "Invalid model type"
        );
        
        FLModel storage model = globalFLModels[modelType];
        model.modelHash = modelHash;
        model.trainingRound++;
        model.participantCount = contributors.length;
        model.modelCID = modelCID;
        model.lastUpdated = block.timestamp;
        
        // Record contributions
        for (uint256 i = 0; i < contributors.length; i++) {
            participantModelContributions[contributors[i]][modelType] = modelHash;
            
            // Reward participation with reputation increase
            _updateReputation(contributors[i], 5, "FL model contribution");
        }
        
        emit FLModelAggregated(modelType, modelHash, model.trainingRound, contributors.length, modelCID);
    }
    
    /**
     * @dev Update participant reputation
     */
    function updateParticipantReputation(
        address participant,
        int256 scoreChange,
        string memory reason
    ) external onlyOwner {
        _updateReputation(participant, scoreChange, reason);
    }
    
    /**
     * @dev Get product information
     */
    function getProduct(uint256 tokenId) external view returns (Product memory) {
        require(products[tokenId].isActive, "Product does not exist");
        return products[tokenId];
    }
    
    /**
     * @dev Get participant information
     */
    function getParticipant(address participantAddress) external view returns (Participant memory) {
        return participants[participantAddress];
    }
    
    /**
     * @dev Get global FL model information
     */
    function getFLModel(string memory modelType) external view returns (FLModel memory) {
        return globalFLModels[modelType];
    }
    
    /**
     * @dev Get products owned by participant
     */
    function getParticipantProducts(address participant) external view returns (uint256[] memory) {
        return participantProducts[participant];
    }
    
    /**
     * @dev Get cross-chain message
     */
    function getCrossChainMessage(uint256 messageId) external view returns (CrossChainMessage memory) {
        return crossChainMessages[messageId];
    }
    
    // Internal functions
    function _updateReputation(address participant, int256 scoreChange, string memory reason) internal {
        require(participants[participant].isActive, "Participant not active");
        
        uint256 oldScore = participants[participant].reputationScore;
        
        if (scoreChange > 0) {
            participants[participant].reputationScore += uint256(scoreChange);
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
    
    function _removeFromParticipantProducts(address participant, uint256 tokenId) internal {
        uint256[] storage products_list = participantProducts[participant];
        for (uint256 i = 0; i < products_list.length; i++) {
            if (products_list[i] == tokenId) {
                products_list[i] = products_list[products_list.length - 1];
                products_list.pop();
                break;
            }
        }
    }
    
    // Admin functions
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
}
