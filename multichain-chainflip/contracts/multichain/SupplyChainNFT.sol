// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "./Marketplace.sol";
import "./BatchProcessing.sol";
import "./DisputeResolution.sol";
import "./NodeManagement.sol";
import { IERC721 as IERC721Interface } from "@openzeppelin/contracts/token/ERC721/IERC721.sol";

/**
* @title SupplyChainNFT - Multi-Chain Compatible
* @dev Main contract implementing all ChainFLIP algorithms with multi-chain support and FL integration
*/
contract SupplyChainNFT is Marketplace, BatchProcessing, DisputeResolution, NodeManagement {

    // --- Dispute Resolution State ---
    mapping(uint256 => DisputeResolution.Dispute) public disputesData;
    uint256 public nextDisputeId = 1;
    mapping(uint256 => uint256) public activeDisputeIdForToken;

    // --- Cross-Chain State ---
    mapping(bytes32 => bool) public processedCrossChainDisputes;
    mapping(uint256 => uint256[]) public disputeChains; // disputeId => array of chainIds where dispute exists

    // --- FL Integration State ---
    struct FLMetrics {
        uint256 totalTransactions;
        uint256 flaggedTransactions;
        uint256 averageAnomalyScore;
        uint256 lastModelUpdate;
    }
    
    mapping(uint256 => FLMetrics) public chainFLMetrics; // chainId => FL metrics

    // --- Events ---
    event PaymentSuspended(uint256 tokenId);
    event DirectSaleAndTransferCompleted(uint256 indexed tokenId, address indexed seller, address indexed buyer, uint256 price, string oldCIDForVerification);
    event FLModelUpdated(uint256 chainId, uint256 timestamp, string modelHash);
    event CrossChainFLSync(uint256 sourceChainId, uint256 targetChainId, bytes32 syncHash, uint256 timestamp);

    constructor(address initialAdmin)
        NFTCore(initialAdmin) 
        BatchProcessing(initialAdmin) 
    {
        // Initialize FL metrics for current chain
        chainFLMetrics[block.chainid] = FLMetrics({
            totalTransactions: 0,
            flaggedTransactions: 0,
            averageAnomalyScore: 0,
            lastModelUpdate: block.timestamp
        });
    }

    // --- Enhanced Sale Functions ---
    function sellProduct(uint256 tokenId, uint256 price) public override {
        // FL-based price validation
        _validatePriceWithFL(tokenId, price);
        super.sellProduct(tokenId, price);
        _updateFLTransactionMetrics(tokenId, false);
    }
    
    function sellAndTransferProduct(
        uint256 tokenId,
        uint256 price,
        address buyer,
        string memory currentProductCID
    ) public {
        require(ownerOf(tokenId) == msg.sender, "SupplyChainNFT: Caller is not the owner");
        require(buyer != address(0), "SupplyChainNFT: Buyer cannot be zero address");

        string memory result = verifyProductAuthenticity(
            tokenId,
            currentProductCID,
            msg.sender 
        );
        require(keccak256(bytes(result)) == keccak256(bytes("Product is Authentic")), result);
    
        // FL validation for direct sales
        _validatePriceWithFL(tokenId, price);
        
        _transferNFTInternal(msg.sender, buyer, tokenId);
        _updateFLTransactionMetrics(tokenId, false);
        
        emit DirectSaleAndTransferCompleted(tokenId, msg.sender, buyer, price, currentProductCID);
    }

    // --- FL Integration Functions ---
    function _validatePriceWithFL(uint256 tokenId, uint256 price) internal {
        // Get market metrics for current chain
        MarketMetrics memory metrics = getMarketMetrics(block.chainid);
        
        // Simple FL-based validation (would be enhanced by actual FL model)
        if (metrics.averagePrice > 0 && (price > metrics.averagePrice * 5 || price < metrics.averagePrice / 5)) {
            chainFLMetrics[block.chainid].flaggedTransactions++;
            
            // Don't revert, just emit warning and update metrics
            emit MarketAnomalyDetected(block.chainid, 80, "Price outside FL validation range", block.timestamp);
        }
    }

    function _updateFLTransactionMetrics(uint256 tokenId, bool flagged) internal {
        FLMetrics storage metrics = chainFLMetrics[block.chainid];
        metrics.totalTransactions++;
        
        if (flagged) {
            metrics.flaggedTransactions++;
        }
        
        // Update average anomaly score (simplified)
        if (metrics.totalTransactions > 0) {
            metrics.averageAnomalyScore = (metrics.flaggedTransactions * 100) / metrics.totalTransactions;
        }
    }

    function updateFLModel(string memory modelHash) external onlyRole(DEFAULT_ADMIN_ROLE) {
        chainFLMetrics[block.chainid].lastModelUpdate = block.timestamp;
        emit FLModelUpdated(block.chainid, block.timestamp, modelHash);
    }

    function syncFLMetricsToChain(uint256 targetChainId) external onlyRole(CROSS_CHAIN_ROLE) {
        bytes32 syncHash = keccak256(abi.encodePacked(
            block.chainid,
            targetChainId,
            chainFLMetrics[block.chainid].averageAnomalyScore,
            block.timestamp
        ));
        
        emit CrossChainFLSync(block.chainid, targetChainId, syncHash, block.timestamp);
    }

    // --- Reputation Management Overrides ---
    function updateReputation(address node, int256 scoreChange, string memory reason) internal override(BatchProcessing, NodeManagement) {
        NodeManagement.updateReputation(node, scoreChange, reason);
    }

    function penalizeNode(address node, uint256 penalty, string memory reason) internal override(BatchProcessing, NodeManagement) {
        NodeManagement.penalizeNode(node, penalty, reason);
    }
    
    function adminUpdateReputation(address node, uint256 score) public onlyOwner {
        updateReputation(node, int256(score), "Admin Reputation Update");
    }

    function adminPenalizeNode(address node, uint256 penalty) public onlyOwner {
        penalizeNode(node, penalty, "Admin Penalty");
    }

    // --- Node Management Overrides & Implementations ---
    function _getAllPrimaryNodes() internal view override(BatchProcessing) returns (address[] memory) {
        uint256 primaryNodeCount = 0;
        for (uint256 i = 0; i < allNodes.length; i++) {
            if (isPrimaryNode(allNodes[i])) {
                primaryNodeCount++;
            }
        }
        address[] memory primaryNodesList = new address[](primaryNodeCount);
        uint256 idx = 0;
        for (uint256 i = 0; i < allNodes.length; i++) {
            if (isPrimaryNode(allNodes[i])) {
                primaryNodesList[idx] = allNodes[i];
                idx++;
            }
        }
        return primaryNodesList;
    }

    function getTotalPrimaryNodes() public view override(NodeManagement) returns (uint256) {
        return NodeManagement.getTotalPrimaryNodes(); 
    }

    function isPrimaryNode(address node) internal view override(BatchProcessing, NodeManagement) returns (bool) {
        return NodeManagement.isPrimaryNode(node);
    }

    function isSecondaryNode(address node) internal view override(BatchProcessing, NodeManagement) returns (bool) {
        return NodeManagement.isSecondaryNode(node);
    }

    function getNodeReputation(address node) internal view override(BatchProcessing) returns (uint256) {
        return NodeManagement.nodeReputation[node];
    }

    // --- Enhanced Dispute Resolution Implementation ---
    function openDispute(
        uint256 tokenId,
        string memory reason,
        string memory evidenceDataString
    ) public returns (uint256) {
        require(_exists(tokenId), "Dispute: Token does not exist");
        require(activeDisputeIdForToken[tokenId] == 0, "Dispute: Token already has an active dispute");

        uint256 currentDisputeId = nextDisputeId++;
        DisputeResolution.Dispute storage newDispute = disputesData[currentDisputeId];
        
        newDispute.tokenId = tokenId;
        newDispute.plaintiff = msg.sender; 
        newDispute.reason = reason;
        newDispute.evidenceCID = "";
        newDispute.openedTimestamp = block.timestamp;
        newDispute.chainId = block.chainid;
        
        // Generate cross-chain hash for dispute coordination
        newDispute.crossChainHash = keccak256(abi.encodePacked(
            currentDisputeId,
            tokenId,
            msg.sender,
            block.chainid,
            block.timestamp
        ));

        activeDisputeIdForToken[tokenId] = currentDisputeId;
        disputeChains[currentDisputeId].push(block.chainid);

        // Update FL metrics for dispute
        _updateFLTransactionMetrics(tokenId, true);

        emit DisputeOpened(currentDisputeId, tokenId, msg.sender, reason, evidenceDataString, block.chainid, block.timestamp);
        return currentDisputeId;
    }

    function proposeArbitratorCandidate(uint256 disputeId, address candidate) public override {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        require(!d.decisionRecorded, "Dispute: Decision already recorded, cannot add candidates");
        require(isVerified(candidate), "Dispute: Candidate must be a verified node"); 

        for (uint i = 0; i < d.candidates.length; i++) {
            require(d.candidates[i] != candidate, "Dispute: Candidate already proposed");
        }
        d.candidates.push(candidate);
        emit ArbitratorCandidateProposed(disputeId, candidate, msg.sender, block.timestamp);
    }

    function makeDisputeDecision(
        uint256 disputeId,
        string memory resolutionDetails,
        uint8 outcome
    ) public {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        require(!d.decisionRecorded, "Dispute: Decision already recorded");
        require(_isCandidate(disputeId, msg.sender), "Dispute: Caller is not an approved arbitrator");

        d.resolutionDetails = resolutionDetails;
        d.outcome = outcome;
        d.decisionRecorded = true;
        d.decisionTimestamp = block.timestamp;

        emit DisputeDecisionMade(disputeId, msg.sender, resolutionDetails, outcome, block.timestamp);
    }

    event DisputeDecisionMade(
        uint256 indexed disputeId,
        address indexed arbitrator,
        string resolutionDetails,
        uint8 outcome,
        uint256 timestamp
    );

    function _isCandidate(uint256 disputeId, address candidateAddr) internal view returns (bool) {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        if (d.openedTimestamp == 0) return false;
        for (uint256 i = 0; i < d.candidates.length; i++) {
            if (d.candidates[i] == candidateAddr) {
                return true;
            }
        }
        return false;
    }

    function voteForArbitrator(uint256 disputeId, address candidate) public override {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        require(_isCandidate(disputeId, candidate), "Dispute: Not a valid arbitrator candidate for this dispute");
        require(d.votes[msg.sender] == 0, "Dispute: Voter has already voted for a candidate in this dispute");
        
        d.votes[candidate] += 1;
        d.votes[msg.sender] = 1;

        emit ArbitratorVoted(disputeId, msg.sender, candidate, block.timestamp);
    }

    function selectArbitrator(uint256 disputeId) public override {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        require(d.selectedArbitrator == address(0), "Dispute: Arbitrator already selected");
        require(d.candidates.length > 0, "Dispute: No candidates available");

        address winner = address(0);
        uint256 highestVotes = 0;

        for (uint256 i = 0; i < d.candidates.length; i++) {
            address currentCandidate = d.candidates[i];
            uint256 currentVotes = d.votes[currentCandidate];
            if (currentVotes > highestVotes) {
                highestVotes = currentVotes;
                winner = currentCandidate;
            }
        }
        
        require(winner != address(0), "Dispute: No valid arbitrator selected (tie or no votes)");
        d.selectedArbitrator = winner;
        emit ArbitratorSelected(disputeId, d.tokenId, winner, block.timestamp);
    }

    function recordDecision(
        uint256 disputeId,
        string memory _resolutionDetails,
        string memory _resolutionDataString,
        uint8 _outcome
    ) public override {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        require(msg.sender == d.selectedArbitrator, "Dispute: Only selected arbitrator can record decision");
        require(!d.decisionRecorded, "Dispute: Decision already recorded");

        d.resolutionDetails = _resolutionDetails;
        d.resolutionCID = "";
        d.outcome = _outcome;
        d.decisionRecorded = true;
        d.decisionTimestamp = block.timestamp;

        emit DisputeDecisionRecorded(disputeId, d.tokenId, msg.sender, _resolutionDetails, _resolutionDataString, _outcome, block.timestamp);
    }

    function enforceNFTReturn(uint256 disputeId, address returnToAddress) public override {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        require(msg.sender == d.selectedArbitrator, "Dispute: Only selected arbitrator can enforce");
        require(d.decisionRecorded, "Dispute: Decision must be recorded first");
        require(!d.nftReturnEnforced, "Dispute: NFT return already enforced");
        require(returnToAddress != address(0), "Dispute: Return address cannot be zero");

        uint256 currentTokenId = d.tokenId;
        address currentOwner = ownerOf(currentTokenId);
        
        require(currentOwner != returnToAddress, "Dispute: NFT already owned by the returnToAddress or invalid operation");

        _transferNFTInternal(currentOwner, returnToAddress, currentTokenId); 
        d.nftReturnEnforced = true;

        emit NFTReturnEnforced(disputeId, currentTokenId, msg.sender, currentOwner, returnToAddress, block.timestamp);
    }

    function enforceRefund(uint256 disputeId, address refundTo, address refundFrom, uint256 refundAmount) public override {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        require(msg.sender == d.selectedArbitrator, "Dispute: Only selected arbitrator can enforce refund");
        require(d.decisionRecorded, "Dispute: Decision must be recorded first");
        require(!d.refundEnforced, "Dispute: Refund already enforced");
        require(refundTo != address(0), "Dispute: Refund address cannot be zero");
        require(refundAmount > 0, "Dispute: Refund amount must be positive");
        require(address(this).balance >= refundAmount, "Dispute: Contract has insufficient funds for this refund");

        d.refundEnforced = true;
        
        (bool success, ) = payable(refundTo).call{value: refundAmount}("");
        require(success, "Dispute: Refund transfer failed");

        emit RefundEnforced(disputeId, msg.sender, refundFrom, refundTo, refundAmount, block.timestamp);
    }

    function concludeDispute(uint256 disputeId) public override {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        require(msg.sender == d.selectedArbitrator || msg.sender == d.plaintiff, "Dispute: Not authorized to conclude");
        require(d.decisionRecorded, "Dispute: Decision must be recorded to conclude");
        require(!d.enforced, "Dispute: Already concluded");
        
        d.enforced = true;
        d.enforcedTimestamp = block.timestamp;
        activeDisputeIdForToken[d.tokenId] = 0; 

        emit DisputeConcluded(disputeId, d.tokenId, d.enforced, block.timestamp);
    }

    // --- Cross-Chain Dispute Functions ---
    function syncDisputeToChain(uint256 disputeId, uint256 targetChainId) public override onlyRole(CROSS_CHAIN_ROLE) {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        
        bytes32 syncHash = keccak256(abi.encodePacked(
            disputeId,
            block.chainid,
            targetChainId,
            d.crossChainHash,
            block.timestamp
        ));
        
        require(!processedCrossChainDisputes[syncHash], "Dispute sync already processed");
        processedCrossChainDisputes[syncHash] = true;
        
        disputeChains[disputeId].push(targetChainId);
        
        emit CrossChainDisputeSync(disputeId, targetChainId, syncHash, block.timestamp);
    }

    function shareEvidenceToChain(uint256 disputeId, uint256 targetChainId) public override onlyRole(CROSS_CHAIN_ROLE) {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        require(bytes(d.evidenceCID).length > 0, "Dispute: No evidence CID to share");
        
        emit CrossChainEvidenceShared(disputeId, d.evidenceCID, targetChainId, block.timestamp);
    }

    // --- ERC721 Overrides ---
    function ownerOf(uint256 tokenId) public view override(ERC721, BatchProcessing, IERC721Interface) returns (address) {
        return ERC721.ownerOf(tokenId);
    }

    function _batchTransfer(address from, address to, uint256 tokenId) internal override(BatchProcessing) {
        _transferNFTInternal(from, to, tokenId);
    }

    function isVerified(address candidate) public view override(DisputeResolution, NodeManagement) returns (bool) {
        return NodeManagement.isVerified(candidate);
    }

    function getProductHistory(uint256 tokenId) public view override(DisputeResolution) returns (string memory) {
        return cidMapping[tokenId]; 
    }

    // --- Backend CID Update Functions ---
    function updateDisputeEvidenceCID(uint256 disputeId, string memory newEvidenceCID) public override onlyOwner {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        d.evidenceCID = newEvidenceCID;
    }

    function updateDisputeResolutionCID(uint256 disputeId, string memory newResolutionCID) public override onlyOwner {
        DisputeResolution.Dispute storage d = disputesData[disputeId];
        require(d.openedTimestamp > 0, "Dispute: Dispute does not exist");
        d.resolutionCID = newResolutionCID;
    }

    // --- View Functions ---
    function getFLMetrics(uint256 chainId) public view returns (FLMetrics memory) {
        return chainFLMetrics[chainId];
    }

    function getDisputeChains(uint256 disputeId) public view returns (uint256[] memory) {
        return disputeChains[disputeId];
    }

    function isDisputeCrossChain(uint256 disputeId) public view returns (bool) {
        return disputeChains[disputeId].length > 1;
    }

    // --- Contract Funding ---
    receive() external payable {}
    fallback() external payable {}

    function depositDisputeFunds() external payable {
        require(msg.value > 0, "Deposit amount must be greater than zero");
        emit FundsDeposited(msg.sender, msg.value);
    }

    event FundsDeposited(address indexed depositor, uint256 amount);
}