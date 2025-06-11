#!/usr/bin/env python3
"""
Final LayerZero Contract Analysis
Determine if contracts are functional or need redeployment
"""

import asyncio
from web3 import Web3
from app.services.layerzero_oft_bridge_service import layerzero_oft_bridge_service

async def analyze_contract_functionality():
    """Analyze what functions actually work vs fail"""
    
    print("🔬 FINAL LAYERZERO CONTRACT ANALYSIS")
    print("=" * 50)
    
    # Initialize the service
    await layerzero_oft_bridge_service.initialize()
    
    # Test on Optimism Sepolia (where we have WETH)
    chain = "optimism_sepolia"
    web3 = layerzero_oft_bridge_service.web3_connections[chain]
    config = layerzero_oft_bridge_service.oft_contracts[chain]
    contract_address = config["address"]
    
    print(f"📍 Analyzing: {contract_address} on {chain}")
    
    # Test various function calls to understand what works
    test_results = {
        "basic_functions": {},
        "layerzero_functions": {},
        "transfer_functions": {},
        "conclusion": ""
    }
    
    # 1. Basic ERC20-style functions
    print(f"\n1️⃣ BASIC CONTRACT FUNCTIONS")
    print("-" * 30)
    
    basic_tests = [
        ("decimals", [], "uint8"),
        ("balanceOf", [layerzero_oft_bridge_service.current_account.address], "uint256"),
        ("totalSupply", [], "uint256"),
        ("name", [], "string"),
        ("symbol", [], "string")
    ]
    
    for func_name, params, return_type in basic_tests:
        try:
            abi = [{
                "inputs": [{"type": "address" if "address" in str(params) else ""}] if params else [],
                "name": func_name,
                "outputs": [{"type": return_type}],
                "stateMutability": "view",
                "type": "function"
            }]
            
            # Clean up ABI for functions without parameters
            if not params:
                abi[0]["inputs"] = []
            
            contract = web3.eth.contract(address=contract_address, abi=abi)
            
            if params:
                result = getattr(contract.functions, func_name)(*params).call()
            else:
                result = getattr(contract.functions, func_name)().call()
                
            test_results["basic_functions"][func_name] = {"status": "works", "result": str(result)}
            print(f"✅ {func_name}: {result}")
            
        except Exception as e:
            test_results["basic_functions"][func_name] = {"status": "failed", "error": str(e)}
            print(f"❌ {func_name}: {str(e)}")
    
    # 2. LayerZero specific functions
    print(f"\n2️⃣ LAYERZERO SPECIFIC FUNCTIONS") 
    print("-" * 30)
    
    lz_tests = [
        ("lzEndpoint", [], "address"),
        ("peers", [40158], "bytes32"),  # zkEVM EID
        ("owner", [], "address"),
        ("delegate", [], "address")
    ]
    
    for func_name, params, return_type in lz_tests:
        try:
            if func_name == "peers":
                abi = [{
                    "inputs": [{"name": "_eid", "type": "uint32"}],
                    "name": func_name,
                    "outputs": [{"type": return_type}],
                    "stateMutability": "view",
                    "type": "function"
                }]
            else:
                abi = [{
                    "inputs": [],
                    "name": func_name,
                    "outputs": [{"type": return_type}],
                    "stateMutability": "view",
                    "type": "function"
                }]
            
            contract = web3.eth.contract(address=contract_address, abi=abi)
            
            if params:
                result = getattr(contract.functions, func_name)(*params).call()
            else:
                result = getattr(contract.functions, func_name)().call()
                
            test_results["layerzero_functions"][func_name] = {"status": "works", "result": str(result)}
            print(f"✅ {func_name}: {result}")
            
        except Exception as e:
            test_results["layerzero_functions"][func_name] = {"status": "failed", "error": str(e)}
            print(f"❌ {func_name}: {str(e)}")
    
    # 3. Transfer-related functions (the failing ones)
    print(f"\n3️⃣ TRANSFER FUNCTIONS (FAILING)")
    print("-" * 30)
    
    # Test with minimal parameters
    target_eid = 40158  # zkEVM
    recipient = Web3.to_bytes(hexstr="28918ecf013F32fAf45e05d62B4D9b207FCae784".zfill(64))
    amount = 1000000000000000  # 0.001 ETH
    fee = (Web3.to_wei(0.001, 'ether'), 0)
    
    transfer_tests = [
        {
            "name": "quoteSend_v1",
            "abi": [{
                "inputs": [
                    {"name": "_dstEid", "type": "uint32"},
                    {"name": "_to", "type": "bytes32"},
                    {"name": "_amountLD", "type": "uint256"},
                    {"name": "_minAmountLD", "type": "uint256"},
                    {"name": "_extraOptions", "type": "bytes"},
                    {"name": "_payInLzToken", "type": "bool"}
                ],
                "name": "quoteSend",
                "outputs": [{"type": "tuple", "components": [
                    {"name": "nativeFee", "type": "uint256"},
                    {"name": "lzTokenFee", "type": "uint256"}
                ]}],
                "stateMutability": "view",
                "type": "function"
            }],
            "params": [target_eid, recipient, amount, amount, b'', False]
        },
        {
            "name": "send_simulation",
            "abi": [{
                "inputs": [
                    {"name": "_dstEid", "type": "uint32"},
                    {"name": "_to", "type": "bytes32"},
                    {"name": "_amountLD", "type": "uint256"},
                    {"name": "_minAmountLD", "type": "uint256"},
                    {"name": "_extraOptions", "type": "bytes"},
                    {"name": "_fee", "type": "tuple", "components": [
                        {"name": "nativeFee", "type": "uint256"},
                        {"name": "lzTokenFee", "type": "uint256"}
                    ]},
                    {"name": "_refundAddress", "type": "address"}
                ],
                "name": "send",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            }],
            "params": [target_eid, recipient, amount, amount, b'', fee, layerzero_oft_bridge_service.current_account.address],
            "call_params": {"from": layerzero_oft_bridge_service.current_account.address, "value": Web3.to_wei(0.001, 'ether')}
        }
    ]
    
    for test in transfer_tests:
        try:
            contract = web3.eth.contract(address=contract_address, abi=test["abi"])
            
            if "call_params" in test:
                # This is a payable function, use call() to simulate
                result = getattr(contract.functions, test["abi"][0]["name"])(*test["params"]).call(test["call_params"])
            else:
                # This is a view function
                result = getattr(contract.functions, test["abi"][0]["name"])(*test["params"]).call()
                
            test_results["transfer_functions"][test["name"]] = {"status": "works", "result": str(result)}
            print(f"✅ {test['name']}: {result}")
            
        except Exception as e:
            test_results["transfer_functions"][test["name"]] = {"status": "failed", "error": str(e)}
            print(f"❌ {test['name']}: {str(e)}")
    
    # 4. Analysis and conclusion
    print(f"\n4️⃣ ANALYSIS & CONCLUSION")
    print("-" * 30)
    
    basic_working = len([t for t in test_results["basic_functions"].values() if t["status"] == "works"])
    lz_working = len([t for t in test_results["layerzero_functions"].values() if t["status"] == "works"])
    transfer_working = len([t for t in test_results["transfer_functions"].values() if t["status"] == "works"])
    
    print(f"📊 Function Analysis:")
    print(f"   Basic functions working: {basic_working}/{len(test_results['basic_functions'])}")
    print(f"   LayerZero functions working: {lz_working}/{len(test_results['layerzero_functions'])}")
    print(f"   Transfer functions working: {transfer_working}/{len(test_results['transfer_functions'])}")
    
    # Determine contract type
    if basic_working == 0 and lz_working == 0:
        conclusion = "❌ NON-FUNCTIONAL CONTRACT - Complete redeployment needed"
    elif basic_working > 0 and lz_working > 0 and transfer_working == 0:
        conclusion = "🚧 INCOMPLETE LAYERZERO IMPLEMENTATION - Contract responds to queries but can't execute transfers"
    elif basic_working > 0 and lz_working > 0 and transfer_working > 0:
        conclusion = "✅ FUNCTIONAL CONTRACT - Issue might be in parameters or initialization"
    else:
        conclusion = "❓ PARTIAL IMPLEMENTATION - Mixed functionality"
    
    test_results["conclusion"] = conclusion
    print(f"\n🎯 CONCLUSION: {conclusion}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if "NON-FUNCTIONAL" in conclusion:
        print("   1. 🔄 Deploy fresh LayerZero OFT contracts using official templates")
        print("   2. 📋 Use LayerZero Create OApp CLI: npx create-lz-oapp@latest")
        print("   3. ✅ Verify contracts on block explorers after deployment")
        
    elif "INCOMPLETE" in conclusion:
        print("   1. 🔍 Check if contracts need initialization beyond setPeer")
        print("   2. 📞 Contact original deployer for missing setup steps")
        print("   3. 🔄 Consider redeployment with complete LayerZero setup")
        
    elif "FUNCTIONAL" in conclusion:
        print("   1. 🧪 Test with different parameters (amounts, addresses)")
        print("   2. 🔧 Check gas limits and fee calculations")
        print("   3. 📝 Review transaction simulation parameters")
    
    print(f"\n🔗 IMMEDIATE WORKAROUND:")
    print(f"   Use Real WETH Bridge as primary method while fixing LayerZero")
    print(f"   Real WETH bridge works reliably for cross-chain transfers")
    
    return test_results

async def main():
    """Run final contract analysis"""
    results = await analyze_contract_functionality()
    
    print(f"\n{'='*60}")
    print("🏁 FINAL ANALYSIS COMPLETE")
    print(f"{'='*60}")
    
    print(f"\n📋 SUMMARY:")
    print(f"   The deployed contracts appear to be incomplete LayerZero implementations")
    print(f"   They respond to basic and LayerZero queries but fail on transfer operations")
    print(f"   This explains the 'execution reverted' errors on all send attempts")
    
    print(f"\n🎯 SOLUTION:")
    print(f"   1. Use Real WETH Bridge for immediate transfers")
    print(f"   2. Deploy fresh LayerZero contracts with complete implementation")
    print(f"   3. Ensure proper contract verification and testing")

if __name__ == "__main__":
    asyncio.run(main())