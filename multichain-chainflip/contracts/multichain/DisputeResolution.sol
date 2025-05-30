// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

/**
* @title DisputeResolution - Multi-Chain Compatible
* @dev Abstract contract for handling disputes across multiple chains with cross-chain evidence support
*/
abstract contract DisputeResolution {
    // --- Data Structures ---
    struct Dispute {
        uint256 tokenId;
        address plaintiff;
        address defendant;
        string reason;
        string evidenceCID; // IPFS CID for evidence
        address[] candidates;
        mapping(address => uint256) votes;
        address selectedArbitrator;
        bool decisionRecorded;
        string resolutionDetails;
        string resolutionCID; // IPFS CID for resolution
        uint8 outcome; // 0=Dismissed, 1=FavorPlaintiff, 2=FavorDefendant, 3=Partial
        bool nftReturnEnforced;
        bool refundEnforced;
        bool enforced;
        uint256 openedTimestamp;
        uint256 decisionTimestamp;
        uint256 enforcedTimestamp;
        uint256 chainId; // Track which chain the dispute is on
        bytes32 crossChainHash; // For cross-chain dispute coordination
    }

    // --- Multi-Chain Events ---
    event DisputeOpened(uint256 indexed disputeId, uint256 indexed tokenId, address indexed plaintiff, string reason, string evidenceDataString, uint256 chainId, uint256 timestamp);
    event ArbitratorCandidateProposed(uint256 indexed disputeId, address indexed candidate, address indexed proposer, uint256 timestamp);
    event ArbitratorVoted(uint256 indexed disputeId, address indexed voter, address indexed candidate, uint256 timestamp);
    event ArbitratorSelected(uint256 indexed disputeId, uint256 indexed tokenId, address indexed selectedArbitrator, uint256 timestamp);
    
    event DisputeDecisionRecorded(
        uint256 indexed disputeId,
        uint256 indexed tokenId,
        address indexed arbitrator,
        string resolutionDetails,
        string resolutionDataString,
        uint8 outcome,
        uint256 timestamp
    );
    
    event NFTReturnEnforced(
        uint256 indexed disputeId,
        uint256 indexed tokenId,
        address indexed arbitrator,
        address from,
        address to,
        uint256 timestamp
    );
    
    event RefundEnforced(
        uint256 indexed disputeId,
        address arbitrator,
        address indexed refundFrom,
        address indexed refundTo,
        uint256 amount,
        uint256 timestamp
    );
    
    event DisputeConcluded(uint256 indexed disputeId, uint256 indexed tokenId, bool wasEnforced, uint256 timestamp);
    
    // --- Cross-Chain Dispute Events ---
    event CrossChainDisputeSync(uint256 indexed disputeId, uint256 targetChainId, bytes32 crossChainHash, uint256 timestamp);
    event CrossChainEvidenceShared(uint256 indexed disputeId, string evidenceCID, uint256 targetChainId, uint256 timestamp);

    // --- Abstract Functions ---
    function getProductHistory(uint256 tokenId) public view virtual returns (string memory);
    function isVerified(address candidate) public view virtual returns (bool);

    // --- Backend CID Update Functions ---
    function updateDisputeEvidenceCID(uint256 disputeId, string memory newEvidenceCID) public virtual;
    function updateDisputeResolutionCID(uint256 disputeId, string memory newResolutionCID) public virtual;

    // --- Core Dispute Functions ---
    function proposeArbitratorCandidate(uint256 disputeId, address candidate) public virtual;
    function voteForArbitrator(uint256 disputeId, address candidate) public virtual;
    function selectArbitrator(uint256 disputeId) public virtual;

    function recordDecision(
        uint256 disputeId,
        string memory resolutionDetails,
        string memory resolutionDataString,
        uint8 outcome
    ) public virtual;

    function enforceNFTReturn(uint256 disputeId, address returnToAddress) public virtual;
    function enforceRefund(uint256 disputeId, address refundTo, address refundFrom, uint256 amount) public virtual;
    function concludeDispute(uint256 disputeId) public virtual;

    // --- Cross-Chain Dispute Functions ---
    function syncDisputeToChain(uint256 disputeId, uint256 targetChainId) public virtual;
    function shareEvidenceToChain(uint256 disputeId, uint256 targetChainId) public virtual;
}