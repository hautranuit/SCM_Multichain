"""
Participant models for role-based access control in ChainFLIP Multi-Chain
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class ParticipantRole(str, Enum):
    """Participant roles in the supply chain"""
    MANUFACTURER = "manufacturer"
    TRANSPORTER = "transporter" 
    BUYER = "buyer"
    ARBITRATOR = "arbitrator"
    ADMIN = "admin"

class ParticipantStatus(str, Enum):
    """Participant status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"

class Participant(BaseModel):
    """Participant model for role-based access control"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str = Field(..., description="Blockchain wallet address")
    name: str = Field(..., description="Participant name or organization")
    email: Optional[str] = Field(None, description="Contact email")
    role: ParticipantRole = Field(..., description="Participant role")
    chain_id: int = Field(..., description="Primary blockchain chain ID")
    status: ParticipantStatus = Field(default=ParticipantStatus.PENDING)
    
    # Role-specific data
    manufacturer_license: Optional[str] = Field(None, description="Manufacturing license number")
    transport_license: Optional[str] = Field(None, description="Transportation license")
    business_registration: Optional[str] = Field(None, description="Business registration number")
    
    # Metadata
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = Field(None, description="Admin who approved this participant")
    approved_date: Optional[datetime] = Field(None)
    last_activity: Optional[datetime] = Field(None)
    
    # Verification
    kyc_verified: bool = Field(default=False)
    documents_verified: bool = Field(default=False)
    blockchain_verified: bool = Field(default=False)
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ParticipantCreate(BaseModel):
    """Model for creating a new participant"""
    wallet_address: str = Field(..., description="Blockchain wallet address")
    name: str = Field(..., description="Participant name or organization")
    email: Optional[str] = Field(None, description="Contact email")
    role: ParticipantRole = Field(..., description="Requested role")
    chain_id: int = Field(..., description="Primary blockchain chain ID")
    
    # Role-specific data
    manufacturer_license: Optional[str] = Field(None)
    transport_license: Optional[str] = Field(None)
    business_registration: Optional[str] = Field(None)
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ParticipantUpdate(BaseModel):
    """Model for updating participant information"""
    name: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    status: Optional[ParticipantStatus] = Field(None)
    manufacturer_license: Optional[str] = Field(None)
    transport_license: Optional[str] = Field(None)
    business_registration: Optional[str] = Field(None)
    kyc_verified: Optional[bool] = Field(None)
    documents_verified: Optional[bool] = Field(None)
    blockchain_verified: Optional[bool] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)

class ParticipantResponse(BaseModel):
    """Response model for participant data"""
    id: str
    wallet_address: str
    name: str
    email: Optional[str]
    role: ParticipantRole
    chain_id: int
    status: ParticipantStatus
    registration_date: datetime
    approved_date: Optional[datetime]
    last_activity: Optional[datetime]
    kyc_verified: bool
    documents_verified: bool
    blockchain_verified: bool

class RoleVerificationRequest(BaseModel):
    """Model for role verification requests"""
    wallet_address: str = Field(..., description="Wallet address to verify")
    required_role: ParticipantRole = Field(..., description="Required role")
    chain_id: Optional[int] = Field(None, description="Required chain ID")

class RoleVerificationResponse(BaseModel):
    """Response model for role verification"""
    wallet_address: str
    has_role: bool
    participant_role: Optional[ParticipantRole]
    participant_status: Optional[ParticipantStatus]
    chain_id: Optional[int]
    message: str