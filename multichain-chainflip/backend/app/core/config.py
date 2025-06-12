"""
Configuration settings for ChainFLIP Multi-Chain Backend
"""
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "chainflip_multichain")
    
    # Blockchain Networks - Updated Multi-chain Architecture
    polygon_pos_rpc: str = os.getenv("POLYGON_POS_RPC", "https://rpc-amoy.polygon.technology")
    polygon_pos_chain_id: int = int(os.getenv("POLYGON_POS_CHAIN_ID", "80002"))
    polygon_pos_rpc_fallback: str = os.getenv("POLYGON_POS_RPC_FALLBACK", "https://polygon-amoy.g.alchemy.com/v2/demo")
    
    # Cross-chain Network Mappings - Base Sepolia replaces zkEVM Cardona
    base_sepolia_rpc: str = os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org")
    base_sepolia_chain_id: int = int(os.getenv("BASE_SEPOLIA_CHAIN_ID", "84532"))
    base_sepolia_rpc_fallback: str = os.getenv("BASE_SEPOLIA_RPC_FALLBACK", "https://base-sepolia.drpc.org")
    
    arbitrum_sepolia_rpc: str = os.getenv("ARBITRUM_SEPOLIA_RPC", "https://sepolia-rollup.arbitrum.io/rpc") 
    arbitrum_sepolia_chain_id: int = int(os.getenv("ARBITRUM_SEPOLIA_CHAIN_ID", "421614"))
    arbitrum_sepolia_rpc_fallback: str = os.getenv("ARBITRUM_SEPOLIA_RPC_FALLBACK", "https://arbitrum-sepolia.drpc.org")
    
    optimism_sepolia_rpc: str = os.getenv("OPTIMISM_SEPOLIA_RPC", "https://sepolia.optimism.io")
    optimism_sepolia_chain_id: int = int(os.getenv("OPTIMISM_SEPOLIA_CHAIN_ID", "11155420"))
    optimism_sepolia_rpc_fallback: str = os.getenv("OPTIMISM_SEPOLIA_RPC_FALLBACK", "https://optimism-sepolia.drpc.org")
    
    # Role-based Access Control - Updated to Base Sepolia
    manufacturer_role_required: bool = os.getenv("MANUFACTURER_ROLE_REQUIRED", "true").lower() == "true"
    manufacturer_chain_id: int = int(os.getenv("MANUFACTURER_CHAIN_ID", "84532"))  # Base Sepolia
    enable_role_verification: bool = os.getenv("ENABLE_ROLE_VERIFICATION", "true").lower() == "true"
    
    # QR Code Encryption Keys
    qr_aes_key: str = os.getenv("QR_AES_KEY", "")
    qr_hmac_key: str = os.getenv("QR_HMAC_KEY", "")
    
    # Legacy L2 CDK (for backward compatibility)
    l2_cdk_rpc: str = os.getenv("L2_CDK_RPC", "")
    l2_cdk_chain_id: int = int(os.getenv("L2_CDK_CHAIN_ID", "0"))
    
    # Private Keys - Address-to-PrivateKey mapping (no role restrictions)
    deployer_private_key: str = os.getenv("DEPLOYER_PRIVATE_KEY", "")
    
    # Address-to-PrivateKey mapping for all 11 accounts
    def get_private_key_for_address(self, address: str) -> Optional[str]:
        """Get private key for any address"""
        env_key = f"ACCOUNT_{address}"
        return os.getenv(env_key, "")
    
    # Contract Addresses - Multi-Chain Architecture
    # Hub Contract (Polygon PoS)
    hub_contract: str = os.getenv("HUB_CONTRACT_ADDRESS", "0x45A2C5B59272dcC9b427926DCd6079B52D4335C8")
    pos_hub_contract: str = os.getenv("POS_HUB_CONTRACT", "0x45A2C5B59272dcC9b427926DCd6079B52D4335C8")  # Legacy support
    
    # L2 Specialized Contracts - Real Deployed Addresses
    manufacturer_contract_address: str = os.getenv("MANUFACTURER_CONTRACT_ADDRESS", "0x4806bdE2D69Af285759e913DA9A4322F876ACE4d")
    transporter_contract_address: str = os.getenv("TRANSPORTER_CONTRACT_ADDRESS", "0x5D9E723dC9f8A54a3904aaCF188893fb67d582a9")
    buyer_contract_address: str = os.getenv("BUYER_CONTRACT_ADDRESS", "0x4806bdE2D69Af285759e913DA9A4322F876ACE4d")
    
    # Legacy contracts (for backward compatibility)
    nft_core_contract: str = os.getenv("NFT_CORE_CONTRACT", "")
    supply_chain_nft_contract: str = os.getenv("SUPPLY_CHAIN_NFT_CONTRACT", "")
    node_management_contract: str = os.getenv("NODE_MANAGEMENT_CONTRACT", "")
    batch_processing_contract: str = os.getenv("BATCH_PROCESSING_CONTRACT", "")
    dispute_resolution_contract: str = os.getenv("DISPUTE_RESOLUTION_CONTRACT", "")
    marketplace_contract: str = os.getenv("MARKETPLACE_CONTRACT", "")
    
    # Bridge and Cross-chain - Updated with real deployed addresses
    bridge_layerzero_hub: str = os.getenv("BRIDGE_LAYERZERO_HUB", "0x72a336eAAC8186906F1Ee85dF00C7d6b91257A43")
    bridge_fxportal_hub: str = os.getenv("BRIDGE_FXPORTAL_HUB", "0xd3c6396D0212Edd8424bd6544E7DF8BA74c16476")
    bridge_crosschain_messenger: str = os.getenv("BRIDGE_CROSSCHAIN_MESSENGER", "0x04C881aaE303091Bda3e06731f6fa565A929F983")
    bridge_optimism_layerzero: str = os.getenv("BRIDGE_OPTIMISM_LAYERZERO", "0xA4f7a7A48cC8C16D35c7F6944E7610694F5BEB26")
    bridge_arbitrum_layerzero: str = os.getenv("BRIDGE_ARBITRUM_LAYERZERO", "0x217e72E43e9375c1121ca36dcAc3fe878901836D")
    
    # LayerZero OFT Contracts (Separated Architecture) - Updated with Base Sepolia
    chainflip_oft_optimism_sepolia: str = os.getenv("CHAINFLIP_OFT_OPTIMISM_SEPOLIA", "0x6478eAB366A16d96ae910fd16F6770DDa1845648")
    chainflip_oft_arbitrum_sepolia: str = os.getenv("CHAINFLIP_OFT_ARBITRUM_SEPOLIA", "0x441C06d8548De93d64072F781e15E16A7c316b67")
    chainflip_oft_amoy: str = os.getenv("CHAINFLIP_OFT_AMOY", "0x865F1Dac1d8E17f492FFce578095b49f3D604ad4")
    chainflip_oft_base_sepolia: str = os.getenv("CHAINFLIP_OFT_BASE_SEPOLIA", "0x0000000000000000000000000000000000000000")
    ethwrapper_optimism_sepolia: str = os.getenv("ETHWRAPPER_OPTIMISM_SEPOLIA", "0x5428793EBd36693c993D6B3f8f2641C46121ec29")
    ethwrapper_arbitrum_sepolia: str = os.getenv("ETHWRAPPER_ARBITRUM_SEPOLIA", "0x5952569276eA7f7eF95B910EAd0a67067A518188")
    ethwrapper_amoy: str = os.getenv("ETHWRAPPER_AMOY", "0xA471c665263928021AF5aa7852724b6f757005e1")
    ethwrapper_base_sepolia: str = os.getenv("ETHWRAPPER_BASE_SEPOLIA", "0x0000000000000000000000000000000000000000")
    
    # Legacy bridge settings
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
