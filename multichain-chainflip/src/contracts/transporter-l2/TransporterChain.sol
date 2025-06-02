// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title TransporterChain
 * @dev Specialized L2 contract for transporters implementing:
 * - Algorithm 3: Supply Chain Consensus Algorithm
 * - Algorithm 1: Payment Release and Incentive Mechanism (Transport)
 * - Algorithm 2: Dispute Resolution and Voting Mechanism (Transport disputes)
 */
contract TransporterChain is AccessControl, ReentrancyGuard, Pausable {
    
    // --- Core Data Structures ---
    struct Shipment {
        uint256 shipmentId;
        uint256 productTokenId;
        bytes32 productHash; // From manufacturer chain
        address shipper;
        address transporter;
        address destination;
        string startLocation;
        string endLocation;
        uint256 distance;
        uint256 estimatedDeliveryTime;
        uint256 actualDeliveryTime;
        ShipmentStatus status;
        uint256 transportFee;
        uint256 collateral;
        bool incentiveEligible;
        bytes32 crossChainHash;
    }

    enum ShipmentStatus {
        Created,
        InTransit,
        Delivered,
        Delayed,
        Disputed,
        Completed
    }

    struct TransportNode {
        address nodeAddress;
        string nodeType; // "primary", "secondary"
        uint256 reputation;
        uint256 totalShipments;
        uint256 successRate;
        uint256 averageDeliveryTime;
        bool isActive;
        string location;
    }

    struct ConsensusVote {
        uint256 shipmentId;
        address voter;
        bool approve;
        string reason;
        uint256 timestamp;
    }

    struct TransportIncentive {
        address transporter;
        uint256 totalDistance;
        uint256 onTimeDeliveries;
        uint256 totalDeliveries;
        uint256 incentivePool;
        uint256 lastClaim;
    }

    // --- FL Integration for Transport ---
    struct FLTransportMetrics {
        uint256 routeOptimizationScore;
        uint256 delayPredictionAccuracy;
        uint256 anomalyScore;
        uint256 lastModelUpdate;
    }

    // --- State Variables ---
    uint256 private _nextShipmentId = 1;
    uint256 private _nextVoteId = 1;
    
    mapping(uint256 => Shipment) public shipments;
    mapping(address => TransportNode) public transportNodes;
    mapping(uint256 => ConsensusVote[]) public shipmentVotes;
    mapping(address => TransportIncentive) public transporterIncentives;
    mapping(address => FLTransportMetrics) public transporterFLMetrics;
    mapping(bytes32 => bool) public processedCrossChainActions;
    
    address[] public allTransportNodes;
    uint256 public consensusThreshold = 66; // 66% for consensus
    uint256 public hubChainId = 80002;
    address public hubContract;

    // --- Roles ---
    bytes32 public constant TRANSPORTER_ROLE = keccak256("TRANSPORTER_ROLE");
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");
    bytes32 public constant HUB_COORDINATOR_ROLE = keccak256("HUB_COORDINATOR_ROLE");

    // --- Events ---
    event ShipmentCreated(
        uint256 indexed shipmentId,
        uint256 indexed productTokenId,
        address indexed transporter,
        string startLocation,
        string endLocation,
        uint256 distance,
        uint256 timestamp
    );
    
    event ShipmentStatusUpdated(
        uint256 indexed shipmentId,
        ShipmentStatus oldStatus,
        ShipmentStatus newStatus,
        address updatedBy,
        uint256 timestamp
    );
    
    event ConsensusVoteSubmitted(
        uint256 indexed shipmentId,
        address indexed voter,
        bool approve,
        string reason,
        uint256 timestamp
    );
    
    event TransportIncentivePaid(
        address indexed transporter,
        uint256 amount,
        uint256 performanceScore,
        uint256 timestamp
    );
    
    event RouteOptimized(
        uint256 indexed shipmentId,
        string newRoute,
        uint256 estimatedSavings,
        uint256 timestamp
    );
    
    event FLRouteAnomalyDetected(
        address indexed transporter,
        uint256 shipmentId,
        uint256 anomalyScore,
        string reason,
        uint256 timestamp
    );

    constructor(
        address initialAdmin,
        address _hubContract
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(TRANSPORTER_ROLE, initialAdmin);
        _grantRole(VALIDATOR_ROLE, initialAdmin);
        _grantRole(HUB_COORDINATOR_ROLE, initialAdmin);
        hubContract = _hubContract;
    }

    // --- Node Management ---
    function registerTransportNode(
        address nodeAddress,
        string memory nodeType,
        string memory location
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(!transportNodes[nodeAddress].isActive, "Node already registered");
        
        transportNodes[nodeAddress] = TransportNode({
            nodeAddress: nodeAddress,
            nodeType: nodeType,
            reputation: 100, // Starting reputation
            totalShipments: 0,
            successRate: 0,
            averageDeliveryTime: 0,
            isActive: true,
            location: location
        });
        
        allTransportNodes.push(nodeAddress);
        _grantRole(TRANSPORTER_ROLE, nodeAddress);
    }

    // --- Algorithm 3: Supply Chain Consensus Algorithm ---
    function createShipment(
        uint256 productTokenId,
        bytes32 productHash,
        address destination,
        string memory startLocation,
        string memory endLocation,
        uint256 distance,
        uint256 estimatedDeliveryTime
    ) external onlyRole(TRANSPORTER_ROLE) whenNotPaused returns (uint256) {
        require(transportNodes[msg.sender].isActive, "Transporter not registered");
        
        uint256 shipmentId = _nextShipmentId++;
        
        bytes32 crossChainHash = keccak256(abi.encodePacked(
            shipmentId,
            productTokenId,
            productHash,
            msg.sender,
            block.chainid,
            block.timestamp
        ));

        shipments[shipmentId] = Shipment({
            shipmentId: shipmentId,
            productTokenId: productTokenId,
            productHash: productHash,
            shipper: msg.sender,
            transporter: msg.sender,
            destination: destination,
            startLocation: startLocation,
            endLocation: endLocation,
            distance: distance,
            estimatedDeliveryTime: estimatedDeliveryTime,
            actualDeliveryTime: 0,
            status: ShipmentStatus.Created,
            transportFee: calculateTransportFee(distance),
            collateral: calculateCollateral(distance),
            incentiveEligible: true,
            crossChainHash: crossChainHash
        });

        emit ShipmentCreated(shipmentId, productTokenId, msg.sender, startLocation, endLocation, distance, block.timestamp);
        return shipmentId;
    }

    function submitConsensusVote(
        uint256 shipmentId,
        bool approve,
        string memory reason
    ) external onlyRole(VALIDATOR_ROLE) whenNotPaused {
        require(shipments[shipmentId].shipmentId != 0, "Shipment does not exist");
        require(shipments[shipmentId].status == ShipmentStatus.Created, "Shipment not in voting phase");
        
        // Check if already voted
        ConsensusVote[] storage votes = shipmentVotes[shipmentId];
        for (uint i = 0; i < votes.length; i++) {
            require(votes[i].voter != msg.sender, "Already voted on this shipment");
        }

        votes.push(ConsensusVote({
            shipmentId: shipmentId,
            voter: msg.sender,
            approve: approve,
            reason: reason,
            timestamp: block.timestamp
        }));

        emit ConsensusVoteSubmitted(shipmentId, msg.sender, approve, reason, block.timestamp);
        
        // Check if consensus reached
        _checkConsensus(shipmentId);
    }

    function _checkConsensus(uint256 shipmentId) internal {
        ConsensusVote[] storage votes = shipmentVotes[shipmentId];
        require(votes.length >= 3, "Need minimum 3 votes"); // Minimum validator requirement
        
        uint256 approveCount = 0;
        for (uint i = 0; i < votes.length; i++) {
            if (votes[i].approve) {
                approveCount++;
            }
        }
        
        uint256 approvalPercentage = (approveCount * 100) / votes.length;
        
        if (approvalPercentage >= consensusThreshold) {
            _updateShipmentStatus(shipmentId, ShipmentStatus.InTransit);
            
            // Update transporter FL metrics for approved shipment
            address transporter = shipments[shipmentId].transporter;
            _updateTransporterFLMetrics(transporter, true);
        } else {
            _updateShipmentStatus(shipmentId, ShipmentStatus.Disputed);
            
            // FL anomaly detection for rejected shipment
            address transporter = shipments[shipmentId].transporter;
            _updateTransporterFLMetrics(transporter, false);
        }
    }

    function _updateShipmentStatus(uint256 shipmentId, ShipmentStatus newStatus) internal {
        ShipmentStatus oldStatus = shipments[shipmentId].status;
        shipments[shipmentId].status = newStatus;
        
        emit ShipmentStatusUpdated(shipmentId, oldStatus, newStatus, msg.sender, block.timestamp);
    }

    // --- Algorithm 1: Transport Incentive Mechanism ---
    function calculateTransportFee(uint256 distance) public pure returns (uint256) {
        // Base fee: 0.0001 ETH per km + fixed cost
        return (distance * 0.0001 ether) + 0.01 ether;
    }

    function calculateCollateral(uint256 distance) public pure returns (uint256) {
        // Collateral: 20% of transport fee
        return calculateTransportFee(distance) / 5;
    }

    function markDelivered(uint256 shipmentId) external onlyRole(TRANSPORTER_ROLE) whenNotPaused {
        require(shipments[shipmentId].transporter == msg.sender, "Not the assigned transporter");
        require(shipments[shipmentId].status == ShipmentStatus.InTransit, "Shipment not in transit");
        
        Shipment storage shipment = shipments[shipmentId];
        shipment.actualDeliveryTime = block.timestamp;
        
        // Determine if delivery was on time
        bool onTime = block.timestamp <= shipment.estimatedDeliveryTime;
        
        if (onTime) {
            _updateShipmentStatus(shipmentId, ShipmentStatus.Delivered);
            
            // Update transporter incentive metrics
            TransportIncentive storage incentive = transporterIncentives[msg.sender];
            incentive.transporter = msg.sender;
            incentive.totalDistance += shipment.distance;
            incentive.onTimeDeliveries++;
            incentive.totalDeliveries++;
            
            // Update transport node reputation
            TransportNode storage node = transportNodes[msg.sender];
            node.totalShipments++;
            node.successRate = (node.successRate * (node.totalShipments - 1) + 100) / node.totalShipments;
            
        } else {
            _updateShipmentStatus(shipmentId, ShipmentStatus.Delayed);
            
            // Penalty for late delivery
            TransportIncentive storage incentive = transporterIncentives[msg.sender];
            incentive.totalDeliveries++;
            
            // FL anomaly detection for late delivery
            FLTransportMetrics storage flMetrics = transporterFLMetrics[msg.sender];
            flMetrics.anomalyScore += 15;
            
            if (flMetrics.anomalyScore > 70) {
                emit FLRouteAnomalyDetected(msg.sender, shipmentId, flMetrics.anomalyScore, "Frequent late deliveries", block.timestamp);
            }
        }
    }

    function calculateTransportIncentive(address transporter) public view returns (uint256) {
        TransportIncentive memory incentive = transporterIncentives[transporter];
        
        if (incentive.totalDeliveries == 0) return 0;
        
        // Base incentive: distance-based
        uint256 baseIncentive = incentive.totalDistance * 0.0001 ether;
        
        // Performance bonus: on-time delivery rate
        uint256 onTimeRate = (incentive.onTimeDeliveries * 100) / incentive.totalDeliveries;
        uint256 performanceBonus = (baseIncentive * onTimeRate) / 200; // Max 50% bonus
        
        // FL efficiency bonus
        FLTransportMetrics memory flMetrics = transporterFLMetrics[transporter];
        uint256 efficiencyBonus = 0;
        if (flMetrics.anomalyScore < 20) { // Low anomaly = high efficiency
            efficiencyBonus = baseIncentive / 10; // 10% efficiency bonus
        }
        
        return baseIncentive + performanceBonus + efficiencyBonus;
    }

    function claimTransportIncentive() external onlyRole(TRANSPORTER_ROLE) nonReentrant {
        uint256 incentiveAmount = calculateTransportIncentive(msg.sender);
        require(incentiveAmount > 0, "No incentive available");
        require(address(this).balance >= incentiveAmount, "Insufficient contract balance");
        
        TransportIncentive storage incentive = transporterIncentives[msg.sender];
        require(block.timestamp > incentive.lastClaim + 1 days, "Can only claim once per day");
        
        incentive.lastClaim = block.timestamp;
        incentive.incentivePool += incentiveAmount;
        
        // Reset counters after claim
        incentive.totalDistance = 0;
        incentive.onTimeDeliveries = 0;
        incentive.totalDeliveries = 0;
        
        (bool success, ) = payable(msg.sender).call{value: incentiveAmount}("");
        require(success, "Incentive transfer failed");
        
        uint256 performanceScore = (incentive.onTimeDeliveries * 100) / incentive.totalDeliveries;
        emit TransportIncentivePaid(msg.sender, incentiveAmount, performanceScore, block.timestamp);
    }

    // --- FL-based Route Optimization ---
    function optimizeRoute(
        uint256 shipmentId,
        string memory optimizedRoute,
        uint256 estimatedSavings
    ) external onlyRole(HUB_COORDINATOR_ROLE) {
        require(shipments[shipmentId].shipmentId != 0, "Shipment does not exist");
        require(shipments[shipmentId].status == ShipmentStatus.Created, "Route can only be optimized before transit");
        
        // Update FL metrics for route optimization
        address transporter = shipments[shipmentId].transporter;
        FLTransportMetrics storage metrics = transporterFLMetrics[transporter];
        metrics.routeOptimizationScore += 10;
        
        emit RouteOptimized(shipmentId, optimizedRoute, estimatedSavings, block.timestamp);
    }

    // --- FL Integration Functions ---
    function _updateTransporterFLMetrics(address transporter, bool approved) internal {
        FLTransportMetrics storage metrics = transporterFLMetrics[transporter];
        
        if (approved) {
            if (metrics.anomalyScore > 0) metrics.anomalyScore -= 5;
            metrics.delayPredictionAccuracy += 1;
        } else {
            metrics.anomalyScore += 10;
        }
        
        metrics.lastModelUpdate = block.timestamp;
    }

    function updateFLModel(address transporter, uint256 newAnomalyScore) external onlyRole(HUB_COORDINATOR_ROLE) {
        transporterFLMetrics[transporter].anomalyScore = newAnomalyScore;
        transporterFLMetrics[transporter].lastModelUpdate = block.timestamp;
    }

    // --- Cross-Chain Coordination ---
    function syncShipmentToHub(uint256 shipmentId) external onlyRole(HUB_COORDINATOR_ROLE) {
        require(shipments[shipmentId].shipmentId != 0, "Shipment does not exist");
        
        // Emit event for hub to process
        Shipment memory shipment = shipments[shipmentId];
        emit ShipmentStatusUpdated(shipmentId, shipment.status, shipment.status, msg.sender, block.timestamp);
    }

    // --- View Functions ---
    function getShipment(uint256 shipmentId) external view returns (Shipment memory) {
        require(shipments[shipmentId].shipmentId != 0, "Shipment does not exist");
        return shipments[shipmentId];
    }

    function getShipmentVotes(uint256 shipmentId) external view returns (ConsensusVote[] memory) {
        return shipmentVotes[shipmentId];
    }

    function getTransporterMetrics(address transporter) external view returns (TransportIncentive memory, FLTransportMetrics memory) {
        return (transporterIncentives[transporter], transporterFLMetrics[transporter]);
    }

    function getTransportNode(address nodeAddress) external view returns (TransportNode memory) {
        return transportNodes[nodeAddress];
    }

    // --- Admin Functions ---
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    function updateConsensusThreshold(uint256 newThreshold) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newThreshold > 50 && newThreshold <= 100, "Threshold must be between 50-100");
        consensusThreshold = newThreshold;
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