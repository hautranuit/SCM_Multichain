"""
Contract ABIs for ChainFLIP Multi-Chain Real Contract Integration
Extracted from the Solidity contract files
"""

# LayerZero Config Contract ABI - For cross-chain messaging
LAYERZERO_CONFIG_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "targetChainId", "type": "uint256"},
            {"internalType": "enum LayerZeroConfig.MessageType", "name": "msgType", "type": "uint8"},
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "bytes", "name": "payload", "type": "bytes"}
        ],
        "name": "sendMessage",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "targetChainId", "type": "uint256"},
            {"internalType": "bytes", "name": "payload", "type": "bytes"},
            {"internalType": "bool", "name": "useZro", "type": "bool"},
            {"internalType": "bytes", "name": "adapterParams", "type": "bytes"}
        ],
        "name": "estimateFee",
        "outputs": [
            {"internalType": "uint256", "name": "nativeFee", "type": "uint256"},
            {"internalType": "uint256", "name": "zroFee", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "chainId", "type": "uint256"}
        ],
        "name": "getLzChainId",
        "outputs": [
            {"internalType": "uint16", "name": "", "type": "uint16"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint16", "name": "dstChainId", "type": "uint16"},
            {"indexed": True, "internalType": "bytes", "name": "dstAddress", "type": "bytes"},
            {"indexed": False, "internalType": "uint256", "name": "nonce", "type": "uint256"},
            {"indexed": False, "internalType": "bytes", "name": "payload", "type": "bytes"}
        ],
        "name": "MessageSent",
        "type": "event"
    }
]

# FxPortal Bridge Contract ABI - For Polygon ecosystem communication
FXPORTAL_BRIDGE_ABI = [
    {
        "inputs": [
            {"internalType": "enum FxPortalBridge.MessageType", "name": "msgType", "type": "uint8"},
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "bytes", "name": "payload", "type": "bytes"}
        ],
        "name": "sendMessageToChild",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "messageHash", "type": "bytes32"}
        ],
        "name": "getMessage",
        "outputs": [
            {
                "components": [
                    {"internalType": "enum FxPortalBridge.MessageType", "name": "msgType", "type": "uint8"},
                    {"internalType": "uint256", "name": "sourceChain", "type": "uint256"},
                    {"internalType": "uint256", "name": "targetChain", "type": "uint256"},
                    {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
                    {"internalType": "bytes", "name": "payload", "type": "bytes"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                    {"internalType": "uint256", "name": "stateId", "type": "uint256"}
                ],
                "internalType": "struct FxPortalBridge.FxMessage",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "receiver", "type": "address"},
            {"indexed": True, "internalType": "bytes32", "name": "messageHash", "type": "bytes32"},
            {"indexed": False, "internalType": "bytes", "name": "data", "type": "bytes"}
        ],
        "name": "MessageSentToChild",
        "type": "event"
    }
]

# Enhanced Hub Contract ABI - Main hub functionality
ENHANCED_HUB_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "productTokenId", "type": "uint256"},
            {"internalType": "address", "name": "manufacturer", "type": "address"},
            {"internalType": "string", "name": "metadataCID", "type": "string"},
            {"internalType": "uint256", "name": "manufacturerChainId", "type": "uint256"},
            {"internalType": "bytes32", "name": "manufacturerHash", "type": "bytes32"}
        ],
        "name": "registerProductFromChain",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "enum EnhancedPolygonPoSHub.ProductStatus", "name": "newStatus", "type": "uint8"},
            {"internalType": "bytes32", "name": "verificationHash", "type": "bytes32"}
        ],
        "name": "updateProductStatus",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "sourceChain", "type": "uint256"},
            {"internalType": "uint256", "name": "targetChain", "type": "uint256"},
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "enum EnhancedPolygonPoSHub.TransactionType", "name": "txType", "type": "uint8"}
        ],
        "name": "createCrossChainTransaction",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "getProduct",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
                    {"internalType": "address", "name": "manufacturer", "type": "address"},
                    {"internalType": "string", "name": "metadataCID", "type": "string"},
                    {"internalType": "uint256", "name": "createdAt", "type": "uint256"},
                    {"internalType": "address", "name": "currentOwner", "type": "address"},
                    {"internalType": "enum EnhancedPolygonPoSHub.ProductStatus", "name": "status", "type": "uint8"},
                    {"internalType": "bool", "name": "isActive", "type": "bool"},
                    {"internalType": "uint256", "name": "manufacturerChainId", "type": "uint256"},
                    {"internalType": "bytes32", "name": "manufacturerHash", "type": "bytes32"},
                    {"internalType": "bool", "name": "qualityApproved", "type": "bool"}
                ],
                "internalType": "struct EnhancedPolygonPoSHub.Product",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Buyer Chain Contract ABI - For purchase operations
