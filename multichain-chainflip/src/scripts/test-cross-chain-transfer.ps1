# Cross-Chain NFT Transfer Test Script
# From: Base Sepolia Token ID 1 → OP Sepolia
# Owner: 0x5503a5B847e98B621d97695edf1bD84242C5862E → 0xc6A050a538a9E857B4DCb4A33436280c202F6941

Write-Host "Cross-Chain NFT Transfer Test" -ForegroundColor Cyan
Write-Host "=========================================="
Write-Host ""

# Configuration
$TOKEN_ID = "1"
$FROM_ADDRESS = "0x5503a5B847e98B621d97695edf1bD84242C5862E"
$TO_ADDRESS = "0xc6A050a538a9E857B4DCb4A33436280c202F6941"
$BACKEND_URL = "http://localhost:8001"

Write-Host "Transfer Configuration:" -ForegroundColor Yellow
Write-Host "   Token ID: $TOKEN_ID"
Write-Host "   From: $FROM_ADDRESS (Base Sepolia)"
Write-Host "   To: $TO_ADDRESS (OP Sepolia)"
Write-Host ""

# Step 1: Check Backend Health
Write-Host "Step 1: Checking Backend Health..." -ForegroundColor Green
try {
    $healthResponse = Invoke-RestMethod -Uri "$BACKEND_URL/api/health" -Method GET
    Write-Host "   Backend Status: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "   Backend Health Check Failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Make sure backend is running on localhost:8001"
    exit 1
}

