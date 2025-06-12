"""
Cross-Chain Token Bridge Service using LayerZero OFT
Implements real ETH transfers between chains without token conversions
Hub coordinates the process but doesn't hold tokens
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from web3 import Web3
from eth_account import Account
from app.core.config import get_settings
from app.core.database import get_database

settings = get_settings()

# WETH Contract ABI (for deposit/withdraw functions)
WETH_ABI = [
    {
        "constant": False,
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# LayerZero OFT (Omnichain Fungible Token) Contract ABI
LAYERZERO_OFT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "_from", "type": "address"},
            {"internalType": "uint16", "name": "_dstChainId", "type": "uint16"},
            {"internalType": "bytes32", "name": "_toAddress", "type": "bytes32"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "address payable", "name": "_refundAddress", "type": "address"},
            {"internalType": "address", "name": "_zroPaymentAddress", "type": "address"},
            {"internalType": "bytes", "name": "_adapterParams", "type": "bytes"}
        ],
        "name": "sendFrom",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint16", "name": "_dstChainId", "type": "uint16"},
            {"internalType": "bytes32", "name": "_toAddress", "type": "bytes32"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "bool", "name": "_useZro", "type": "bool"},
            {"internalType": "bytes", "name": "_adapterParams", "type": "bytes"}
        ],
        "name": "estimateSendFee",
        "outputs": [
            {"internalType": "uint256", "name": "nativeFee", "type": "uint256"},
            {"internalType": "uint256", "name": "zroFee", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# LayerZero Chain IDs (different from normal chain IDs)
LAYERZERO_CHAIN_IDS = {
    "optimism_sepolia": 10132,    # Optimism Sepolia
    "polygon_pos": 10109,         # Polygon Amoy  
    "base_sepolia": 10245,        # Base Sepolia
    "arbitrum_sepolia": 10231     # Arbitrum Sepolia
}

class TokenBridgeService:
    def __init__(self):
        self.database = None
        
        # Multi-chain Web3 connections
        self.optimism_web3: Optional[Web3] = None
        self.polygon_web3: Optional[Web3] = None
        self.zkevm_web3: Optional[Web3] = None
        self.arbitrum_web3: Optional[Web3] = None
        
        # WETH OFT Contract Addresses (deployed on 2025-06-10)
        self.weth_oft_contracts = {
            "optimism_sepolia": "0x8AfF7B758eC0f57FfC4b08Dd91589832b8DF4d78",  # Real deployed contract
            "polygon_pos": "0x778Ccc71741a1e3F455E0e82b6BF3C583E62bfb0",      # Real deployed contract
            "base_sepolia": "0x0000000000000000000000000000000000000000",    # To be deployed
            "arbitrum_sepolia": "0x33d62824787BCD38c4738AC5B5d962d30C80F91a"  # Real deployed contract
        }
        
        # Contract instances
        self.weth_oft_optimism = None
        self.weth_oft_polygon = None
        self.weth_oft_zkevm = None
        self.weth_oft_arbitrum = None
        
        # Account for signing transactions
        self.current_account = None
        
    async def initialize(self):
        """Initialize token bridge service with real WETH OFT contracts"""
        self.database = await get_database()
        
        # Initialize account
        from app.services.multi_account_manager import address_key_manager
        deployer_account_info = address_key_manager.get_account_info_for_address('0x032041b4b356fEE1496805DD4749f181bC736FFA')
        if deployer_account_info:
            self.current_account = deployer_account_info['account']
            print(f"🔑 Token Bridge using account: {self.current_account.address}")
        
        # Initialize chain connections
        await self._initialize_chain_connections()
        
        # Initialize WETH OFT contracts
        await self._initialize_weth_oft_contracts()
        
        print("✅ Token Bridge Service initialized with REAL LayerZero OFT contracts")
        print(f"   📄 Optimism: {self.weth_oft_contracts['optimism_sepolia']}")
        print(f"   📄 Polygon: {self.weth_oft_contracts['polygon_pos']}")
        print(f"   📄 Base Sepolia: {self.weth_oft_contracts['base_sepolia']}")
        print(f"   📄 Arbitrum: {self.weth_oft_contracts['arbitrum_sepolia']}")
    
    async def _initialize_chain_connections(self):
        """Initialize Web3 connections to all chains"""
        
        # Optimism Sepolia (Buyer Chain)
        if settings.optimism_sepolia_rpc:
            self.optimism_web3 = Web3(Web3.HTTPProvider(settings.optimism_sepolia_rpc))
            if self.optimism_web3.is_connected():
                print(f"✅ Token Bridge connected to Optimism Sepolia")
                
        # Polygon PoS (Hub Chain)
        if settings.polygon_pos_rpc:
            self.polygon_web3 = Web3(Web3.HTTPProvider(settings.polygon_pos_rpc))
            if self.polygon_web3.is_connected():
                print(f"✅ Token Bridge connected to Polygon PoS Hub")
                
        # Base Sepolia (Manufacturer Chain)
        if settings.base_sepolia_rpc:
            self.base_sepolia_web3 = Web3(Web3.HTTPProvider(settings.base_sepolia_rpc))
            if self.base_sepolia_web3.is_connected():
                print(f"✅ Token Bridge connected to Base Sepolia")
                
        # Arbitrum Sepolia (Transporter Chain)
        if settings.arbitrum_sepolia_rpc:
            self.arbitrum_web3 = Web3(Web3.HTTPProvider(settings.arbitrum_sepolia_rpc))
            if self.arbitrum_web3.is_connected():
                print(f"✅ Token Bridge connected to Arbitrum Sepolia")
    
    async def _initialize_weth_oft_contracts(self):
        """Initialize WETH OFT contract instances with REAL deployed contracts"""
        
        print("✅ Initializing REAL WETH OFT contracts...")
        
        # Initialize contract instances with real addresses
        try:
            if self.optimism_web3:
                self.weth_oft_optimism = self.optimism_web3.eth.contract(
                    address=self.weth_oft_contracts["optimism_sepolia"],
                    abi=LAYERZERO_OFT_ABI
                )
                print(f"✅ Optimism WETH OFT contract initialized")
                
            if self.polygon_web3:
                self.weth_oft_polygon = self.polygon_web3.eth.contract(
                    address=self.weth_oft_contracts["polygon_pos"],
                    abi=LAYERZERO_OFT_ABI
                )
                print(f"✅ Polygon WETH OFT contract initialized")
                
            if self.base_sepolia_web3:
                self.weth_oft_base = self.base_sepolia_web3.eth.contract(
                    address=self.weth_oft_contracts["base_sepolia"],
                    abi=LAYERZERO_OFT_ABI
                )
                print(f"✅ Base Sepolia WETH OFT contract initialized")
                
            if self.arbitrum_web3:
                self.weth_oft_arbitrum = self.arbitrum_web3.eth.contract(
                    address=self.weth_oft_contracts["arbitrum_sepolia"],
                    abi=LAYERZERO_OFT_ABI
                )
                print(f"✅ Arbitrum WETH OFT contract initialized")
                
        except Exception as e:
            print(f"⚠️ Contract initialization warning: {e}")
        
        print("🎉 WETH OFT contracts ready for real token transfers")
        
    def get_layerzero_chain_id(self, chain_name: str) -> int:
        """Get LayerZero chain ID for a given chain"""
        return LAYERZERO_CHAIN_IDS.get(chain_name, 0)
    
    def get_web3_for_chain(self, chain_name: str) -> Optional[Web3]:
        """Get Web3 instance for a given chain"""
        chain_map = {
            "optimism_sepolia": self.optimism_web3,
            "polygon_pos": self.polygon_web3,
            "base_sepolia": self.base_sepolia_web3,
            "arbitrum_sepolia": self.arbitrum_web3
        }
        return chain_map.get(chain_name)
    
    def get_oft_contract_for_chain(self, chain_name: str):
        """Get OFT contract instance for a given chain"""
        contract_map = {
            "optimism_sepolia": self.weth_oft_optimism,
            "polygon_pos": self.weth_oft_polygon,
            "base_sepolia": self.weth_oft_base,
            "arbitrum_sepolia": self.weth_oft_arbitrum
        }
        return contract_map.get(chain_name)
    
    async def transfer_eth_cross_chain(
        self, 
        from_chain: str, 
        to_chain: str, 
        from_address: str, 
        to_address: str, 
        amount_eth: float,
        escrow_id: str
    ) -> Dict[str, Any]:
        """
        Execute real cross-chain ETH transfer using LayerZero OFT
        
        Args:
            from_chain: Source chain name (e.g. "optimism_sepolia")
            to_chain: Destination chain name (e.g. "base_sepolia") 
            from_address: Sender address
            to_address: Recipient address
            amount_eth: Amount in ETH to transfer
            escrow_id: Associated escrow ID for tracking
        """
        try:
            print(f"🌉 Cross-Chain ETH Transfer Initiated")
            print(f"   📤 From: {from_chain} ({from_address})")
            print(f"   📥 To: {to_chain} ({to_address})")
            print(f"   💰 Amount: {amount_eth} ETH")
            
            # Get Web3 instances
            source_web3 = self.get_web3_for_chain(from_chain)
            target_web3 = self.get_web3_for_chain(to_chain)
            
            if not source_web3 or not target_web3:
                return {"success": False, "error": "Chain connection not available"}
            
            # Get LayerZero chain IDs
            source_lz_chain_id = self.get_layerzero_chain_id(from_chain)
            target_lz_chain_id = self.get_layerzero_chain_id(to_chain)
            
            if not source_lz_chain_id or not target_lz_chain_id:
                return {"success": False, "error": "LayerZero chain ID not configured"}
            
            # Get OFT contract for source chain
            oft_contract = self.get_oft_contract_for_chain(from_chain)
            if not oft_contract:
                return {"success": False, "error": f"OFT contract not available for {from_chain}"}
            
            # Convert amount to Wei
            amount_wei = int(amount_eth * 10**18)
            
            # Step 1: Wrap ETH to WETH on source chain (using OFT contract deposit)
            wrap_result = await self._wrap_eth_on_chain(source_web3, oft_contract, from_address, amount_wei, from_chain)
            if not wrap_result["success"]:
                return {"success": False, "error": f"ETH wrapping failed: {wrap_result['error']}"}
            
            # Step 2: Transfer WETH using LayerZero OFT
            transfer_result = await self._transfer_weth_via_layerzero(
                source_web3, oft_contract, target_lz_chain_id, from_address, to_address, amount_wei, from_chain
            )
            if not transfer_result["success"]:
                return {"success": False, "error": f"LayerZero transfer failed: {transfer_result['error']}"}
            
            # Step 3: Record transfer in database with pending status initially
            transfer_record = {
                "transfer_id": f"TRANSFER-{escrow_id}-{int(time.time())}",
                "escrow_id": escrow_id,
                "from_chain": from_chain,
                "to_chain": to_chain,
                "from_address": from_address,
                "to_address": to_address,
                "amount_eth": amount_eth,
                "amount_wei": amount_wei,
                "wrap_tx": wrap_result.get("transaction_hash"),
                "layerzero_tx": transfer_result.get("transaction_hash"),
                "status": "pending",  # Start as pending, will be updated when confirmed
                "timestamp": time.time(),
                "real_transfer": True,
                "confirmation_block": None,
                "gas_used_total": (wrap_result.get("gas_used", 0) + transfer_result.get("gas_used", 0))
            }
            
            await self.database.token_transfers.insert_one(transfer_record)
            
            # Start background task to monitor transaction status
            asyncio.create_task(self._monitor_transfer_status(transfer_record["transfer_id"], transfer_result.get("transaction_hash"), source_web3))
            
            print(f"✅ Cross-chain ETH transfer initiated successfully")
            print(f"   🔗 Wrap TX: {wrap_result.get('transaction_hash')}")
            print(f"   🔗 LayerZero TX: {transfer_result.get('transaction_hash')}")
            
            return {
                "success": True,
                "transfer_id": transfer_record["transfer_id"],
                "wrap_transaction_hash": wrap_result.get("transaction_hash"),
                "layerzero_transaction_hash": transfer_result.get("transaction_hash"),
                "amount_transferred": amount_eth,
                "gas_used": {
                    "wrap_gas": wrap_result.get("gas_used", 0),
                    "transfer_gas": transfer_result.get("gas_used", 0)
                }
            }
            
        except Exception as e:
            print(f"❌ Cross-chain transfer error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _wrap_eth_on_chain(self, web3: Web3, oft_contract, user_address: str, amount_wei: int, chain_name: str) -> Dict[str, Any]:
        """Wrap ETH to WETH using the OFT contract deposit function"""
        try:
            print(f"🔄 Wrapping {Web3.from_wei(amount_wei, 'ether')} ETH on {chain_name}")
            
            # Build WETH deposit transaction using OFT contract
            nonce = web3.eth.get_transaction_count(self.current_account.address)
            
            # Get chain ID for EIP-155 compliance
            chain_id = web3.eth.chain_id
            
            # Call the deposit function on the OFT contract
            transaction = oft_contract.functions.deposit().build_transaction({
                'from': self.current_account.address,
                'value': amount_wei,
                'gas': 100000,  # Sufficient gas for WETH deposit
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
                'chainId': chain_id
            })
            
            # Sign and send transaction
            signed_txn = web3.eth.account.sign_transaction(transaction, self.current_account.key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            print(f"⏳ Waiting for WETH wrap confirmation...")
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if tx_receipt.status == 1:
                print(f"✅ ETH wrapped successfully on {chain_name}")
                return {
                    "success": True,
                    "transaction_hash": tx_hash.hex(),
                    "gas_used": tx_receipt.gasUsed,
                    "block_number": tx_receipt.blockNumber
                }
            else:
                return {"success": False, "error": "WETH wrap transaction failed"}
                
        except Exception as e:
            print(f"❌ WETH wrapping error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _transfer_weth_via_layerzero(
        self, 
        source_web3: Web3, 
        oft_contract,
        target_lz_chain_id: int, 
        from_address: str, 
        to_address: str, 
        amount_wei: int,
        chain_name: str
    ) -> Dict[str, Any]:
        """Transfer WETH using LayerZero OFT"""
        try:
            print(f"🌉 LayerZero WETH transfer: {Web3.from_wei(amount_wei, 'ether')} WETH")
            print(f"   🎯 Target Chain ID: {target_lz_chain_id}")
            
            # Convert address to bytes32 for LayerZero
            to_address_bytes32 = Web3.to_bytes(hexstr=to_address).rjust(32, b'\x00')
            
            # Estimate LayerZero fees
            adapter_params = b''  # Default adapter params
            
            try:
                # Get estimated fee from the contract
                estimated_fees = oft_contract.functions.estimateSendFee(
                    target_lz_chain_id,
                    to_address_bytes32,
                    amount_wei,
                    False,  # useZro
                    adapter_params
                ).call()
                estimated_fee = estimated_fees[0]  # nativeFee
                print(f"   💰 Estimated LayerZero fee: {Web3.from_wei(estimated_fee, 'ether')} ETH")
            except Exception as e:
                print(f"⚠️ Fee estimation failed, using default: {e}")
                estimated_fee = Web3.to_wei(0.01, 'ether')  # Fallback fee
            
            # Build LayerZero OFT sendFrom transaction
            nonce = source_web3.eth.get_transaction_count(self.current_account.address)
            
            # Get chain ID for EIP-155 compliance
            chain_id = source_web3.eth.chain_id
            
            transaction = oft_contract.functions.sendFrom(
                self.current_account.address,  # _from
                target_lz_chain_id,           # _dstChainId
                to_address_bytes32,           # _toAddress
                amount_wei,                   # _amount
                self.current_account.address, # _refundAddress
                "0x0000000000000000000000000000000000000000",  # _zroPaymentAddress (none)
                adapter_params                # _adapterParams
            ).build_transaction({
                'from': self.current_account.address,
                'value': estimated_fee,  # LayerZero fee
                'gas': 500000,          # Sufficient gas for LayerZero transfer
                'gasPrice': source_web3.eth.gas_price,
                'nonce': nonce,
                'chainId': chain_id
            })
            
            # Sign and send transaction
            signed_txn = source_web3.eth.account.sign_transaction(transaction, self.current_account.key)
            tx_hash = source_web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            print(f"⏳ Waiting for LayerZero transfer confirmation...")
            tx_receipt = source_web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if tx_receipt.status == 1:
                print(f"✅ LayerZero WETH transfer initiated successfully")
                print(f"   🔗 TX Hash: {tx_hash.hex()}")
                print(f"   ⛽ Gas Used: {tx_receipt.gasUsed}")
                
                return {
                    "success": True,
                    "transaction_hash": tx_hash.hex(),
                    "gas_used": tx_receipt.gasUsed,
                    "block_number": tx_receipt.blockNumber,
                    "layerzero_fee": Web3.from_wei(estimated_fee, 'ether')
                }
            else:
                return {"success": False, "error": "LayerZero transfer transaction failed"}
                
        except Exception as e:
            print(f"❌ LayerZero transfer error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _monitor_transfer_status(self, transfer_id: str, tx_hash: str, web3: Web3):
        """Monitor transaction status and update database when confirmed"""
        try:
            print(f"🔍 Monitoring transfer {transfer_id[:16]}... status")
            
            # Wait for multiple confirmations
            confirmation_blocks = 3
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt.status == 1:
                # Wait for additional confirmations
                current_block = web3.eth.block_number
                target_block = tx_receipt.blockNumber + confirmation_blocks
                
                while current_block < target_block:
                    await asyncio.sleep(10)  # Wait 10 seconds
                    current_block = web3.eth.block_number
                
                # Update transfer status to completed
                await self.database.token_transfers.update_one(
                    {"transfer_id": transfer_id},
                    {
                        "$set": {
                            "status": "completed",
                            "confirmation_block": current_block,
                            "confirmed_at": time.time()
                        }
                    }
                )
                
                print(f"✅ Transfer {transfer_id[:16]}... confirmed and completed")
            else:
                # Mark as failed
                await self.database.token_transfers.update_one(
                    {"transfer_id": transfer_id},
                    {
                        "$set": {
                            "status": "failed",
                            "failure_reason": "Transaction failed on-chain"
                        }
                    }
                )
                print(f"❌ Transfer {transfer_id[:16]}... failed")
                
        except Exception as e:
            print(f"⚠️ Transfer monitoring error for {transfer_id[:16]}...: {e}")
            # Mark as failed due to monitoring error
            await self.database.token_transfers.update_one(
                {"transfer_id": transfer_id},
                {
                    "$set": {
                        "status": "failed",
                        "failure_reason": f"Monitoring error: {str(e)}"
                    }
                }
            )
    
    async def get_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Get status of a cross-chain transfer"""
        try:
            transfer = await self.database.token_transfers.find_one({"transfer_id": transfer_id})
            if not transfer:
                return {"success": False, "error": "Transfer not found"}
            
            return {
                "success": True,
                "transfer": transfer,
                "status": transfer.get("status", "unknown"),
                "completion_time": transfer.get("confirmed_at") or transfer.get("timestamp")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_balance_on_chain(self, chain_name: str, address: str) -> Dict[str, Any]:
        """Get ETH and WETH balance for an address on a specific chain"""
        try:
            web3 = self.get_web3_for_chain(chain_name)
            if not web3:
                return {"success": False, "error": "Chain not connected"}
            
            # Get native ETH balance
            eth_balance_wei = web3.eth.get_balance(address)
            eth_balance = float(Web3.from_wei(eth_balance_wei, 'ether'))
            
            # Get WETH balance from OFT contract
            weth_balance = 0.0
            try:
                oft_contract = self.get_oft_contract_for_chain(chain_name)
                if oft_contract:
                    weth_balance_wei = oft_contract.functions.balanceOf(address).call()
                    weth_balance = float(Web3.from_wei(weth_balance_wei, 'ether'))
            except Exception as e:
                print(f"⚠️ WETH balance check failed for {chain_name}: {e}")
            
            return {
                "success": True,
                "chain": chain_name,
                "address": address,
                "eth_balance": eth_balance,
                "weth_balance": weth_balance,
                "total_balance": eth_balance + weth_balance
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global service instance
token_bridge_service = TokenBridgeService()
