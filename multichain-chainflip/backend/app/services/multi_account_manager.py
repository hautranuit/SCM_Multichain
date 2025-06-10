"""
Address-to-PrivateKey Manager for ChainFLIP Cross-Chain Operations
Maps any address to its corresponding private key for transaction signing
No role restrictions - addresses can register for any role they want
"""
import os
from typing import Dict, Optional, Any
from eth_account import Account
from app.core.config import get_settings

settings = get_settings()

class AddressKeyManager:
    def __init__(self):
        self.address_to_key = {}
        self._initialize_address_mappings()
    
    def _initialize_address_mappings(self):
        """Initialize address-to-private-key mappings from environment"""
        
        # All available addresses and their private keys
        address_key_pairs = [
            ("0x032041b4b356fEE1496805DD4749f181bC736FFA", "5d014eee1544fe8e166b0ffc5d9a5da41456cec5d4c15b76611e8747d848f079"),
            ("0x04351e7dF40d04B5E610c4aA033faCf435b98711", "30d4efde8e871586f42f9564fddef62c3fa51025516dec865a8476041c7d963f"),
            ("0xc6A050a538a9E857B4DCb4A33436280c202F6941", "5e76179b71fb77d8820a8d5752fdc36974d464b2fe9df7798c9dddeb2002dc32"),
            ("0x5503a5B847e98B621d97695edf1bD84242C5862E", "1b217d4daf489e04ac8c2b88bf875784987f014a37f5e19e9e4a22cbb2b3696f"),
            ("0x34Fc023EE50781e0a007852eEDC4A17fa353a8cD", "a28abcf25ef9115241a8718d9c1b15936de534f8b88fbe7b707c101154d93e79"),
            ("0x724876f86fA52568aBc51955BD3A68bFc1441097", "7978d0b8c753b7e6d7e4b5f60e769a2591c68ae546bf015f1e36b777928129dd"),
            ("0x72EB9742d3B684ebA40F11573b733Ac9dB499f23", "740d83072c31361f2c9c1bbcc1b5bf8aa7baee28910020a06c3f791206f93f2b"),
            ("0x94081502540FD333075f3290d1D5C10A21AC5A5C", "67de5b3e68137bfbf13f1306d8bcc20706960497afe5e1546ed20317d825df0b"),
            ("0x7ca2dF29b5ea3BB9Ef3b4245D8b7c41a03318Fc1", "0769b82db47e64af8d80ab2ea9e6e8a16e00b9c20cc9c6dc1d91d8bb0ce2c8dd"),
            ("0x361d25a7F28F05dDE7a2cb191b4B8128EEE0fAB6", "1b7f24174a9648fab02e9d684e440de6328d067c60578427f2bb7adf95d751ec"),
            ("0x28918ecf013F32fAf45e05d62B4D9b207FCae784", "8fb67bbc36b6b1872c025cc13cd6c708a11fc6e9e2c9c4b9dbe98b1dff6ea0d5")
        ]
        
        for address, private_key in address_key_pairs:
            # Also check environment variable
            env_private_key = os.getenv(f"ACCOUNT_{address}", private_key)
            
            try:
                # Verify the private key matches the address
                account = Account.from_key(env_private_key)
                if account.address.lower() == address.lower():
                    self.address_to_key[address.lower()] = {
                        "address": address,
                        "private_key": env_private_key,
                        "account": account
                    }
                else:
                    print(f"⚠️ Private key mismatch for {address}")
            except Exception as e:
                print(f"❌ Failed to initialize account {address}: {e}")
        
        print(f"✅ Initialized {len(self.address_to_key)} address-to-key mappings")
    
    def get_private_key_for_address(self, address: str) -> Optional[str]:
        """Get private key for any address"""
        account_info = self.address_to_key.get(address.lower())
        return account_info["private_key"] if account_info else None
    
    def get_account_for_address(self, address: str) -> Optional[Account]:
        """Get Web3 Account object for any address"""
        account_info = self.address_to_key.get(address.lower())
        return account_info["account"] if account_info else None
    
    def has_private_key_for_address(self, address: str) -> bool:
        """Check if we have a private key for the given address"""
        return address.lower() in self.address_to_key
    
    def get_all_available_addresses(self) -> list:
        """Get all addresses we have private keys for"""
        return [info["address"] for info in self.address_to_key.values()]
    
    def get_account_info_for_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Get complete account info for an address"""
        return self.address_to_key.get(address.lower())

# Global instance
address_key_manager = AddressKeyManager()