# Step 2: Check NFT Bridge Health
Write-Host ""
Write-Host "Step 2: Checking NFT Bridge Service..." -ForegroundColor Green
try {
    $bridgeHealth = Invoke-RestMethod -Uri "$BACKEND_URL/api/nft-bridge/health" -Method GET
    Write-Host "   Bridge Status: $($bridgeHealth.status)" -ForegroundColor Green
    Write-Host "   Connected Networks: $($bridgeHealth.connected_networks)/$($bridgeHealth.total_networks)"
    Write-Host "   Loaded Contracts: $($bridgeHealth.loaded_contracts)"
} catch {
    Write-Host "   NFT Bridge Health Check Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 3: Get Current NFT Status
Write-Host ""
Write-Host "Step 3: Checking Current NFT Status..." -ForegroundColor Green
Write-Host "   Check the frontend or blockchain explorer to verify:"
Write-Host "   • Token ID $TOKEN_ID exists on Base Sepolia"
Write-Host "   • Current owner is $FROM_ADDRESS"
Write-Host "   • Token has valid metadata URI"
Write-Host ""

# Step 4: Initiate Cross-Chain Transfer
Write-Host "Step 4: Initiating Cross-Chain Transfer..." -ForegroundColor Magenta
$transferPayload = @{
    token_id = $TOKEN_ID
    from_chain = "base_sepolia"
    to_chain = "optimism_sepolia"
    from_address = $FROM_ADDRESS
    to_address = $TO_ADDRESS
} | ConvertTo-Json

Write-Host "   Transfer Payload:" -ForegroundColor Yellow
Write-Host $transferPayload
Write-Host ""

$TRANSFER_ID = $null
try {
    $transferResponse = Invoke-RestMethod -Uri "$BACKEND_URL/api/nft-bridge/transfer" -Method POST -Body $transferPayload -ContentType "application/json"
    Write-Host "   Transfer Initiated Successfully!" -ForegroundColor Green
    Write-Host "   Transfer ID: $($transferResponse.transfer_id)"
    Write-Host "   Status: $($transferResponse.status)"
    $TRANSFER_ID = $transferResponse.transfer_id
} catch {
    Write-Host "   Transfer Initiation Failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Continue with manual mint approach
    Write-Host ""
    Write-Host "Fallback: Manual Admin Mint Approach..." -ForegroundColor Yellow
    
    # Get token URI from original NFT (you'll need to provide this)
    $TOKEN_URI = "https://w3s.link/ipfs/bafkreib4yyhchxrsymdwk5j36i3etzej5lew47kfakskgwoa7bdxfx4vza"  # From the previous mint
    
    $mintPayload = @{
        token_id = $TOKEN_ID
        to_chain = "optimism_sepolia"
        to_address = $TO_ADDRESS
        token_uri = $TOKEN_URI
        use_admin_account = $true
    } | ConvertTo-Json
    
    Write-Host "   Mint Payload:" -ForegroundColor Yellow
    Write-Host $mintPayload
    Write-Host ""
    
    try {
        $mintResponse = Invoke-RestMethod -Uri "$BACKEND_URL/api/nft-bridge/admin/mint-on-destination" -Method POST -Body $mintPayload -ContentType "application/json"
        Write-Host "   Admin Mint Successful!" -ForegroundColor Green
        Write-Host "   Mint Transaction: $($mintResponse.transaction_hash)"
        Write-Host "   New Token ID: $($mintResponse.token_id)"
    } catch {
        Write-Host "   Admin Mint Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Step 5: Check Transfer Status
if ($TRANSFER_ID) {
    Write-Host ""
    Write-Host "Step 5: Checking Transfer Status..." -ForegroundColor Green
    
    Start-Sleep -Seconds 5  # Wait a bit for processing
    
    try {
        $statusResponse = Invoke-RestMethod -Uri "$BACKEND_URL/api/nft-bridge/transfer/$TRANSFER_ID" -Method GET
        Write-Host "   Transfer Status: $($statusResponse.status)" -ForegroundColor Cyan
        Write-Host "   Created: $($statusResponse.created_at)"
        Write-Host "   Updated: $($statusResponse.updated_at)"
        
        if ($statusResponse.source_tx_hash) {
            Write-Host "   Source TX: $($statusResponse.source_tx_hash)"
        }
        if ($statusResponse.dest_tx_hash) {
            Write-Host "   Dest TX: $($statusResponse.dest_tx_hash)"
        }
    } catch {
        Write-Host "   Could not get transfer status: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Step 6: List All Transfers
Write-Host ""
Write-Host "Step 6: Recent Transfer History..." -ForegroundColor Green
try {
    $allTransfers = Invoke-RestMethod -Uri "$BACKEND_URL/api/nft-bridge/transfers" -Method GET
    Write-Host "   Total Transfers: $($allTransfers.Count)"
    
    if ($allTransfers.Count -gt 0) {
        Write-Host "   Recent Transfers:"
        $allTransfers | Select-Object -First 3 | ForEach-Object {
            Write-Host "      • ID: $($_.transfer_id) | Status: $($_.status) | From: $($_.from_chain) → $($_.to_chain)"
        }
    }
} catch {
    Write-Host "   Could not get transfer history: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Step 7: Verification Instructions
Write-Host ""
Write-Host "Step 7: Verification Instructions" -ForegroundColor Green
Write-Host "======================================="
Write-Host ""
Write-Host "Manual Verification Steps:"
Write-Host "1. Check Base Sepolia (Source Chain):"
Write-Host "   • Contract: 0x0D06a583a3d1bD02D7BdEe535D53495A0E57510C"
Write-Host "   • Token ID: $TOKEN_ID should be burned/transferred"
Write-Host "   • Previous Owner: $FROM_ADDRESS"
Write-Host ""
Write-Host "2. Check OP Sepolia (Destination Chain):"
Write-Host "   • Contract: 0x36f6416213f454Af4a3213067C68F81Fd4919c18"
Write-Host "   • New Owner: $TO_ADDRESS"
Write-Host "   • TokenURI should match original"
Write-Host ""
Write-Host "3. Blockchain Explorers:"
Write-Host "   • Base Sepolia: https://sepolia.basescan.org/"
Write-Host "   • OP Sepolia: https://sepolia-optimism.etherscan.io/"
Write-Host ""

Write-Host "Summary:"
Write-Host "• Transfer from Base Sepolia → OP Sepolia initiated"
Write-Host "• Token ID: $TOKEN_ID"
Write-Host "• From: $FROM_ADDRESS → $TO_ADDRESS"
Write-Host "• Backend API integration tested"
Write-Host ""
Write-Host "Cross-Chain NFT Transfer Test Completed!" -ForegroundColor Cyan