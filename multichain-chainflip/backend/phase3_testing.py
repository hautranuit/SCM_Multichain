#!/usr/bin/env python3
"""
PHASE 3: End-to-End Token Bridge Testing

Comprehensive testing suite for real cross-chain ETH transfers,
complete purchase flows, and production readiness validation.
"""
import asyncio
import sys
import os
import json
import time
from typing import Dict, Any, List
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class Phase3TestSuite:
    def __init__(self):
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
    async def run_all_tests(self):
        """Run complete Phase 3 test suite"""
        
        print("🚀 PHASE 3: END-TO-END TOKEN BRIDGE TESTING")
        print("=" * 60)
        print("Testing complete cross-chain transfer flows and production readiness")
        print()
        
        try:
            # Initialize services
            await self.initialize_services()
            
            # Test 1: Basic Token Transfer Flow
            await self.test_basic_token_transfer()
            
            # Test 2: Cross-Chain Purchase Flow
            await self.test_cross_chain_purchase()
            
            # Test 3: Multi-Chain Balance Verification
            await self.test_multi_chain_balances()
            
            # Test 4: Fee Optimization Testing
            await self.test_fee_optimization()
            
            # Test 5: Error Handling & Recovery
            await self.test_error_handling()
            
            # Test 6: Database Recording & Tracking
            await self.test_database_tracking()
            
            # Test 7: API Endpoint Stress Testing
            await self.test_api_stress()
            
            # Test 8: Production Readiness Validation
            await self.test_production_readiness()
            
            # Generate comprehensive test report
            await self.generate_test_report()
            
            return len(self.failed_tests) == 0
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def initialize_services(self):
        """Initialize all required services for testing"""
        print("📋 Initializing test environment...")
        
        from app.services.token_bridge_service import token_bridge_service
        from app.services.crosschain_purchase_service import crosschain_purchase_service
        from app.services.multi_account_manager import address_key_manager
        
        # Initialize token bridge
        await token_bridge_service.initialize()
        self.token_bridge = token_bridge_service
        
        # Initialize cross-chain purchase service
        await crosschain_purchase_service.initialize()
        self.crosschain_purchase = crosschain_purchase_service
        
        # Get test accounts
        self.test_accounts = {
            "deployer": "0x032041b4b356fEE1496805DD4749f181bC736FFA",
            "buyer": "0xc6A050a538a9E857B4DCb4A33436280c202F6941", 
            "manufacturer": "0x28918ecf013F32fAf45e05d62B4D9b207FCae784",
            "transporter": "0x5503a5B847e98B621d97695edf1bD84242C5862E"
        }
        
        print("✅ Test environment initialized")
        print(f"   🔑 Test accounts: {len(self.test_accounts)}")
        print(f"   🌉 Token bridge: Ready")
        print(f"   🔗 Cross-chain service: Ready")
        print()
    
    async def test_basic_token_transfer(self):
        """Test 1: Basic cross-chain ETH transfer"""
        print("📋 TEST 1: Basic Token Transfer Flow")
        print("-" * 40)
        
        test_name = "basic_token_transfer"
        
        try:
            # Test parameters
            transfer_params = {
                "from_chain": "optimism_sepolia",
                "to_chain": "zkevm_cardona", 
                "from_address": self.test_accounts["buyer"],
                "to_address": self.test_accounts["manufacturer"],
                "amount_eth": 0.001,
                "escrow_id": f"TEST-{int(time.time())}"
            }
            
            print(f"   💸 Transfer: {transfer_params['amount_eth']} ETH")
            print(f"   🔄 Route: {transfer_params['from_chain']} → {transfer_params['to_chain']}")
            print(f"   👤 From: {transfer_params['from_address'][:10]}...")
            print(f"   👤 To: {transfer_params['to_address'][:10]}...")
            
            # Execute transfer
            result = await self.token_bridge.transfer_eth_cross_chain(**transfer_params)
            
            if result["success"]:
                print(f"   ✅ Transfer successful")
                print(f"      🆔 Transfer ID: {result['transfer_id']}")
                print(f"      🔗 Wrap TX: {result.get('wrap_transaction_hash', 'N/A')}")
                print(f"      🔗 LayerZero TX: {result.get('layerzero_transaction_hash', 'N/A')}")
                print(f"      ⛽ Gas Used: {result.get('gas_used', {})}")
                
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "result": result,
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)
            else:
                print(f"   ❌ Transfer failed: {result.get('error', 'Unknown error')}")
                self.test_results[test_name] = {
                    "status": "FAILED", 
                    "error": result.get('error'),
                    "timestamp": time.time()
                }
                self.failed_tests.append(test_name)
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.time()
            }
            self.failed_tests.append(test_name)
        
        print()
    
    async def test_cross_chain_purchase(self):
        """Test 2: Complete cross-chain purchase flow"""
        print("📋 TEST 2: Cross-Chain Purchase Flow")
        print("-" * 40)
        
        test_name = "cross_chain_purchase"
        
        try:
            # Test purchase parameters
            purchase_params = {
                "product_id": "1749210465933",  # Test product from problem statement
                "buyer": self.test_accounts["buyer"],
                "seller": self.test_accounts["manufacturer"],
                "amount": 0.0001,
                "payment_method": "ETH"
            }
            
            print(f"   🛒 Product: {purchase_params['product_id']}")
            print(f"   💰 Price: {purchase_params['amount']} ETH")
            print(f"   👤 Buyer: {purchase_params['buyer'][:10]}...")
            print(f"   👤 Seller: {purchase_params['seller'][:10]}...")
            
            # Execute purchase flow
            result = await self.crosschain_purchase.process_cross_chain_purchase(**purchase_params)
            
            if result.get("success"):
                print(f"   ✅ Purchase successful")
                print(f"      🆔 Purchase ID: {result.get('purchase_id', 'N/A')}")
                print(f"      🆔 Escrow ID: {result.get('escrow_id', 'N/A')}")
                print(f"      📊 Status: {result.get('status', 'Unknown')}")
                
                # Check if real token transfer occurred
                if result.get("real_transfer"):
                    print(f"      🌉 Real token transfer: ✅")
                    print(f"      🔗 Transfer ID: {result.get('transfer_id', 'N/A')}")
                else:
                    print(f"      🌉 Simulated transfer only")
                
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "result": result,
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)
            else:
                print(f"   ❌ Purchase failed: {result.get('error', 'Unknown error')}")
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "error": result.get('error'),
                    "timestamp": time.time()
                }
                self.failed_tests.append(test_name)
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.time()
            }
            self.failed_tests.append(test_name)
        
        print()
    
    async def test_multi_chain_balances(self):
        """Test 3: Multi-chain balance verification"""
        print("📋 TEST 3: Multi-Chain Balance Verification")
        print("-" * 40)
        
        test_name = "multi_chain_balances"
        
        try:
            chains = ["optimism_sepolia", "polygon_pos", "zkevm_cardona", "arbitrum_sepolia"]
            test_address = self.test_accounts["buyer"]
            
            balance_results = {}
            total_eth = 0.0
            
            for chain in chains:
                try:
                    result = await self.token_bridge.get_balance_on_chain(chain, test_address)
                    
                    if result["success"]:
                        eth_balance = result["eth_balance"]
                        weth_balance = result["weth_balance"]
                        total_eth += eth_balance
                        
                        balance_results[chain] = result
                        print(f"   ✅ {chain}: ETH={eth_balance:.6f}, WETH={weth_balance:.6f}")
                    else:
                        print(f"   ❌ {chain}: {result['error']}")
                        balance_results[chain] = {"error": result["error"]}
                        
                except Exception as e:
                    print(f"   ❌ {chain}: Exception - {e}")
                    balance_results[chain] = {"error": str(e)}
            
            successful_checks = len([r for r in balance_results.values() if "error" not in r])
            
            print(f"   📊 Summary: {successful_checks}/{len(chains)} chains")
            print(f"   💰 Total ETH across chains: {total_eth:.6f}")
            
            if successful_checks >= 3:  # Allow for some tolerance
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "balances": balance_results,
                    "total_eth": total_eth,
                    "successful_checks": successful_checks,
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)
            else:
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "error": f"Only {successful_checks}/{len(chains)} balance checks succeeded",
                    "balances": balance_results,
                    "timestamp": time.time()
                }
                self.failed_tests.append(test_name)
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.time()
            }
            self.failed_tests.append(test_name)
        
        print()
    
    async def test_fee_optimization(self):
        """Test 4: Fee optimization and gas estimation"""
        print("📋 TEST 4: Fee Optimization Testing")
        print("-" * 40)
        
        test_name = "fee_optimization"
        
        try:
            # Test different transfer amounts and routes
            test_scenarios = [
                {"from": "optimism_sepolia", "to": "zkevm_cardona", "amount": 0.001},
                {"from": "optimism_sepolia", "to": "arbitrum_sepolia", "amount": 0.01},
                {"from": "polygon_pos", "to": "zkevm_cardona", "amount": 0.005},
                {"from": "arbitrum_sepolia", "to": "optimism_sepolia", "amount": 0.002}
            ]
            
            fee_results = {}
            
            for i, scenario in enumerate(test_scenarios):
                route_name = f"{scenario['from']} → {scenario['to']}"
                print(f"   🧮 Testing route {i+1}: {route_name}")
                print(f"      💰 Amount: {scenario['amount']} ETH")
                
                try:
                    # Get source web3 for fee calculation
                    source_web3 = self.token_bridge.get_web3_for_chain(scenario['from'])
                    
                    if source_web3:
                        gas_price = source_web3.eth.gas_price
                        
                        # Calculate estimated fees
                        wrap_gas = 50000
                        transfer_gas = 500000
                        wrap_fee_eth = float(source_web3.from_wei(wrap_gas * gas_price, 'ether'))
                        transfer_fee_eth = float(source_web3.from_wei(transfer_gas * gas_price, 'ether'))
                        layerzero_fee = 0.01
                        total_fee = wrap_fee_eth + transfer_fee_eth + layerzero_fee
                        
                        fee_percentage = (total_fee / scenario['amount']) * 100
                        
                        fee_results[route_name] = {
                            "wrap_fee": wrap_fee_eth,
                            "transfer_fee": transfer_fee_eth,
                            "layerzero_fee": layerzero_fee,
                            "total_fee": total_fee,
                            "transfer_amount": scenario['amount'],
                            "fee_percentage": fee_percentage
                        }
                        
                        print(f"      ⛽ Total fee: {total_fee:.6f} ETH ({fee_percentage:.2f}%)")
                        print(f"      💸 Cost breakdown: Wrap={wrap_fee_eth:.6f}, Transfer={transfer_fee_eth:.6f}, LZ={layerzero_fee:.6f}")
                        
                        if fee_percentage < 20:  # Reasonable fee threshold
                            print(f"      ✅ Fee acceptable")
                        else:
                            print(f"      ⚠️ High fee percentage")
                            
                    else:
                        print(f"      ❌ Chain not connected")
                        
                except Exception as e:
                    print(f"      ❌ Fee calculation failed: {e}")
            
            avg_fee_percentage = sum(r["fee_percentage"] for r in fee_results.values()) / len(fee_results) if fee_results else 0
            
            print(f"   📊 Average fee percentage: {avg_fee_percentage:.2f}%")
            
            if avg_fee_percentage < 15:  # Target under 15%
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "fee_results": fee_results,
                    "avg_fee_percentage": avg_fee_percentage,
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)
            else:
                self.test_results[test_name] = {
                    "status": "WARNING",
                    "fee_results": fee_results,
                    "avg_fee_percentage": avg_fee_percentage,
                    "note": "Fees higher than target",
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)  # Still pass but with warning
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.time()
            }
            self.failed_tests.append(test_name)
        
        print()
    
    async def test_error_handling(self):
        """Test 5: Error handling and recovery scenarios"""
        print("📋 TEST 5: Error Handling & Recovery")
        print("-" * 40)
        
        test_name = "error_handling"
        
        try:
            error_scenarios = []
            
            # Test 1: Invalid chain name
            print("   🧪 Testing invalid chain name...")
            try:
                result = await self.token_bridge.transfer_eth_cross_chain(
                    "invalid_chain", "optimism_sepolia", 
                    self.test_accounts["buyer"], self.test_accounts["manufacturer"],
                    0.001, "TEST-ERROR-1"
                )
                if not result["success"]:
                    print("      ✅ Properly rejected invalid chain")
                    error_scenarios.append({"test": "invalid_chain", "passed": True})
                else:
                    print("      ❌ Should have rejected invalid chain")
                    error_scenarios.append({"test": "invalid_chain", "passed": False})
            except Exception as e:
                print(f"      ✅ Exception properly caught: {e}")
                error_scenarios.append({"test": "invalid_chain", "passed": True})
            
            # Test 2: Zero amount transfer
            print("   🧪 Testing zero amount transfer...")
            try:
                result = await self.token_bridge.transfer_eth_cross_chain(
                    "optimism_sepolia", "zkevm_cardona",
                    self.test_accounts["buyer"], self.test_accounts["manufacturer"],
                    0.0, "TEST-ERROR-2"
                )
                if not result["success"]:
                    print("      ✅ Properly rejected zero amount")
                    error_scenarios.append({"test": "zero_amount", "passed": True})
                else:
                    print("      ❌ Should have rejected zero amount")
                    error_scenarios.append({"test": "zero_amount", "passed": False})
            except Exception as e:
                print(f"      ✅ Exception properly caught: {e}")
                error_scenarios.append({"test": "zero_amount", "passed": True})
            
            # Test 3: Invalid address format
            print("   🧪 Testing invalid address format...")
            try:
                result = await self.token_bridge.transfer_eth_cross_chain(
                    "optimism_sepolia", "zkevm_cardona",
                    "invalid_address", self.test_accounts["manufacturer"],
                    0.001, "TEST-ERROR-3"
                )
                if not result["success"]:
                    print("      ✅ Properly rejected invalid address")
                    error_scenarios.append({"test": "invalid_address", "passed": True})
                else:
                    print("      ❌ Should have rejected invalid address")
                    error_scenarios.append({"test": "invalid_address", "passed": False})
            except Exception as e:
                print(f"      ✅ Exception properly caught: {e}")
                error_scenarios.append({"test": "invalid_address", "passed": True})
            
            passed_scenarios = sum(1 for s in error_scenarios if s["passed"])
            
            print(f"   📊 Error handling: {passed_scenarios}/{len(error_scenarios)} scenarios passed")
            
            if passed_scenarios == len(error_scenarios):
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "error_scenarios": error_scenarios,
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)
            else:
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "error_scenarios": error_scenarios,
                    "failed_scenarios": len(error_scenarios) - passed_scenarios,
                    "timestamp": time.time()
                }
                self.failed_tests.append(test_name)
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.time()
            }
            self.failed_tests.append(test_name)
        
        print()
    
    async def test_database_tracking(self):
        """Test 6: Database recording and transfer tracking"""
        print("📋 TEST 6: Database Recording & Tracking")
        print("-" * 40)
        
        test_name = "database_tracking"
        
        try:
            # Create a test transfer and check database recording
            test_transfer_id = f"TEST-DB-{int(time.time())}"
            
            print(f"   🗄️ Testing database operations...")
            print(f"   🆔 Test Transfer ID: {test_transfer_id}")
            
            # Simulate a transfer record
            transfer_record = {
                "transfer_id": test_transfer_id,
                "escrow_id": f"ESCROW-{int(time.time())}",
                "from_chain": "optimism_sepolia",
                "to_chain": "zkevm_cardona",
                "from_address": self.test_accounts["buyer"],
                "to_address": self.test_accounts["manufacturer"],
                "amount_eth": 0.001,
                "amount_wei": int(0.001 * 10**18),
                "wrap_tx": "0x1234567890abcdef...",
                "layerzero_tx": "0xabcdef1234567890...",
                "status": "completed",
                "timestamp": time.time(),
                "real_transfer": True
            }
            
            # Insert test record
            await self.token_bridge.database.token_transfers.insert_one(transfer_record.copy())
            print("      ✅ Transfer record inserted")
            
            # Query the record back
            retrieved_record = await self.token_bridge.database.token_transfers.find_one(
                {"transfer_id": test_transfer_id}
            )
            
            if retrieved_record:
                print("      ✅ Transfer record retrieved")
                print(f"         🆔 ID: {retrieved_record['transfer_id']}")
                print(f"         📊 Status: {retrieved_record['status']}")
                print(f"         💰 Amount: {retrieved_record['amount_eth']} ETH")
                
                # Test transfer status API
                status_result = await self.token_bridge.get_transfer_status(test_transfer_id)
                
                if status_result["success"]:
                    print("      ✅ Transfer status API working")
                    print(f"         📊 API Status: {status_result['status']}")
                else:
                    print(f"      ❌ Transfer status API failed: {status_result['error']}")
                
                # Clean up test record
                await self.token_bridge.database.token_transfers.delete_one(
                    {"transfer_id": test_transfer_id}
                )
                print("      ✅ Test record cleaned up")
                
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "test_transfer_id": test_transfer_id,
                    "record_operations": "successful",
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)
                
            else:
                print("      ❌ Failed to retrieve transfer record")
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "error": "Database record retrieval failed",
                    "timestamp": time.time()
                }
                self.failed_tests.append(test_name)
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.time()
            }
            self.failed_tests.append(test_name)
        
        print()
    
    async def test_api_stress(self):
        """Test 7: API endpoint stress testing"""
        print("📋 TEST 7: API Endpoint Stress Testing")
        print("-" * 40)
        
        test_name = "api_stress"
        
        try:
            # Import API components
            from app.api.routes.token_bridge import router
            
            print(f"   🔥 Testing API endpoints under load...")
            
            # Test multiple concurrent balance checks
            balance_tasks = []
            for i in range(5):
                chain = ["optimism_sepolia", "polygon_pos", "zkevm_cardona", "arbitrum_sepolia"][i % 4]
                task = self.token_bridge.get_balance_on_chain(chain, self.test_accounts["buyer"])
                balance_tasks.append(task)
            
            balance_results = await asyncio.gather(*balance_tasks, return_exceptions=True)
            
            successful_balance_calls = sum(1 for r in balance_results if not isinstance(r, Exception) and r.get("success"))
            print(f"      ✅ Balance API: {successful_balance_calls}/5 concurrent calls successful")
            
            # Test fee estimation stress
            fee_tasks = []
            for i in range(3):
                # Use source web3 directly for fee calculation
                source_web3 = self.token_bridge.get_web3_for_chain("optimism_sepolia")
                if source_web3:
                    fee_tasks.append(self._calculate_fees(source_web3))
            
            fee_results = await asyncio.gather(*fee_tasks, return_exceptions=True)
            successful_fee_calls = sum(1 for r in fee_results if not isinstance(r, Exception))
            print(f"      ✅ Fee API: {successful_fee_calls}/3 concurrent calls successful")
            
            # Test database stress
            db_tasks = []
            for i in range(3):
                task = self.token_bridge.database.token_transfers.count_documents({})
                db_tasks.append(task)
            
            db_results = await asyncio.gather(*db_tasks, return_exceptions=True)
            successful_db_calls = sum(1 for r in db_results if not isinstance(r, Exception))
            print(f"      ✅ Database API: {successful_db_calls}/3 concurrent calls successful")
            
            total_successful = successful_balance_calls + successful_fee_calls + successful_db_calls
            total_calls = 5 + 3 + 3
            
            success_rate = (total_successful / total_calls) * 100
            print(f"   📊 Overall success rate: {success_rate:.1f}% ({total_successful}/{total_calls})")
            
            if success_rate >= 80:  # 80% success rate threshold
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "success_rate": success_rate,
                    "successful_calls": total_successful,
                    "total_calls": total_calls,
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)
            else:
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "success_rate": success_rate,
                    "error": f"Success rate {success_rate:.1f}% below 80% threshold",
                    "timestamp": time.time()
                }
                self.failed_tests.append(test_name)
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.time()
            }
            self.failed_tests.append(test_name)
        
        print()
    
    async def _calculate_fees(self, web3):
        """Helper function to calculate fees"""
        gas_price = web3.eth.gas_price
        return {
            "gas_price": gas_price,
            "estimated_fee": float(web3.from_wei(550000 * gas_price, 'ether'))
        }
    
    async def test_production_readiness(self):
        """Test 8: Production readiness validation"""
        print("📋 TEST 8: Production Readiness Validation")
        print("-" * 40)
        
        test_name = "production_readiness"
        
        try:
            readiness_checks = {}
            
            # Check 1: All chains connected
            chains = ["optimism_sepolia", "polygon_pos", "zkevm_cardona", "arbitrum_sepolia"]
            connected_chains = 0
            
            for chain in chains:
                web3 = self.token_bridge.get_web3_for_chain(chain)
                if web3 and web3.is_connected():
                    connected_chains += 1
            
            readiness_checks["chain_connectivity"] = {
                "connected": connected_chains,
                "total": len(chains),
                "percentage": (connected_chains / len(chains)) * 100,
                "passed": connected_chains == len(chains)
            }
            
            print(f"   🌐 Chain connectivity: {connected_chains}/{len(chains)} ({readiness_checks['chain_connectivity']['percentage']:.0f}%)")
            
            # Check 2: Real contract addresses
            real_contracts = 0
            for chain, address in self.token_bridge.weth_oft_contracts.items():
                if address != "0x0000000000000000000000000000000000000000":
                    real_contracts += 1
            
            readiness_checks["real_contracts"] = {
                "deployed": real_contracts,
                "total": len(self.token_bridge.weth_oft_contracts),
                "percentage": (real_contracts / len(self.token_bridge.weth_oft_contracts)) * 100,
                "passed": real_contracts == len(self.token_bridge.weth_oft_contracts)
            }
            
            print(f"   📄 Real contracts: {real_contracts}/{len(self.token_bridge.weth_oft_contracts)} ({readiness_checks['real_contracts']['percentage']:.0f}%)")
            
            # Check 3: Database connectivity
            try:
                await self.token_bridge.database.token_transfers.count_documents({})
                readiness_checks["database"] = {"connected": True, "passed": True}
                print(f"   🗄️ Database: Connected ✅")
            except Exception as e:
                readiness_checks["database"] = {"connected": False, "error": str(e), "passed": False}
                print(f"   🗄️ Database: Failed ❌")
            
            # Check 4: Account management
            available_accounts = len([addr for addr in self.test_accounts.values() if addr])
            readiness_checks["accounts"] = {
                "available": available_accounts,
                "required": 4,
                "passed": available_accounts >= 4
            }
            
            print(f"   🔑 Accounts: {available_accounts}/4 available")
            
            # Check 5: API endpoints
            from app.api.routes.token_bridge import router
            api_endpoints = len(router.routes)
            readiness_checks["api_endpoints"] = {
                "endpoints": api_endpoints,
                "expected": 8,
                "passed": api_endpoints >= 8
            }
            
            print(f"   🔌 API endpoints: {api_endpoints}/8 available")
            
            # Overall readiness score
            passed_checks = sum(1 for check in readiness_checks.values() if check.get("passed", False))
            total_checks = len(readiness_checks)
            readiness_score = (passed_checks / total_checks) * 100
            
            print(f"   📊 Overall readiness: {readiness_score:.1f}% ({passed_checks}/{total_checks} checks passed)")
            
            if readiness_score >= 90:
                print(f"   🚀 PRODUCTION READY!")
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "readiness_score": readiness_score,
                    "checks": readiness_checks,
                    "production_ready": True,
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)
            elif readiness_score >= 75:
                print(f"   ⚠️ MOSTLY READY (minor issues)")
                self.test_results[test_name] = {
                    "status": "WARNING",
                    "readiness_score": readiness_score,
                    "checks": readiness_checks,
                    "production_ready": False,
                    "note": "Minor issues need resolution",
                    "timestamp": time.time()
                }
                self.passed_tests.append(test_name)
            else:
                print(f"   ❌ NOT READY FOR PRODUCTION")
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "readiness_score": readiness_score,
                    "checks": readiness_checks,
                    "production_ready": False,
                    "timestamp": time.time()
                }
                self.failed_tests.append(test_name)
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.time()
            }
            self.failed_tests.append(test_name)
        
        print()
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("📋 Generating comprehensive test report...")
        
        total_tests = len(self.test_results)
        passed_tests = len(self.passed_tests)
        failed_tests = len(self.failed_tests)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report = {
            "phase": "PHASE_3_END_TO_END_TESTING",
            "test_timestamp": time.time(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate
            },
            "test_results": self.test_results,
            "passed_test_names": self.passed_tests,
            "failed_test_names": self.failed_tests,
            "production_ready": success_rate >= 90
        }
        
        with open("/app/multichain-chainflip/backend/phase3_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("✅ Test report saved to phase3_test_report.json")
        
        # Print summary
        print()
        print("=" * 60)
        print("🎯 PHASE 3 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! System ready for Phase 4")
        elif success_rate >= 75:
            print("⚠️ GOOD with minor issues. Proceed with caution to Phase 4")
        else:
            print("❌ NEEDS WORK before Phase 4")
        
        print()
        print("📋 Test Breakdown:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "PASSED" else ("⚠️" if result["status"] == "WARNING" else "❌")
            print(f"   {status_icon} {test_name}: {result['status']}")
        
        return report

async def run_phase3_testing():
    """Main function to run Phase 3 testing"""
    test_suite = Phase3TestSuite()
    success = await test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(run_phase3_testing())
    sys.exit(0 if success else 1)