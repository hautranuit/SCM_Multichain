"""
User models for ChainFLIP authentication and authorization
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId

class UserRegistration(BaseModel):
    """User registration request model"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)
    wallet_address: str = Field(..., pattern=r"^0x[a-fA-F0-9]{40}$")
    role: Literal["manufacturer", "transporter", "buyer"]
    
    class Config:
        schema_extra = {
            "example": {
                "email": "manufacturer@example.com",
                "password": "SecurePass123!",
                "name": "John Manufacturer",
                "wallet_address": "0x032041b4b356fEE1496805DD4749f181bC736FFA",
                "role": "manufacturer"
            }
        }

class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """User response model (without password)"""
    id: str
    email: str
    name: str
    wallet_address: str
    role: str
    approval_status: Literal["pending", "approved", "rejected"]
    l2_blockchain_assigned: Optional[str] = None
    registration_date: datetime
    approved_date: Optional[datetime] = None
    approved_by: Optional[str] = None

class UserApproval(BaseModel):
    """Admin user approval model"""
    user_id: str
    approval_status: Literal["approved", "rejected"]
    admin_notes: Optional[str] = None

class AuthToken(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserUpdate(BaseModel):
    """User profile update model"""
    name: Optional[str] = None
    wallet_address: Optional[str] = Field(None, pattern=r"^0x[a-fA-F0-9]{40}$")

# Internal database model (includes password hash)
class UserDB(BaseModel):
    """Internal user database model"""
    email: str
    password_hash: str
    name: str
    wallet_address: str
    role: str
    approval_status: str = "pending"
    l2_blockchain_assigned: Optional[str] = None
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    approved_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AdminStats(BaseModel):
    """Admin dashboard statistics"""
    total_users: int
    pending_approvals: int
    approved_users: int
    rejected_users: int
    manufacturers: int
    transporters: int
    buyers: int

# L2 blockchain assignments based on role
L2_BLOCKCHAIN_MAPPING = {
    "manufacturer": "2442",  # L2 CDK Manufacturer Chain
    "transporter": "2443",   # L2 CDK Transporter Chain  
    "buyer": "2444"          # L2 CDK Buyer Chain
}
