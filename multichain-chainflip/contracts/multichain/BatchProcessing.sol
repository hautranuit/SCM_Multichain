// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
* @title BatchProcessing - Multi-Chain Compatible
* @dev Abstract contract for batch processing transactions across multiple chains with FL integration
*/
abstract contract BatchProcessing is Ownable {
    // --- Data Structures ---
    struct TransactionData {
        address from;
        address to;
        uint256 tokenId;
        uint256 chainId; // Track which chain the transaction is for
    }

    struct Batch {
        uint256 batchId;
        TransactionData[] transactions;
        bool validated;
        bool committed;
        address proposer;
        bool flagged;
        address[] selectedValidators;
        uint256 numSelectedValidators;
        uint256 chainId; // Track which chain this batch is for
        bytes32 crossChainHash; // For cross-chain batch coordination
        bool isCrossChain; // Whether this batch involves cross-chain transactions
    }

    // --- FL Integration Data ---
    struct BatchMetrics {
        uint256 batchId;
        uint256 processingTime;
        uint256 validatorPerformance;
        uint256 anomalyScore; // From FL model
        bool flValidated; // Whether FL model validated this batch
    }

    mapping(uint256 => Batch) public batches;
    mapping(uint256 => BatchMetrics) public batchMetrics;
    uint256 public nextBatchId = 1;
    mapping(uint256 => uint256) public batchApprovals;
    mapping(uint256 => uint256) public batchDenials;
    mapping(uint256 => mapping(address => uint8)) public batchVotes; // 0: not voted, 1: approve, 2: deny
    mapping(uint256 => mapping(address => bool)) public isSelectedValidator;
    mapping(bytes32 => bool) public processedCrossChainBatches;
    
    uint256 public numValidatorsToSelect = 5;
    uint256 public superMajorityFraction = 66;
    uint256 public flAnomalyThreshold = 80; // FL anomaly threshold (0-100)

    // --- Events ---
    event BatchProposed(uint256 batchId, address proposer, address[] selectedValidators, bool isCrossChain);
    event BatchValidated(uint256 batchId, address validator, bool approve);
    event BatchCommitted(uint256 batchId, bool success);
    event ReconciliationComplete(uint256 reconciledCount);
    event CrossChainBatchSync(uint256 indexed batchId, uint256 targetChainId, bytes32 crossChainHash, uint256 timestamp);
    event FLValidationCompleted(uint256 indexed batchId, uint256 anomalyScore, bool validated, uint256 timestamp);
    event BatchAnomalyDetected(uint256 indexed batchId, uint256 anomalyScore, address flaggedBy, uint256 timestamp);

    constructor(address initialOwner) Ownable(initialOwner) {}

    // --- Abstract Functions ---
    function _batchTransfer(address from, address to, uint256 tokenId) internal virtual;
    function ownerOf(uint256 tokenId) public view virtual returns (address);
    function updateReputation(address node, int256 scoreChange, string memory reason) internal virtual;
    function penalizeNode(address node, uint256 penalty, string memory reason) internal virtual;
    function _getAllPrimaryNodes() internal view virtual returns (address[] memory);
    function getNodeReputation(address node) internal view virtual returns (uint256);
    function isPrimaryNode(address node) internal view virtual returns (bool);
    function isSecondaryNode(address node) internal view virtual returns (bool);

    // --- FL Integration Functions ---
    function requestFLValidation(uint256 batchId) internal virtual {
        // This would trigger FL model validation
        // For now, we emit an event that the FL service can listen to
        Batch storage batch = batches[batchId];
        uint256 batchSize = batch.transactions.length;
        uint256 proposerReputation = getNodeReputation(batch.proposer);
        
        // Emit event for FL service to process
        emit FLValidationCompleted(batchId, 0, true, block.timestamp); // Placeholder
    }

    function updateFLValidation(uint256 batchId, uint256 anomalyScore, bool validated) external onlyOwner {
        require(batches[batchId].batchId != 0, "Batch does not exist");
        
        batchMetrics[batchId].anomalyScore = anomalyScore;
        batchMetrics[batchId].flValidated = validated;
        
        if (anomalyScore > flAnomalyThreshold) {
            batches[batchId].flagged = true;
            emit BatchAnomalyDetected(batchId, anomalyScore, msg.sender, block.timestamp);
        }
        
        emit FLValidationCompleted(batchId, anomalyScore, validated, block.timestamp);
    }

    // --- Enhanced Batch Processing Functions ---
    function proposeBatch(TransactionData[] memory txs, bool isCrossChain) public virtual {
        require(isSecondaryNode(msg.sender), "Only Secondary Node can propose batch");

        uint256 currentBatchId = nextBatchId;
        Batch storage b = batches[currentBatchId];
        b.batchId = currentBatchId;
        b.proposer = msg.sender;
        b.chainId = block.chainid;
        b.isCrossChain = isCrossChain;

        if (isCrossChain) {
            b.crossChainHash = keccak256(abi.encodePacked(
                currentBatchId,
                block.chainid,
                msg.sender,
                block.timestamp
            ));
        }

        for (uint256 i = 0; i < txs.length; i++) {
            b.transactions.push(txs[i]);
        }

        address[] memory selected = getRandomValidators(currentBatchId, numValidatorsToSelect);
        b.selectedValidators = selected;
        b.numSelectedValidators = selected.length;

        for (uint j = 0; j < selected.length; j++) {
            isSelectedValidator[currentBatchId][selected[j]] = true;
        }

        // Initialize batch metrics
        batchMetrics[currentBatchId] = BatchMetrics({
            batchId: currentBatchId,
            processingTime: block.timestamp,
            validatorPerformance: 0,
            anomalyScore: 0,
            flValidated: false
        });

        // Request FL validation
        requestFLValidation(currentBatchId);

        emit BatchProposed(currentBatchId, msg.sender, selected, isCrossChain);
        nextBatchId++;
    }

    function getRandomValidators(uint256 batchId, uint256 numToSelect)
        internal view virtual returns (address[] memory)
    {
        address[] memory primaryNodes = _getAllPrimaryNodes();
        uint256 len = primaryNodes.length;

        if (numToSelect == 0 || len == 0) {
            return new address[](0);
        }
        if (numToSelect > len) {
            numToSelect = len;
        }

        // Enhanced selection with FL-based reputation weighting
        uint256[] memory reputations = new uint256[](len);
        uint256 totalReputation = 0;
        for (uint256 i = 0; i < len; i++) {
            // Base reputation + FL performance bonus
            uint256 baseRep = getNodeReputation(primaryNodes[i]);
            uint256 enhancedRep = 1 + baseRep + (baseRep / 10); // 10% FL bonus
            reputations[i] = enhancedRep;
            totalReputation += enhancedRep;
        }

        address[] memory selected = new address[](numToSelect);
        address[] memory candidates = primaryNodes;
        uint256[] memory currentReputations = reputations;

        uint256 randSeed = uint256(keccak256(abi.encodePacked(blockhash(block.number - 1), block.timestamp, batchId)));
        uint256 currentLength = len;

        for (uint256 i = 0; i < numToSelect; i++) {
            require(totalReputation > 0, "Reputation sum error");
            randSeed = uint256(keccak256(abi.encodePacked(randSeed, i, block.difficulty, block.coinbase)));
            uint256 rand = randSeed % totalReputation;
            uint256 cumulative = 0;
            uint256 selectedIndex = 0;

            for (uint256 j = 0; j < currentLength; j++) {
                cumulative += currentReputations[j];
                if (rand < cumulative) {
                    selectedIndex = j;
                    break;
                }
            }

            selected[i] = candidates[selectedIndex];
            totalReputation -= currentReputations[selectedIndex];
            candidates[selectedIndex] = candidates[currentLength - 1];
            currentReputations[selectedIndex] = currentReputations[currentLength - 1];
            currentLength--;
            randSeed = uint256(keccak256(abi.encodePacked(randSeed, i, selected[i])));
        }
        return selected;
    }

    function validateBatch(uint256 batchId, bool approve) public virtual {
        require(isSelectedValidator[batchId][msg.sender], "Not a selected validator for this batch");
        Batch storage b = batches[batchId];
        require(b.batchId != 0, "Batch does not exist");
        require(!b.committed, "Batch already committed");
        require(!b.flagged, "Batch flagged for review");
        require(batchVotes[batchId][msg.sender] == 0, "Already voted");

        batchVotes[batchId][msg.sender] = approve ? 1 : 2;

        if (approve) {
            batchApprovals[batchId]++;
        } else {
            batchDenials[batchId]++;
        }
        emit BatchValidated(batchId, msg.sender, approve);
    }

    function commitBatch(uint256 batchId) public virtual {
        Batch storage b = batches[batchId];
        require(b.batchId != 0, "Batch does not exist");
        require(!b.committed, "Batch already committed");
        require(!b.flagged, "Batch is flagged, cannot commit");
        require(b.numSelectedValidators > 0, "No validators selected");

        // Check FL validation if required
        if (batchMetrics[batchId].anomalyScore > flAnomalyThreshold) {
            b.flagged = true;
            penalizeNode(b.proposer, 5, "High FL anomaly score detected");
            emit BatchCommitted(batchId, false);
            return;
        }

        uint256 approvalPercent = (batchApprovals[batchId] * 100) / b.numSelectedValidators;

        if (approvalPercent >= superMajorityFraction) {
            b.validated = true;
            b.committed = true;
            
            // Process transactions
            for (uint256 i = 0; i < b.transactions.length; i++) {
                TransactionData memory txData = b.transactions[i];
                if (ownerOf(txData.tokenId) == txData.from) {
                    _batchTransfer(txData.from, txData.to, txData.tokenId);
                }
            }
            
            // Update batch metrics
            batchMetrics[batchId].processingTime = block.timestamp - batchMetrics[batchId].processingTime;
            
            updateReputation(b.proposer, 5, "Successful batch proposal");
            _rewardValidators(batchId, true);
            
            // Handle cross-chain sync if needed
            if (b.isCrossChain) {
                emit CrossChainBatchSync(batchId, 0, b.crossChainHash, block.timestamp); // targetChainId would be determined by logic
            }
            
            emit BatchCommitted(batchId, true);
        } else {
            uint256 denialPercent = (batchDenials[batchId] * 100) / b.numSelectedValidators;
            if (denialPercent > (100 - superMajorityFraction)) {
                b.flagged = true;
                penalizeNode(b.proposer, 2, "Batch flagged for review");
                _rewardValidators(batchId, false);
                emit BatchCommitted(batchId, false);
            }
        }
    }

    function _rewardValidators(uint256 batchId, bool batchPassed) internal virtual {
        Batch storage b = batches[batchId];
        BatchMetrics storage metrics = batchMetrics[batchId];
        
        for (uint256 i = 0; i < b.numSelectedValidators; i++) {
            address validator = b.selectedValidators[i];
            uint8 vote = batchVotes[batchId][validator];
            if (vote == 0) continue;
            
            bool votedApprove = (vote == 1);
            bool correctVote = (votedApprove == batchPassed);
            
            if (correctVote) {
                // Base reward + FL performance bonus
                int256 reward = 2;
                if (metrics.flValidated && metrics.anomalyScore < 20) {
                    reward += 1; // FL bonus for low anomaly score
                }
                updateReputation(validator, reward, "Correct validation vote with FL consideration");
            } else {
                penalizeNode(validator, 1, "Incorrect validation vote");
            }
        }
    }

    // --- Cross-Chain Functions ---
    function syncBatchToChain(uint256 batchId, uint256 targetChainId) public virtual onlyOwner {
        Batch storage batch = batches[batchId];
        require(batch.batchId != 0, "Batch does not exist");
        require(batch.committed, "Batch not committed");
        
        bytes32 syncHash = keccak256(abi.encodePacked(
            batchId,
            block.chainid,
            targetChainId,
            block.timestamp
        ));
        
        require(!processedCrossChainBatches[syncHash], "Batch sync already processed");
        processedCrossChainBatches[syncHash] = true;
        
        emit CrossChainBatchSync(batchId, targetChainId, syncHash, block.timestamp);
    }

    function reconcileLogs() public virtual onlyOwner {
        uint256 reconciledCount = 0;
        for (uint256 i = 1; i < nextBatchId; i++) {
            Batch storage b = batches[i];
            if (b.flagged && !b.committed) {
                b.flagged = false;
                reconciledCount++;
            }
        }
        emit ReconciliationComplete(reconciledCount);
    }

    // --- View Functions ---
    function getBatchDetails(uint256 batchId) public view returns (Batch memory) {
        require(batches[batchId].batchId != 0, "Batch does not exist");
        return batches[batchId];
    }

    function getBatchMetrics(uint256 batchId) public view returns (BatchMetrics memory) {
        return batchMetrics[batchId];
    }

    function getSelectedValidatorsForBatch(uint256 batchId) public view returns (address[] memory) {
        require(batches[batchId].batchId != 0, "Batch does not exist");
        return batches[batchId].selectedValidators;
    }

    function isBatchFLValidated(uint256 batchId) public view returns (bool) {
        return batchMetrics[batchId].flValidated;
    }
}