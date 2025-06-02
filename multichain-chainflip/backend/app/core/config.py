"""
Configuration settings for ChainFLIP Multi-Chain Backend
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "chainflip_multichain")
    
    # Blockchain Networks
    polygon_pos_rpc: str = os.getenv("POLYGON_POS_RPC", "https://polygon-amoy.drpc.org")
    polygon_pos_chain_id: int = int(os.getenv("POLYGON_POS_CHAIN_ID", "80002"))
    
    l2_cdk_rpc: str = os.getenv("L2_CDK_RPC", "")
    l2_cdk_chain_id: int = int(os.getenv("L2_CDK_CHAIN_ID", "0"))
    
    # Private Keys
    deployer_private_key: str = os.getenv("DEPLOYER_PRIVATE_KEY", "")
    operator_private_key: str = os.getenv("OPERATOR_PRIVATE_KEY", "")
    
    # Contract Addresses - Multi-Chain Architecture
    # Hub Contract (Polygon PoS)
    hub_contract: str = os.getenv("HUB_CONTRACT_ADDRESS", "")
    pos_hub_contract: str = os.getenv("POS_HUB_CONTRACT", "")  # Legacy support
    
    # L2 Specialized Contracts
    manufacturer_contract: str = os.getenv("MANUFACTURER_CONTRACT_ADDRESS", "")
    transporter_contract: str = os.getenv("TRANSPORTER_CONTRACT_ADDRESS", "")
    buyer_contract: str = os.getenv("BUYER_CONTRACT_ADDRESS", "")
    
    # Legacy contracts (for backward compatibility)
    nft_core_contract: str = os.getenv("NFT_CORE_CONTRACT", "")
    supply_chain_nft_contract: str = os.getenv("SUPPLY_CHAIN_NFT_CONTRACT", "")
    node_management_contract: str = os.getenv("NODE_MANAGEMENT_CONTRACT", "")
    batch_processing_contract: str = os.getenv("BATCH_PROCESSING_CONTRACT", "")
    dispute_resolution_contract: str = os.getenv("DISPUTE_RESOLUTION_CONTRACT", "")
    marketplace_contract: str = os.getenv("MARKETPLACE_CONTRACT", "")
    
    # Bridge and Cross-chain
    bridge_contract: str = os.getenv("BRIDGE_CONTRACT", "")
    l2_participant_contract: str = os.getenv("L2_PARTICIPANT_CONTRACT", "")
    
    # IPFS/Web3.Storage
    w3storage_token: str = os.getenv("W3STORAGE_TOKEN", "")
    w3storage_proof: str = os.getenv("W3STORAGE_PROOF", "")
    ipfs_gateway: str = os.getenv("IPFS_GATEWAY", "https://w3s.link/ipfs/")
    
    # Federated Learning
    fl_model_storage: str = os.getenv("FL_MODEL_STORAGE", "./fl_models")
    fl_aggregation_threshold: int = int(os.getenv("FL_AGGREGATION_THRESHOLD", "3"))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "chainflip-multichain-secret-key")
    aes_secret_key: str = os.getenv("AES_SECRET_KEY", "")
    hmac_secret_key: str = os.getenv("HMAC_SECRET_KEY", "")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis for caching and messaging
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    model_config = {"env_file": ".env", "extra": "allow"}

@lru_cache()
def get_settings():
    return Settings()
