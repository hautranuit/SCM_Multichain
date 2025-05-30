"""
Database configuration and initialization
"""
import motor.motor_asyncio
from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()

# Async MongoDB client for FastAPI
motor_client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_url)
database = motor_client[settings.database_name]

# Sync client for non-async operations if needed
sync_client = MongoClient(settings.mongo_url)
sync_database = sync_client[settings.database_name]

async def init_database():
    """Initialize database collections and indexes"""
    
    # Create collections if they don't exist
    collections = [
        "products",
        "transactions",
        "participants",
        "fl_models",
        "qr_codes",
        "transport_logs",
        "anomalies",
        "counterfeits"
    ]
    
    existing_collections = await database.list_collection_names()
    
    for collection_name in collections:
        if collection_name not in existing_collections:
            await database.create_collection(collection_name)
            print(f"✅ Created collection: {collection_name}")
    
    # Create indexes for better performance
    await create_indexes()

async def create_indexes():
    """Create database indexes"""
    
    # Products collection
    await database.products.create_index("token_id")
    await database.products.create_index("chain_id")
    await database.products.create_index("manufacturer")
    await database.products.create_index("created_at")
    
    # Transactions collection
    await database.transactions.create_index("tx_hash")
    await database.transactions.create_index("chain_id")
    await database.transactions.create_index("block_number")
    await database.transactions.create_index("timestamp")
    
    # Participants collection
    await database.participants.create_index("address")
    await database.participants.create_index("participant_type")
    await database.participants.create_index("chain_id")
    
    # FL Models collection
    await database.fl_models.create_index("model_id")
    await database.fl_models.create_index("participant_address")
    await database.fl_models.create_index("training_round")
    await database.fl_models.create_index("created_at")
    
    # QR Codes collection
    await database.qr_codes.create_index("product_id")
    await database.qr_codes.create_index("qr_hash")
    await database.qr_codes.create_index("created_at")
    
    print("✅ Database indexes created successfully")

def get_database():
    """Dependency to get database instance"""
    return database
