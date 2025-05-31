"""
Database configuration and initialization
"""
import motor.motor_asyncio
from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()

# Global database instances
motor_client = None
database = None
sync_client = None
sync_database = None

def init_sync_database():
    """Initialize synchronous database connection"""
    global sync_client, sync_database
    sync_client = MongoClient(settings.mongo_url)
    sync_database = sync_client[settings.database_name]
    return sync_database

async def init_database():
    """Initialize database collections and indexes"""
    global motor_client, database
    
    print("🔗 Initializing MongoDB connection...")
    print(f"MongoDB URL: {settings.mongo_url}")
    print(f"Database name: {settings.database_name}")
    
    # Initialize async MongoDB client
    motor_client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_url)
    database = motor_client[settings.database_name]
    
    # Test the connection
    try:
        # This will throw an exception if connection fails
        await motor_client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise e
    
    # Create collections if they don't exist
    collections = [
        "products",
        "transactions", 
        "participants",
        "fl_models",
        "qr_codes",
        "transport_logs",
        "anomalies",
        "counterfeits",
        "cross_chain_messages"
    ]
    
    existing_collections = await database.list_collection_names()
    print(f"Existing collections: {existing_collections}")
    
    for collection_name in collections:
        if collection_name not in existing_collections:
            await database.create_collection(collection_name)
            print(f"✅ Created collection: {collection_name}")
        else:
            print(f"📋 Collection already exists: {collection_name}")
    
    # Create indexes for better performance
    await create_indexes()
    
    return database

async def create_indexes():
    """Create database indexes"""
    
    print("📊 Creating database indexes...")
    
    # Products collection
    await database.products.create_index("token_id", unique=True)
    await database.products.create_index("chain_id")
    await database.products.create_index("manufacturer")
    await database.products.create_index("created_at")
    
    # Transactions collection
    await database.transactions.create_index("tx_hash")
    await database.transactions.create_index("chain_id")
    await database.transactions.create_index("block_number")
    await database.transactions.create_index("timestamp")
    
    # Participants collection
    await database.participants.create_index("address", unique=True)
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
    
    # Cross-chain messages
    await database.cross_chain_messages.create_index("source_chain")
    await database.cross_chain_messages.create_index("target_chain")
    await database.cross_chain_messages.create_index("timestamp")
    
    print("✅ Database indexes created successfully")

async def get_database():
    """Async dependency to get database instance"""
    global motor_client, database
    if database is None:
        # Initialize async MongoDB client if not already initialized
        motor_client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_url)
        database = motor_client[settings.database_name]
        
        # Test the connection
        try:
            await motor_client.admin.command('ping')
            print("✅ Database connection established via get_database()")
        except Exception as e:
            print(f"❌ Database connection failed in get_database(): {e}")
            raise e
    
    return database

def get_sync_database():
    """Get synchronous database instance"""
    global sync_database
    if sync_database is None:
        return init_sync_database()
    return sync_database

async def close_database():
    """Close database connections"""
    global motor_client, sync_client
    if motor_client:
        motor_client.close()
    if sync_client:
        sync_client.close()
