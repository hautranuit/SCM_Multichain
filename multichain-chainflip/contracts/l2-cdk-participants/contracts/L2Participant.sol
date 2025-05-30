// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title L2Participant
 * @dev L2 CDK contract for individual participant operations in ChainFLIP
 * Handles high-frequency operations, local business logic, and participant-specific data
 */
contract L2Participant is Ownable, ReentrancyGuard, Pausable {
    
    // Structs
    struct TransportLog {
        uint256 logId;
        uint256 productId; // Token ID from PoS Hub
        address fromParticipant;
        address toParticipant;
        string ipfsCID; // Transport details stored in IPFS
        uint256 timestamp;
        string status; // "initiated", "in_progress", "completed", "failed"
        bool verified;
    }
    
    struct QRCodeData {
        uint256 qrId;
        uint256 productId;
        string encryptedDataCID; // IPFS CID of encrypted QR data
        bytes32 qrHash;
        uint256 createdAt;
        uint256 expiresAt;
        bool isActive;
        address authorizedScanner; // Who can decrypt this QR
    }
    
    struct LocalFLModel {
        string modelType; // "anomaly_detection", "counterfeit_detection"
        bytes32 modelHash;
        string modelCID; // IPFS CID of local model
        uint256 trainingSamples;
        uint256 trainingTimestamp;
        bool readyForAggregation;
    }
    
    struct AnomalyDetection {
        uint256 detectionId;
        uint256 productId;
        string anomalyType; // "transport", "temperature", "location", etc.
        uint256 severity; // 1-10 scale
        string evidenceCID; // IPFS CID of evidence data
        uint256 detectedAt;
        bool reported; // Reported to PoS Hub
    }
    
    // State variables
    address public participantAddress;
    string public participantType;
    address public posHubContract; // Polygon PoS Hub contract address
    uint256 public chainId;
    
    uint256 private _nextLogId = 1;
    uint256 private _nextQRId = 1;
    uint256 private _nextDetectionId = 1;
    
    mapping(uint256 => TransportLog) public transportLogs;
    mapping(uint256 => QRCodeData) public qrCodes;
    mapping(string => LocalFLModel) public localFLModels;
    mapping(uint256 => AnomalyDetection) public anomalyDetections;
    
    mapping(uint256 => uint256[]) public productTransportLogs; // productId => logIds
    mapping(uint256 => uint256[]) public productQRCodes; // productId => qrIds
    mapping(address => uint256[]) public participantInteractions; // participant => logIds
    
    // Events
    event TransportLogCreated(
        uint256 indexed logId,
        uint256 indexed productId,
        address indexed fromParticipant,
        address toParticipant,
        string ipfsCID
    );
    
    event QRCodeGenerated(
        uint256 indexed qrId,
        uint256 indexed productId,
        bytes32 qrHash,
        address authorizedScanner
    );
    
    event QRCodeScanned(
        uint256 indexed qrId,
        address indexed scanner,
        uint256 timestamp
    );
    
    event LocalFLModelTrained(
        string indexed modelType,
        bytes32 modelHash,
        uint256 trainingSamples,
        string modelCID
    );
    
    event AnomalyDetected(
        uint256 indexed detectionId,
        uint256 indexed productId,
        string anomalyType,
        uint256 severity
    );
    
    event CrossChainDataSent(
        address indexed posHub,
        bytes32 dataHash,
        string dataType
    );
    
    // Modifiers
    modifier onlyParticipant() {
        require(msg.sender == participantAddress, "Only participant can call this function");
        _;
    }
    
    modifier onlyAuthorizedScanner(uint256 qrId) {
        require(
            qrCodes[qrId].authorizedScanner == msg.sender || 
            qrCodes[qrId].authorizedScanner == address(0),
            "Not authorized to scan this QR code"
        );
        require(qrCodes[qrId].isActive, "QR code is not active");
        require(block.timestamp <= qrCodes[qrId].expiresAt, "QR code has expired");
        _;
    }
    
    constructor(
        address _participantAddress,
        string memory _participantType,
        address _posHubContract,
        uint256 _chainId,
        address initialOwner
    ) Ownable(initialOwner) {
        participantAddress = _participantAddress;
        participantType = _participantType;
        posHubContract = _posHubContract;
        chainId = _chainId;
    }
    
    /**
     * @dev Create a new transport log entry
     */
    function createTransportLog(
        uint256 productId,
        address fromParticipant,
        address toParticipant,
        string memory ipfsCID
    ) external onlyParticipant whenNotPaused returns (uint256) {
        require(fromParticipant != toParticipant, "Cannot transfer to same participant");
        
        uint256 logId = _nextLogId;
        _nextLogId++;
        
        transportLogs[logId] = TransportLog({
            logId: logId,
            productId: productId,
            fromParticipant: fromParticipant,
            toParticipant: toParticipant,
            ipfsCID: ipfsCID,
            timestamp: block.timestamp,
            status: "initiated",
            verified: false
        });
        
        productTransportLogs[productId].push(logId);
        participantInteractions[fromParticipant].push(logId);
        participantInteractions[toParticipant].push(logId);
        
        emit TransportLogCreated(logId, productId, fromParticipant, toParticipant, ipfsCID);
        
        return logId;
    }
    
    /**
     * @dev Update transport log status
     */
    function updateTransportLogStatus(
        uint256 logId,
        string memory newStatus,
        bool verified
    ) external onlyParticipant {
        require(logId < _nextLogId, "Transport log does not exist");
        
        TransportLog storage log = transportLogs[logId];
        log.status = newStatus;
        log.verified = verified;
        
        // If transport completed, trigger anomaly detection
        if (keccak256(abi.encodePacked(newStatus)) == keccak256(abi.encodePacked("completed"))) {
            _performAnomalyDetection(log.productId, logId);
        }
    }
    
    /**
     * @dev Generate dynamic QR code for product
     */
    function generateQRCode(
        uint256 productId,
        string memory encryptedDataCID,
        bytes32 qrHash,
        uint256 validityDuration,
        address authorizedScanner
    ) external onlyParticipant whenNotPaused returns (uint256) {
        uint256 qrId = _nextQRId;
        _nextQRId++;
        
        qrCodes[qrId] = QRCodeData({
            qrId: qrId,
            productId: productId,
            encryptedDataCID: encryptedDataCID,
            qrHash: qrHash,
            createdAt: block.timestamp,
            expiresAt: block.timestamp + validityDuration,
            isActive: true,
            authorizedScanner: authorizedScanner
        });
        
        productQRCodes[productId].push(qrId);
        
        emit QRCodeGenerated(qrId, productId, qrHash, authorizedScanner);
        
        return qrId;
    }
    
    /**
     * @dev Scan QR code (for authorized scanners)
     */
    function scanQRCode(uint256 qrId) external onlyAuthorizedScanner(qrId) returns (string memory) {
        QRCodeData storage qr = qrCodes[qrId];
        
        emit QRCodeScanned(qrId, msg.sender, block.timestamp);
        
        return qr.encryptedDataCID;
    }
    
    /**
     * @dev Train local FL model
     */
    function trainLocalFLModel(
        string memory modelType,
        bytes32 modelHash,
        string memory modelCID,
        uint256 trainingSamples
    ) external onlyParticipant whenNotPaused {
        require(
            keccak256(abi.encodePacked(modelType)) == keccak256(abi.encodePacked("anomaly_detection")) ||
            keccak256(abi.encodePacked(modelType)) == keccak256(abi.encodePacked("counterfeit_detection")),
            "Invalid model type"
        );
        
        localFLModels[modelType] = LocalFLModel({
            modelType: modelType,
            modelHash: modelHash,
            modelCID: modelCID,
            trainingSamples: trainingSamples,
            trainingTimestamp: block.timestamp,
            readyForAggregation: true
        });
        
        emit LocalFLModelTrained(modelType, modelHash, trainingSamples, modelCID);
    }
    
    /**
     * @dev Report local FL model to PoS Hub for aggregation
     */
    function reportFLModelToHub(string memory modelType) external onlyParticipant {
        LocalFLModel storage model = localFLModels[modelType];
        require(model.readyForAggregation, "Model not ready for aggregation");
        
        // Prepare data for cross-chain communication
        bytes memory modelData = abi.encode(
            modelType,
            model.modelHash,
            model.modelCID,
            model.trainingSamples,
            participantAddress
        );
        
        // Mark model as reported
        model.readyForAggregation = false;
        
        emit CrossChainDataSent(posHubContract, model.modelHash, "fl_model");
        
        // Note: Actual cross-chain communication would be implemented here
        // This would use FxPortal or similar bridge mechanism
    }
    
    /**
     * @dev Record anomaly detection (internal)
     */
    function recordAnomalyDetection(
        uint256 productId,
        string memory anomalyType,
        uint256 severity,
        string memory evidenceCID
    ) internal returns (uint256) {
        uint256 detectionId = _nextDetectionId;
        _nextDetectionId++;
        
        anomalyDetections[detectionId] = AnomalyDetection({
            detectionId: detectionId,
            productId: productId,
            anomalyType: anomalyType,
            severity: severity,
            evidenceCID: evidenceCID,
            detectedAt: block.timestamp,
            reported: false
        });
        
        emit AnomalyDetected(detectionId, productId, anomalyType, severity);
        
        // If high severity, automatically report to PoS Hub
        if (severity >= 7) {
            _reportAnomalyToHub(detectionId);
        }
        
        return detectionId;
    }
    
    /**
     * @dev Record anomaly detection (external wrapper)
     */
    function recordAnomalyDetectionExternal(
        uint256 productId,
        string memory anomalyType,
        uint256 severity,
        string memory evidenceCID
    ) external onlyParticipant returns (uint256) {
        return recordAnomalyDetection(productId, anomalyType, severity, evidenceCID);
    }
    
    /**
     * @dev Get transport logs for a product
     */
    function getProductTransportLogs(uint256 productId) external view returns (uint256[] memory) {
        return productTransportLogs[productId];
    }
    
    /**
     * @dev Get QR codes for a product
     */
    function getProductQRCodes(uint256 productId) external view returns (uint256[] memory) {
        return productQRCodes[productId];
    }
    
    /**
     * @dev Get local FL model
     */
    function getLocalFLModel(string memory modelType) external view returns (LocalFLModel memory) {
        return localFLModels[modelType];
    }
    
    /**
     * @dev Get participant interactions
     */
    function getParticipantInteractions(address participant) external view returns (uint256[] memory) {
        return participantInteractions[participant];
    }
    
    /**
     * @dev Get anomaly detection details
     */
    function getAnomalyDetection(uint256 detectionId) external view returns (AnomalyDetection memory) {
        return anomalyDetections[detectionId];
    }
    
    // Internal functions
    function _performAnomalyDetection(uint256 productId, uint256 logId) internal {
        // Simplified anomaly detection logic
        // In practice, this would use the trained FL models
        
        TransportLog storage log = transportLogs[logId];
        uint256 transportDuration = block.timestamp - log.timestamp;
        
        // Example: Flag unusually long transport times
        if (transportDuration > 7 days) {
            recordAnomalyDetection(
                productId,
                "transport_delay",
                5, // Medium severity
                log.ipfsCID
            );
        }
    }
    
    function _reportAnomalyToHub(uint256 detectionId) internal {
        AnomalyDetection storage detection = anomalyDetections[detectionId];
        detection.reported = true;
        
        // Prepare data for cross-chain communication
        bytes memory anomalyData = abi.encode(
            detection.productId,
            detection.anomalyType,
            detection.severity,
            detection.evidenceCID,
            participantAddress
        );
        
        emit CrossChainDataSent(posHubContract, keccak256(anomalyData), "anomaly_report");
    }
    
    // Admin functions
    function updatePosHubContract(address newPosHub) external onlyOwner {
        posHubContract = newPosHub;
    }
    
    function deactivateQRCode(uint256 qrId) external onlyOwner {
        qrCodes[qrId].isActive = false;
    }
    
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
    
    // Emergency functions
    function emergencyWithdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}
