"""
Authentication service for ChainFLIP user management
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserDB, UserRegistration, UserLogin, UserResponse, L2_BLOCKCHAIN_MAPPING
from app.core.config import get_settings

settings = get_settings()

class AuthService:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.users_collection = database.users
        
        # JWT settings
        self.secret_key = getattr(settings, 'jwt_secret_key', 'chainflip-secret-key-2025')
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 1440  # 24 hours

    async def initialize_admin(self):
        """Initialize default admin account"""
        admin_email = "admin@chainflip.com"
        
        # Check if admin already exists
        existing_admin = await self.users_collection.find_one({"email": admin_email})
        if existing_admin:
            print(f"✅ Admin account already exists: {admin_email}")
            return existing_admin

        # Create admin account
        admin_password = "ChainFLIP2025!"
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin_user = {
            "email": admin_email,
            "password_hash": password_hash,
            "name": "ChainFLIP Administrator",
            "wallet_address": "0x000000000000000000000000000000000000000A",  # Admin wallet
            "role": "admin",
            "approval_status": "approved",
            "l2_blockchain_assigned": None,  # Admin doesn't need L2 assignment
            "registration_date": datetime.utcnow(),
            "approved_date": datetime.utcnow(),
            "approved_by": None,  # Self-approved
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.users_collection.insert_one(admin_user)
        print(f"✅ Admin account created: {admin_email}")
        print(f"🔑 Admin password: {admin_password}")
        
        return await self.users_collection.find_one({"_id": result.inserted_id})

    def create_access_token(self, user_data: dict) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "user_id": str(user_data["_id"]),
            "email": user_data["email"],
            "role": user_data["role"],
            "approval_status": user_data["approval_status"],
            "exp": expire
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    async def register_user(self, user_data: UserRegistration) -> UserResponse:
        """Register a new user (pending approval)"""
        
        # Check if user already exists
        existing_user = await self.users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Check if wallet address is already used
        existing_wallet = await self.users_collection.find_one({"wallet_address": user_data.wallet_address})
        if existing_wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet address is already registered"
            )

        # Hash password
        password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "password_hash": password_hash,
            "name": user_data.name,
            "wallet_address": user_data.wallet_address,
            "role": user_data.role,
            "approval_status": "pending",
            "l2_blockchain_assigned": None,  # Assigned after approval
            "registration_date": datetime.utcnow(),
            "approved_date": None,
            "approved_by": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.users_collection.insert_one(user_doc)
        created_user = await self.users_collection.find_one({"_id": result.inserted_id})
        
        return self._user_to_response(created_user)

    async def login_user(self, login_data: UserLogin) -> dict:
        """Authenticate user and return token"""
        
        # Find user by email
        user = await self.users_collection.find_one({"email": login_data.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not bcrypt.checkpw(login_data.password.encode('utf-8'), user["password_hash"].encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is approved (except admin)
        if user["role"] != "admin" and user["approval_status"] != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user['approval_status']}. Please wait for admin approval."
            )
        
        # Create access token
        access_token = self.create_access_token(user)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": self._user_to_response(user)
        }

    async def approve_user(self, user_id: str, approval_status: str, admin_id: str, admin_notes: Optional[str] = None) -> UserResponse:
        """Admin approves or rejects a user"""
        
        # Find user to approve
        user = await self.users_collection.find_one({"_id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user["approval_status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User is already {user['approval_status']}"
            )
        
        # Prepare update data
        update_data = {
            "approval_status": approval_status,
            "approved_date": datetime.utcnow(),
            "approved_by": admin_id,
            "updated_at": datetime.utcnow()
        }
        
        # Assign L2 blockchain if approved
        if approval_status == "approved":
            l2_chain = L2_BLOCKCHAIN_MAPPING.get(user["role"])
            update_data["l2_blockchain_assigned"] = l2_chain
        
        # Update user
        await self.users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        updated_user = await self.users_collection.find_one({"_id": user_id})
        return self._user_to_response(updated_user)

    async def get_pending_users(self) -> list[UserResponse]:
        """Get all users pending approval"""
        cursor = self.users_collection.find({"approval_status": "pending"})
        users = await cursor.to_list(length=None)
        return [self._user_to_response(user) for user in users]

    async def get_all_users(self) -> list[UserResponse]:
        """Get all users (admin only)"""
        cursor = self.users_collection.find({"role": {"$ne": "admin"}})
        users = await cursor.to_list(length=None)
        return [self._user_to_response(user) for user in users]

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        user = await self.users_collection.find_one({"_id": user_id})
        return self._user_to_response(user) if user else None

    async def get_admin_stats(self) -> dict:
        """Get admin dashboard statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_users": {"$sum": 1},
                    "pending_approvals": {
                        "$sum": {"$cond": [{"$eq": ["$approval_status", "pending"]}, 1, 0]}
                    },
                    "approved_users": {
                        "$sum": {"$cond": [{"$eq": ["$approval_status", "approved"]}, 1, 0]}
                    },
                    "rejected_users": {
                        "$sum": {"$cond": [{"$eq": ["$approval_status", "rejected"]}, 1, 0]}
                    },
                    "manufacturers": {
                        "$sum": {"$cond": [{"$eq": ["$role", "manufacturer"]}, 1, 0]}
                    },
                    "transporters": {
                        "$sum": {"$cond": [{"$eq": ["$role", "transporter"]}, 1, 0]}
                    },
                    "buyers": {
                        "$sum": {"$cond": [{"$eq": ["$role", "buyer"]}, 1, 0]}
                    }
                }
            }
        ]
        
        result = await self.users_collection.aggregate(pipeline).to_list(1)
        if result:
            stats = result[0]
            del stats["_id"]
            return stats
        
        return {
            "total_users": 0,
            "pending_approvals": 0,
            "approved_users": 0,
            "rejected_users": 0,
            "manufacturers": 0,
            "transporters": 0,
            "buyers": 0
        }

    def _user_to_response(self, user: dict) -> UserResponse:
        """Convert database user to response model"""
        return UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            name=user["name"],
            wallet_address=user["wallet_address"],
            role=user["role"],
            approval_status=user["approval_status"],
            l2_blockchain_assigned=user.get("l2_blockchain_assigned"),
            registration_date=user["registration_date"],
            approved_date=user.get("approved_date"),
            approved_by=user.get("approved_by")
        )

    async def verify_token(self, token: str) -> dict:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            user = await self.users_collection.find_one({"_id": user_id})
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return user
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
