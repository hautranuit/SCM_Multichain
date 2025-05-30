// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

/**
* @title NodeManagement - Multi-Chain Compatible
* @dev Abstract contract for managing nodes across multiple chains with cross-chain reputation sync
*/
abstract contract NodeManagement {
    // --- Node Management Variables ---
    mapping(address => bool) internal _verifiedNodes;
    mapping(address => uint256) public nodeReputation;
    mapping(address => uint256) public lastActionTimestamp;
    mapping(address => uint256) public nodeRegistrationChain; // Track original registration chain

    enum Role { Manufacturer, Transporter, Customer, Retailer, Arbitrator, Unassigned }
    mapping(address => Role) public roles;

    enum NodeType { Primary, Secondary, Unspecified }
    mapping(address => NodeType) public nodeTypes;

    address[] public allNodes;

    // --- Cross-Chain Reputation Tracking ---
    mapping(address => mapping(uint256 => uint256)) public crossChainReputation; // node => chainId => reputation
    mapping(bytes32 => bool) public processedCrossChainActions; // Prevent duplicate cross-chain operations

    // --- Events ---
    event NodeVerified(address indexed node, bool status, uint256 chainId, uint256 timestamp);
    event ReputationUpdated(address indexed node, uint256 newReputation, int256 changeAmount, address indexed actor, string reason, uint256 timestamp);
    event NodePenalized(address indexed node, uint256 newReputation, uint256 penaltyAmount, address indexed actor, string reason, uint256 timestamp);
    event NodeRoleChanged(address indexed node, Role oldRole, Role newRole, address indexed actor, uint256 timestamp);
    event NodeTypeChanged(address indexed node, NodeType oldType, NodeType newType, address indexed actor, uint256 timestamp);
    
    // --- Cross-Chain Events ---
    event CrossChainReputationSync(address indexed node, uint256 targetChainId, uint256 reputation, bytes32 syncHash, uint256 timestamp);
    event CrossChainNodeRegistration(address indexed node, uint256 sourceChainId, Role role, NodeType nodeType, uint256 timestamp);

    // --- Node Management Functions ---
    function setVerifiedNode(address node, bool status) public virtual {
        _verifiedNodes[node] = status;
        lastActionTimestamp[msg.sender] = block.timestamp;
        lastActionTimestamp[node] = block.timestamp;
        
        if (nodeRegistrationChain[node] == 0) {
            nodeRegistrationChain[node] = block.chainid;
        }

        emit NodeVerified(node, status, block.chainid, block.timestamp);

        bool found = false;
        for (uint256 i = 0; i < allNodes.length; i++) {
            if (allNodes[i] == node) {
                found = true;
                break;
            }
        }
        if (!found) {
            allNodes.push(node);
        }
    }

    function setNodeType(address node, NodeType nType) public virtual {
        NodeType oldType = nodeTypes[node];
        nodeTypes[node] = nType;
        lastActionTimestamp[msg.sender] = block.timestamp;
        lastActionTimestamp[node] = block.timestamp;
        emit NodeTypeChanged(node, oldType, nType, msg.sender, block.timestamp);
    }

    function setRole(address _addr, Role _role) public virtual {
        Role oldRole = roles[_addr];
        roles[_addr] = _role;
        lastActionTimestamp[msg.sender] = block.timestamp;
        lastActionTimestamp[_addr] = block.timestamp;
        emit NodeRoleChanged(_addr, oldRole, _role, msg.sender, block.timestamp);
    }

    function getTotalPrimaryNodes() public view virtual returns (uint256) {
        uint256 count = 0;
        for (uint256 i = 0; i < allNodes.length; i++) {
            if (_verifiedNodes[allNodes[i]] && nodeTypes[allNodes[i]] == NodeType.Primary) {
                count++;
            }
        }
        return count;
    }

    function updateReputation(address node, int256 scoreChange, string memory reason) internal virtual {
        uint256 oldReputation = nodeReputation[node];
        if (scoreChange >= 0) {
            nodeReputation[node] += uint256(scoreChange);
        } else {
            uint256 change = uint256(-scoreChange);
            if (nodeReputation[node] > change) {
                nodeReputation[node] -= change;
            } else {
                nodeReputation[node] = 0;
            }
        }
        
        // Update cross-chain reputation for current chain
        crossChainReputation[node][block.chainid] = nodeReputation[node];
        
        lastActionTimestamp[node] = block.timestamp;
        emit ReputationUpdated(node, nodeReputation[node], scoreChange, msg.sender, reason, block.timestamp);
    }

    function penalizeNode(address node, uint256 penalty, string memory reason) internal virtual {
        uint256 oldReputation = nodeReputation[node];
        if (nodeReputation[node] > penalty) {
            nodeReputation[node] -= penalty;
        } else {
            nodeReputation[node] = 0;
        }
        
        // Update cross-chain reputation for current chain
        crossChainReputation[node][block.chainid] = nodeReputation[node];
        
        lastActionTimestamp[node] = block.timestamp;
        emit NodePenalized(node, nodeReputation[node], penalty, msg.sender, reason, block.timestamp);
    }

    // --- Cross-Chain Functions ---
    function syncReputationToChain(address node, uint256 targetChainId) public virtual {
        require(_verifiedNodes[node], "Node not verified");
        
        bytes32 syncHash = keccak256(abi.encodePacked(
            node,
            block.chainid,
            targetChainId,
            nodeReputation[node],
            block.timestamp
        ));
        
        require(!processedCrossChainActions[syncHash], "Sync already processed");
        processedCrossChainActions[syncHash] = true;
        
        emit CrossChainReputationSync(node, targetChainId, nodeReputation[node], syncHash, block.timestamp);
    }

    function registerNodeFromChain(
        address node,
        uint256 sourceChainId,
        Role role,
        NodeType nodeType,
        bool verified
    ) public virtual {
        bytes32 registrationHash = keccak256(abi.encodePacked(
            node,
            sourceChainId,
            block.chainid,
            role,
            nodeType
        ));
        
        require(!processedCrossChainActions[registrationHash], "Registration already processed");
        processedCrossChainActions[registrationHash] = true;
        
        if (nodeRegistrationChain[node] == 0) {
            nodeRegistrationChain[node] = sourceChainId;
        }
        
        _verifiedNodes[node] = verified;
        roles[node] = role;
        nodeTypes[node] = nodeType;
        
        bool found = false;
        for (uint256 i = 0; i < allNodes.length; i++) {
            if (allNodes[i] == node) {
                found = true;
                break;
            }
        }
        if (!found) {
            allNodes.push(node);
        }
        
        emit CrossChainNodeRegistration(node, sourceChainId, role, nodeType, block.timestamp);
    }

    // --- View Functions ---
    function isVerified(address node) public virtual view returns (bool) {
        return _verifiedNodes[node];
    }

    function isPrimaryNode(address node) internal virtual view returns (bool) {
        return _verifiedNodes[node] && nodeTypes[node] == NodeType.Primary;
    }

    function isSecondaryNode(address node) internal virtual view returns (bool) {
        return _verifiedNodes[node] && nodeTypes[node] == NodeType.Secondary;
    }

    function getAllVerifiedNodes() public view returns (address[] memory) {
        address[] memory verifiedNodesList = new address[](allNodes.length);
        uint256 idx = 0;
        for (uint256 i = 0; i < allNodes.length; i++) {
            if (_verifiedNodes[allNodes[i]]) {
                verifiedNodesList[idx] = allNodes[i];
                idx++;
            }
        }
        return verifiedNodesList;
    }

    function getNodeReputationOnChain(address node, uint256 chainId) public view returns (uint256) {
        return crossChainReputation[node][chainId];
    }

    function getTotalCrossChainReputation(address node) public view returns (uint256) {
        // This could aggregate reputation across all chains or use a weighted average
        // For simplicity, we'll return the current chain reputation
        return nodeReputation[node];
    }
}