BUYER_CHAIN_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "productTokenId", "type": "uint256"},
            {"internalType": "bytes32", "name": "productHash", "type": "bytes32"},
            {"internalType": "uint256", "name": "price", "type": "uint256"},
            {"internalType": "string", "name": "productDescription", "type": "string"},
            {"internalType": "string", "name": "metadataCID", "type": "string"},
            {"internalType": "enum BuyerChain.MarketplaceCategory", "name": "category", "type": "uint8"}
        ],
        "name": "createMarketplaceListing",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "listingId", "type": "uint256"},
            {"internalType": "string", "name": "deliveryLocation", "type": "string"}
        ],
        "name": "createPurchase",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "purchaseId", "type": "uint256"}
        ],
        "name": "confirmDelivery",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "purchaseId", "type": "uint256"}
        ],
        "name": "getPurchase",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "purchaseId", "type": "uint256"},
                    {"internalType": "uint256", "name": "productTokenId", "type": "uint256"},
                    {"internalType": "bytes32", "name": "productHash", "type": "bytes32"},
                    {"internalType": "bytes32", "name": "shipmentHash", "type": "bytes32"},
                    {"internalType": "address", "name": "buyer", "type": "address"},
                    {"internalType": "address", "name": "seller", "type": "address"},
                    {"internalType": "uint256", "name": "price", "type": "uint256"},
                    {"internalType": "uint256", "name": "collateral", "type": "uint256"},
                    {"internalType": "enum BuyerChain.PurchaseStatus", "name": "status", "type": "uint8"},
                    {"internalType": "uint256", "name": "purchaseTime", "type": "uint256"},
                    {"internalType": "uint256", "name": "deliveryTime", "type": "uint256"},
                    {"internalType": "uint256", "name": "confirmationDeadline", "type": "uint256"},
                    {"internalType": "bool", "name": "paymentReleased", "type": "bool"},
                    {"internalType": "string", "name": "deliveryLocation", "type": "string"},
                    {"internalType": "bytes32", "name": "crossChainHash", "type": "bytes32"}
                ],
                "internalType": "struct BuyerChain.Purchase",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "purchaseId", "type": "uint256"},
            {"indexed": True, "internalType": "uint256", "name": "productTokenId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "buyer", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "seller", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "price", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "PurchaseCreated",
        "type": "event"
    }
]

# Message Types for cross-chain communication
class MessageType:
    # LayerZero Message Types
    PRODUCT_SYNC = 0
    SHIPMENT_UPDATE = 1
    PURCHASE_UPDATE = 2
    FL_MODEL_UPDATE = 3
    REPUTATION_UPDATE = 4
    
    # FxPortal Message Types  
    PRODUCT_REGISTRATION = 0
    QUALITY_APPROVAL = 1
    MANUFACTURING_UPDATE = 2
    FL_MODEL_SYNC = 3
    INCENTIVE_UPDATE = 4

# Transaction Types for hub
class TransactionType:
    PRODUCT_TRANSFER = 0
    SHIPMENT_UPDATE = 1
    PAYMENT_RELEASE = 2
    DISPUTE_SYNC = 3
    FL_MODEL_UPDATE = 4

# Product Status enum
class ProductStatus:
    MANUFACTURED = 0
    QUALITY_APPROVED = 1
    LISTED = 2
    SOLD = 3
    IN_TRANSIT = 4
    DELIVERED = 5
    COMPLETED = 6

# Purchase Status enum
class PurchaseStatus:
    CREATED = 0
    PAID = 1
    IN_TRANSIT = 2
    DELIVERED = 3
    CONFIRMED = 4
    DISPUTED = 5
    COMPLETED = 6
    REFUNDED = 7

# Marketplace Category enum
class MarketplaceCategory:
    ELECTRONICS = 0
    CLOTHING = 1
    FOOD = 2
    MEDICINE = 3
    OTHER = 4