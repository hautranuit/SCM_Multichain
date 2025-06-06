/**
 * ChainFLIP Frontend Blockchain Service
 * Connects React frontend to sophisticated multi-chain backend APIs
 * Implements all 5 algorithms and cross-chain operations
 */

class BlockchainService {
  constructor() {
    this.baseURL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}/api/blockchain${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('Blockchain service request failed:', error);
      throw error;
    }
  }

  // ==========================================
  // CORE SYSTEM STATUS
  // ==========================================

  async getMultiChainStatus() {
    try {
      return await this.request('/status');
    } catch (error) {
      throw new Error(`Failed to get multi-chain status: ${error.message}`);
    }
  }

  async getAlgorithmStatus() {
    try {
      return await this.request('/algorithms/status');
    } catch (error) {
      throw new Error(`Failed to get algorithm status: ${error.message}`);
    }
  }

  async getContractInfo() {
    try {
      return await this.request('/contracts/info');
    } catch (error) {
      throw new Error(`Failed to get contract info: ${error.message}`);
    }
  }

  // ==========================================
  // PARTICIPANT MANAGEMENT
  // ==========================================

  async registerParticipant(participantData) {
    try {
      return await this.request('/participants/register', {
        method: 'POST',
        body: JSON.stringify(participantData),
      });
    } catch (error) {
      throw new Error(`Failed to register participant: ${error.message}`);
    }
  }

  // ==========================================
  // ENHANCED PRODUCT MANAGEMENT (Multi-Chain)
  // ==========================================

  async mintProduct(productData) {
    try {
      return await this.request('/products/mint', {
        method: 'POST',
        body: JSON.stringify(productData),
      });
    } catch (error) {
      throw new Error(`Failed to mint product: ${error.message}`);
    }
  }

  async getProduct(tokenId) {
    try {
      return await this.request(`/products/${tokenId}`);
    } catch (error) {
      throw new Error(`Failed to get product: ${error.message}`);
    }
  }

  async getParticipantProducts(address) {
    try {
      return await this.request(`/participants/${address}/products`);
    } catch (error) {
      throw new Error(`Failed to get participant products: ${error.message}`);
    }
  }

  // ==========================================
  // ALGORITHM 1: PAYMENT RELEASE AND INCENTIVE MECHANISM
  // ==========================================

  async processPaymentRelease(paymentData) {
    try {
      return await this.request('/payment/release', {
        method: 'POST',
        body: JSON.stringify(paymentData),
      });
    } catch (error) {
      throw new Error(`Failed to process payment release: ${error.message}`);
    }
  }

  // ==========================================
  // ALGORITHM 3: SUPPLY CHAIN CONSENSUS ALGORITHM (BATCH PROCESSING)
  // ==========================================

  async createShipmentForConsensus(transporterAddress, shipmentData) {
    try {
      return await this.request('/consensus/shipment/create', {
        method: 'POST',
        body: JSON.stringify({
          transporter: transporterAddress,
          shipment_data: shipmentData
        }),
      });
    } catch (error) {
      throw new Error(`Failed to create shipment for consensus: ${error.message}`);
    }
  }

  async submitConsensusVote(shipmentId, voter, approve, reason) {
    try {
      return await this.request('/consensus/vote', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          voter: voter,
          approve: approve,
          reason: reason
        }),
      });
    } catch (error) {
      throw new Error(`Failed to submit consensus vote: ${error.message}`);
    }
  }

  async processTransactionBatch(nodeType, transactions) {
    try {
      return await this.request('/consensus/batch/process', {
        method: 'POST',
        body: JSON.stringify({
          node_type: nodeType,
          transactions: transactions
        }),
      });
    } catch (error) {
      throw new Error(`Failed to process transaction batch: ${error.message}`);
    }
  }

  async getConsensusBatches() {
    try {
      return await this.request('/consensus/batches');
    } catch (error) {
      throw new Error(`Failed to get consensus batches: ${error.message}`);
    }
  }

  async getConsensusShipments() {
    try {
      return await this.request('/consensus/shipments');
    } catch (error) {
      throw new Error(`Failed to get consensus shipments: ${error.message}`);
    }
  }

  async markShipmentDelivered(shipmentId, transporterAddress) {
    try {
      return await this.request('/consensus/delivery/confirm', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          transporter: transporterAddress
        }),
      });
    } catch (error) {
      throw new Error(`Failed to mark shipment delivered: ${error.message}`);
    }
  }

  async getConsensusStatistics() {
    try {
      return await this.request('/consensus/stats');
    } catch (error) {
      throw new Error(`Failed to get consensus statistics: ${error.message}`);
    }
  }

  // ==========================================
  // ALGORITHM 3: SUPPLY CHAIN CONSENSUS ALGORITHM (BATCH PROCESSING)
  // ==========================================

  async createShipmentForConsensus(transporterAddress, shipmentData) {
    try {
      return await this.request('/consensus/shipment/create', {
        method: 'POST',
        body: JSON.stringify({
          transporter: transporterAddress,
          shipment_data: shipmentData
        }),
      });
    } catch (error) {
      throw new Error(`Failed to create shipment for consensus: ${error.message}`);
    }
  }

  async submitConsensusVote(shipmentId, voter, approve, reason) {
    try {
      return await this.request('/consensus/vote', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          voter: voter,
          approve: approve,
          reason: reason
        }),
      });
    } catch (error) {
      throw new Error(`Failed to submit consensus vote: ${error.message}`);
    }
  }

  async processTransactionBatch(nodeType, transactions) {
    try {
      return await this.request('/consensus/batch/process', {
        method: 'POST',
        body: JSON.stringify({
          node_type: nodeType,
          transactions: transactions
        }),
      });
    } catch (error) {
      throw new Error(`Failed to process transaction batch: ${error.message}`);
    }
  }

  async getConsensusBatches() {
    try {
      return await this.request('/consensus/batches');
    } catch (error) {
      throw new Error(`Failed to get consensus batches: ${error.message}`);
    }
  }

  async getConsensusShipments() {
    try {
      return await this.request('/consensus/shipments');
    } catch (error) {
      throw new Error(`Failed to get consensus shipments: ${error.message}`);
    }
  }

  async markShipmentDelivered(shipmentId, transporterAddress) {
    try {
      return await this.request('/consensus/delivery/confirm', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          transporter: transporterAddress
        }),
      });
    } catch (error) {
      throw new Error(`Failed to mark shipment delivered: ${error.message}`);
    }
  }

  async getConsensusStatistics() {
    try {
      return await this.request('/consensus/stats');
    } catch (error) {
      throw new Error(`Failed to get consensus statistics: ${error.message}`);
    }
  }

  // ==========================================
  // ALGORITHM 4: PRODUCT AUTHENTICITY VERIFICATION
  // ==========================================

  async verifyProductAuthenticity(verificationData) {
    try {
      return await this.request('/products/verify', {
        method: 'POST',
        body: JSON.stringify(verificationData),
      });
    } catch (error) {
      throw new Error(`Failed to verify product authenticity: ${error.message}`);
    }
  }

  // ==========================================
  // ALGORITHM 5: MARKETPLACE (POST SUPPLY CHAIN MANAGEMENT)
  // ==========================================

  async listProductForSale(listingData) {
    try {
      return await this.request('/marketplace/list', {
        method: 'POST',
        body: JSON.stringify(listingData),
      });
    } catch (error) {
      throw new Error(`Failed to list product for sale: ${error.message}`);
    }
  }

  async initiateProductPurchase(purchaseData) {
    try {
      return await this.request('/marketplace/purchase', {
        method: 'POST',
        body: JSON.stringify(purchaseData),
      });
    } catch (error) {
      throw new Error(`Failed to initiate product purchase: ${error.message}`);
    }
  }

  // ==========================================
  // ALGORITHM 3: SUPPLY CHAIN CONSENSUS ALGORITHM (BATCH PROCESSING)
  // ==========================================

  async createShipmentForConsensus(transporterAddress, shipmentData) {
    try {
      return await this.request('/consensus/shipment/create', {
        method: 'POST',
        body: JSON.stringify({
          transporter: transporterAddress,
          shipment_data: shipmentData
        }),
      });
    } catch (error) {
      throw new Error(`Failed to create shipment for consensus: ${error.message}`);
    }
  }

  async submitConsensusVote(shipmentId, voter, approve, reason) {
    try {
      return await this.request('/consensus/vote', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          voter: voter,
          approve: approve,
          reason: reason
        }),
      });
    } catch (error) {
      throw new Error(`Failed to submit consensus vote: ${error.message}`);
    }
  }

  async processTransactionBatch(nodeType, transactions) {
    try {
      return await this.request('/consensus/batch/process', {
        method: 'POST',
        body: JSON.stringify({
          node_type: nodeType,
          transactions: transactions
        }),
      });
    } catch (error) {
      throw new Error(`Failed to process transaction batch: ${error.message}`);
    }
  }

  async getConsensusBatches() {
    try {
      return await this.request('/consensus/batches');
    } catch (error) {
      throw new Error(`Failed to get consensus batches: ${error.message}`);
    }
  }

  async getConsensusShipments() {
    try {
      return await this.request('/consensus/shipments');
    } catch (error) {
      throw new Error(`Failed to get consensus shipments: ${error.message}`);
    }
  }

  async markShipmentDelivered(shipmentId, transporterAddress) {
    try {
      return await this.request('/consensus/delivery/confirm', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          transporter: transporterAddress
        }),
      });
    } catch (error) {
      throw new Error(`Failed to mark shipment delivered: ${error.message}`);
    }
  }

  async getConsensusStatistics() {
    try {
      return await this.request('/consensus/stats');
    } catch (error) {
      throw new Error(`Failed to get consensus statistics: ${error.message}`);
    }
  }

  // ==========================================
  // MULTI-CHAIN SERVICE INTEGRATION
  // (These methods will integrate with the sophisticated MultiChainService)
  // ==========================================

  async getMultiChainServiceStatus() {
    try {
      // This will connect to the MultiChainService chain statistics
      const response = await fetch(`${this.baseURL}/api/multichain/status`);
      if (response.ok) {
        return await response.json();
      }
      // Fallback to blockchain status if multichain endpoint not available
      return await this.getMultiChainStatus();
    } catch (error) {
      console.warn('MultiChain service status not available, using fallback');
      return await this.getMultiChainStatus();
    }
  }

  // Manufacturer Chain Operations (Algorithm 4 & 1)
  async mintProductOnManufacturerChain(manufacturerAddress, productData) {
    try {
      // This would integrate with multichain_service.mint_product_on_manufacturer_chain()
      return await this.request('/multichain/manufacturer/mint', {
        method: 'POST',
        body: JSON.stringify({
          manufacturer: manufacturerAddress,
          product_data: productData
        }),
      });
    } catch (error) {
      console.warn('Manufacturer chain operation not available, using standard mint');
      return await this.mintProduct({
        manufacturer: manufacturerAddress,
        metadata: productData
      });
    }
  }

  async performQualityCheck(productId, inspector, passed, score, reportCid = '') {
    try {
      // This would integrate with multichain_service.perform_quality_check()
      return await this.request('/multichain/manufacturer/quality-check', {
        method: 'POST',
        body: JSON.stringify({
          product_id: productId,
          inspector: inspector,
          passed: passed,
          score: score,
          report_cid: reportCid
        }),
      });
    } catch (error) {
      throw new Error(`Failed to perform quality check: ${error.message}`);
    }
  }

  async claimManufacturingIncentive(manufacturerAddress) {
    try {
      // This would integrate with multichain_service.claim_manufacturing_incentive()
      return await this.request('/multichain/manufacturer/incentive', {
        method: 'POST',
        body: JSON.stringify({
          manufacturer: manufacturerAddress
        }),
      });
    } catch (error) {
      throw new Error(`Failed to claim manufacturing incentive: ${error.message}`);
    }
  }

  // Transporter Chain Operations (Algorithm 3 & 1 & 2)
  async createShipment(transporterAddress, shipmentData) {
    try {
      // This would integrate with multichain_service.create_shipment()
      return await this.request('/multichain/transporter/shipment', {
        method: 'POST',
        body: JSON.stringify({
          transporter: transporterAddress,
          shipment_data: shipmentData
        }),
      });
    } catch (error) {
      throw new Error(`Failed to create shipment: ${error.message}`);
    }
  }

  async submitConsensusVote(shipmentId, voter, approve, reason) {
    try {
      // This would integrate with multichain_service.submit_consensus_vote()
      return await this.request('/multichain/transporter/consensus-vote', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          voter: voter,
          approve: approve,
          reason: reason
        }),
      });
    } catch (error) {
      throw new Error(`Failed to submit consensus vote: ${error.message}`);
    }
  }

  async markDelivered(shipmentId, transporterAddress) {
    try {
      // This would integrate with multichain_service.mark_delivered()
      return await this.request('/multichain/transporter/delivered', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          transporter: transporterAddress
        }),
      });
    } catch (error) {
      throw new Error(`Failed to mark delivered: ${error.message}`);
    }
  }

  // Buyer Chain Operations (Algorithm 5 & 2 & 1)
  async createMarketplaceListing(sellerAddress, listingData) {
    try {
      // This would integrate with multichain_service.create_marketplace_listing()
      return await this.request('/multichain/buyer/marketplace-listing', {
        method: 'POST',
        body: JSON.stringify({
          seller: sellerAddress,
          listing_data: listingData
        }),
      });
    } catch (error) {
      throw new Error(`Failed to create marketplace listing: ${error.message}`);
    }
  }

  async createPurchase(buyerAddress, listingId, deliveryLocation, paymentAmount) {
    try {
      // This would integrate with multichain_service.create_purchase()
      return await this.request('/multichain/buyer/purchase', {
        method: 'POST',
        body: JSON.stringify({
          buyer: buyerAddress,
          listing_id: listingId,
          delivery_location: deliveryLocation,
          payment_amount: paymentAmount
        }),
      });
    } catch (error) {
      throw new Error(`Failed to create purchase: ${error.message}`);
    }
  }

  async openDispute(purchaseId, plaintiff, reason, evidenceCid = '') {
    try {
      // This would integrate with multichain_service.open_dispute()
      return await this.request('/multichain/buyer/dispute', {
        method: 'POST',
        body: JSON.stringify({
          purchase_id: purchaseId,
          plaintiff: plaintiff,
          reason: reason,
          evidence_cid: evidenceCid
        }),
      });
    } catch (error) {
      throw new Error(`Failed to open dispute: ${error.message}`);
    }
  }

  async confirmDelivery(purchaseId, buyerAddress) {
    try {
      // This would integrate with multichain_service.confirm_delivery()
      return await this.request('/multichain/buyer/confirm-delivery', {
        method: 'POST',
        body: JSON.stringify({
          purchase_id: purchaseId,
          buyer: buyerAddress
        }),
      });
    } catch (error) {
      throw new Error(`Failed to confirm delivery: ${error.message}`);
    }
  }

  // ==========================================
  // ALGORITHM 3: SUPPLY CHAIN CONSENSUS ALGORITHM (BATCH PROCESSING)
  // ==========================================

  async createShipmentForConsensus(transporterAddress, shipmentData) {
    try {
      return await this.request('/consensus/shipment/create', {
        method: 'POST',
        body: JSON.stringify({
          transporter: transporterAddress,
          shipment_data: shipmentData
        }),
      });
    } catch (error) {
      throw new Error(`Failed to create shipment for consensus: ${error.message}`);
    }
  }

  async submitConsensusVote(shipmentId, voter, approve, reason) {
    try {
      return await this.request('/consensus/vote', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          voter: voter,
          approve: approve,
          reason: reason
        }),
      });
    } catch (error) {
      throw new Error(`Failed to submit consensus vote: ${error.message}`);
    }
  }

  async processTransactionBatch(nodeType, transactions) {
    try {
      return await this.request('/consensus/batch/process', {
        method: 'POST',
        body: JSON.stringify({
          node_type: nodeType,
          transactions: transactions
        }),
      });
    } catch (error) {
      throw new Error(`Failed to process transaction batch: ${error.message}`);
    }
  }

  async getConsensusBatches() {
    try {
      return await this.request('/consensus/batches');
    } catch (error) {
      throw new Error(`Failed to get consensus batches: ${error.message}`);
    }
  }

  async getConsensusShipments() {
    try {
      return await this.request('/consensus/shipments');
    } catch (error) {
      throw new Error(`Failed to get consensus shipments: ${error.message}`);
    }
  }

  async markShipmentDelivered(shipmentId, transporterAddress) {
    try {
      return await this.request('/consensus/delivery/confirm', {
        method: 'POST',
        body: JSON.stringify({
          shipment_id: shipmentId,
          transporter: transporterAddress
        }),
      });
    } catch (error) {
      throw new Error(`Failed to mark shipment delivered: ${error.message}`);
    }
  }

  async getConsensusStatistics() {
    try {
      return await this.request('/consensus/stats');
    } catch (error) {
      throw new Error(`Failed to get consensus statistics: ${error.message}`);
    }
  }

  // ==========================================
  // UTILITY METHODS
  // ==========================================

  async getAllChainStats() {
    try {
      // This would integrate with multichain_service.get_chain_stats()
      const multiChainStatus = await this.getMultiChainServiceStatus();
      const algorithmStatus = await this.getAlgorithmStatus();
      
      return {
        multichain: multiChainStatus,
        algorithms: algorithmStatus,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      throw new Error(`Failed to get all chain stats: ${error.message}`);
    }
  }

  // Format data for UI display
  formatAddressForDisplay(address) {
    if (!address) return 'N/A';
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  }

  formatDateForDisplay(timestamp) {
    if (!timestamp) return 'N/A';
    return new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp).toLocaleDateString();
  }

  formatCurrencyForDisplay(amount) {
    if (!amount) return '$0.00';
    return `$${parseFloat(amount).toFixed(2)}`;
  }
}

export default new BlockchainService();