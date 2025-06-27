"""
Ownership Verification Service
Enhanced service to verify product ownership across multiple chains and handle cross-chain transfers
"""

import time
from typing import Dict, List, Any, Optional
from web3 import Web3


class OwnershipVerificationService:
    """
    Service to verify product ownership across multiple chains
    Handles scenarios where:
    1. Products are owned locally (database current_owner)
    2. Products are transferred cross-chain (same CID, different token_id)
    3. On-chain verification is needed for accuracy
    """
    
    def __init__(self, database, web3_connections: Dict, contract_addresses: Dict):
        self.database = database
        self.web3_connections = web3_connections
        self.contract_addresses = contract_addresses
        
        # Standard NFT ABI for ownerOf and tokenURI functions
        self.nft_abi = [
            {
                "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
                "name": "ownerOf",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
                "name": "tokenURI", 
                "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    async def get_owned_products_for_buyer(self, buyer_address: str, verify_on_chain: bool = False) -> List[Dict[str, Any]]:
        """
        Get all products owned by a buyer
        
        Args:
            buyer_address: The buyer's wallet address
            verify_on_chain: Whether to verify ownership on-chain (slower but more accurate)
            
        Returns:
            List of products owned by the buyer
        """
        try:
            print(f"🔍 Finding owned products for buyer {buyer_address}")
            
            # Step 1: Get products from database where current_owner matches
            db_owned_products = []
            cursor = self.database.products.find({"current_owner": buyer_address})
            async for product in cursor:
                product["_id"] = str(product["_id"])
                product["verification_method"] = "database"
                db_owned_products.append(product)
            
            print(f"📊 Found {len(db_owned_products)} products in database")
            
            # Step 2: If on-chain verification is requested, check blockchain
            if verify_on_chain:
                on_chain_products = await self._verify_on_chain_ownership(buyer_address, db_owned_products)
                
                # Merge results and mark verification status
                for product in db_owned_products:
                    cid = product.get("cid") or product.get("image_cid")
                    if cid:
                        on_chain_match = any(p.get("cid") == cid for p in on_chain_products)
                        product["on_chain_verified"] = on_chain_match
                        if on_chain_match:
                            product["verification_method"] = "database_and_blockchain"
                    else:
                        product["on_chain_verified"] = False
                        
                return db_owned_products
            else:
                # Return database results with verification flag
                for product in db_owned_products:
                    product["on_chain_verified"] = None  # Not checked
                return db_owned_products
                
        except Exception as e:
            print(f"❌ Error getting owned products: {e}")
            return []
    
    async def _verify_on_chain_ownership(self, buyer_address: str, db_products: List[Dict]) -> List[Dict[str, Any]]:
        """
        Verify on-chain ownership for products
        This is useful for cross-chain scenarios where CID is the same but token_id changes
        """
        verified_products = []
        
        try:
            # Check each supported chain
            chains_to_check = ["optimism_sepolia", "polygon_amoy", "base_sepolia", "arbitrum_sepolia"]
            
            for chain_name in chains_to_check:
                web3_conn = self.web3_connections.get(chain_name)
                contract_addr = self.contract_addresses.get(chain_name)
                
                if not web3_conn or not contract_addr:
                    continue
                    
                print(f"🔍 Checking {chain_name} for owned NFTs...")
                
                try:
                    # Create contract instance
                    nft_contract = web3_conn.eth.contract(
                        address=contract_addr,
                        abi=self.nft_abi
                    )
                    
                    # Get total supply to know how many tokens to check
                    total_supply = nft_contract.functions.totalSupply().call()
                    print(f"📊 {chain_name} total supply: {total_supply}")
                    
                    # Check ownership for each token (this is expensive, so we limit it)
                    max_tokens_to_check = min(total_supply, 100)  # Limit for performance
                    
                    for token_id in range(1, max_tokens_to_check + 1):
                        try:
                            owner = nft_contract.functions.ownerOf(token_id).call()
                            
                            if owner.lower() == buyer_address.lower():
                                # Get token URI to find CID
                                token_uri = nft_contract.functions.tokenURI(token_id).call()
                                
                                # Extract CID from token URI
                                cid = self._extract_cid_from_uri(token_uri)
                                
                                if cid:
                                    verified_products.append({
                                        "chain": chain_name,
                                        "token_id": token_id,
                                        "owner": owner,
                                        "cid": cid,
                                        "token_uri": token_uri,
                                        "verification_method": "blockchain"
                                    })
                                    print(f"✅ Found owned NFT on {chain_name}: token {token_id}, CID {cid}")
                                    
                        except Exception as token_error:
                            # Token might not exist or other error, continue
                            continue
                            
                except Exception as chain_error:
                    print(f"⚠️ Error checking {chain_name}: {chain_error}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error in on-chain verification: {e}")
            
        return verified_products
    
    def _extract_cid_from_uri(self, token_uri: str) -> Optional[str]:
        """Extract CID from token URI"""
        try:
            if "ipfs://" in token_uri:
                return token_uri.replace("ipfs://", "").split("/")[0]
            elif ".ipfs." in token_uri:
                # Handle gateway URLs like https://bafybei....ipfs.dweb.link/metadata.json
                parts = token_uri.split(".ipfs.")
                if len(parts) > 0:
                    cid_part = parts[0].split("/")[-1]
                    return cid_part
            return None
        except Exception as e:
            print(f"⚠️ Error extracting CID from URI {token_uri}: {e}")
            return None
    
    async def update_product_ownership(self, product_id: str, new_owner: str, chain: str = None, token_id: str = None) -> bool:
        """
        Update product ownership in database
        Called after successful cross-chain transfers
        """
        try:
            update_data = {
                "current_owner": new_owner,
                "last_updated": time.time(),
                "ownership_updated_at": time.time()
            }
            
            if chain:
                update_data["current_chain"] = chain
                
            if token_id:
                update_data["current_token_id"] = token_id
            
            result = await self.database.products.update_one(
                {"token_id": product_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print(f"✅ Updated ownership for product {product_id} to {new_owner}")
                return True
            else:
                print(f"⚠️ No product found with token_id {product_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating product ownership: {e}")
            return False
    
    async def verify_single_product_ownership(self, product_id: str, claimed_owner: str, verify_on_chain: bool = True) -> Dict[str, Any]:
        """
        Verify ownership of a single product
        """
        try:
            # Get product from database
            product = await self.database.products.find_one({"token_id": product_id})
            if not product:
                return {"verified": False, "error": "Product not found"}
            
            db_owner = product.get("current_owner")
            db_match = db_owner and db_owner.lower() == claimed_owner.lower()
            
            result = {
                "product_id": product_id,
                "claimed_owner": claimed_owner,
                "database_owner": db_owner,
                "database_match": db_match,
                "verified": db_match
            }
            
            if verify_on_chain and db_match:
                # Additional on-chain verification for high-value operations
                cid = product.get("cid") or product.get("image_cid")
                if cid:
                    on_chain_products = await self._verify_on_chain_ownership(claimed_owner, [product])
                    on_chain_match = any(p.get("cid") == cid for p in on_chain_products)
                    result["on_chain_verified"] = on_chain_match
                    result["verified"] = db_match and on_chain_match
                else:
                    result["on_chain_verified"] = None
                    result["error"] = "No CID available for on-chain verification"
            
            return result
            
        except Exception as e:
            return {"verified": False, "error": f"Verification error: {e}"}
