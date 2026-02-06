"""
MongoDB Database Module for Resume Evaluator Application
Handles database connection, initialization, and collection management
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


# ========================================================
# DATABASE CONFIGURATION
# ========================================================

# Local MongoDB connection settings (can be overridden by environment variables)
USE_LOCAL_MONGODB = os.environ.get('USE_LOCAL_MONGODB', 'true').lower() == 'true'
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))
DATABASE_NAME = 'resume_evaluator'

# MongoDB Atlas settings (for remote connection if needed)
MONGO_USERNAME = os.environ.get('MONGO_USERNAME', 'kashishknp07')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', 'mypass12345')
MONGO_CLUSTER = os.environ.get('MONGO_CLUSTER', 'cluster0.xioyye6.mongodb.net')

# Build MongoDB URI based on connection type
if USE_LOCAL_MONGODB:
    # Local MongoDB connection
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{DATABASE_NAME}"
else:
    # MongoDB Atlas connection
    MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/{DATABASE_NAME}?retryWrites=true&w=majority"

# Global connection variables
_client = None
_db = None
_users_col = None
_evaluations_col = None
_generated_col = None
_connection_status = False


# ========================================================
# CONNECTION MANAGEMENT
# ========================================================

def is_connection_alive():
    """
    Check if MongoDB connection exists and is alive
    
    Returns:
        bool: True if connection exists and is alive, False otherwise
    """
    global _client, _connection_status
    if _client is None:
        return False
    try:
        # Try to ping the database
        _client.admin.command('ping')
        _connection_status = True
        return True
    except Exception:
        _connection_status = False
        return False


def create_mongo_connection():
    """
    Create a new MongoDB connection and initialize database
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    global _client, _db, _users_col, _evaluations_col, _generated_col, _connection_status
    
    try:
        if USE_LOCAL_MONGODB:
            print(f"Creating MongoDB connection to local server ({MONGO_HOST}:{MONGO_PORT})...")
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
        else:
            print("Creating MongoDB connection to Atlas cluster...")
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
        
        # Test the connection
        _client.admin.command('ping')
        print("MongoDB connection successful!")
        
        # Get or create database
        _db = _client[DATABASE_NAME]
        print(f"Database '{DATABASE_NAME}' ready")
        
        # Initialize collections
        _users_col = _db['users']
        _evaluations_col = _db['evaluations']
        _generated_col = _db['generated_resumes']
        
        # Create indexes
        create_indexes()
        
        _connection_status = True
        return True
        
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
        _connection_status = False
        _reset_connection()
        return False
    except ServerSelectionTimeoutError as e:
        print(f"MongoDB server selection timeout: {e}")
        _connection_status = False
        _reset_connection()
        return False
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        _connection_status = False
        _reset_connection()
        return False


def _reset_connection():
    """Reset all connection variables"""
    global _client, _db, _users_col, _evaluations_col, _generated_col
    _client = None
    _db = None
    _users_col = None
    _evaluations_col = None
    _generated_col = None


def get_mongo_client():
    """
    Get or create MongoDB client - checks if connection exists, creates if not
    
    Returns:
        MongoClient or None: MongoDB client instance or None if connection failed
    """
    global _client, _connection_status
    
    # Check if connection exists and is alive
    if is_connection_alive():
        return _client
    
    # Connection doesn't exist or is dead, create new one
    if create_mongo_connection():
        return _client
    else:
        print("MongoDB connection unavailable. Some features may not work.")
        return None


# ========================================================
# COLLECTION GETTERS
# ========================================================

def get_database():
    """
    Get database instance
    
    Returns:
        Database: MongoDB database instance or None
    """
    get_mongo_client()
    return _db


def get_users_col():
    """
    Get users collection - creates connection if needed
    
    Returns:
        Collection: Users collection or None
    """
    get_mongo_client()
    return _users_col


def get_evaluations_col():
    """
    Get evaluations collection - creates connection if needed
    
    Returns:
        Collection: Evaluations collection or None
    """
    get_mongo_client()
    return _evaluations_col


def get_generated_col():
    """
    Get generated resumes collection - creates connection if needed
    
    Returns:
        Collection: Generated resumes collection or None
    """
    get_mongo_client()
    return _generated_col


def check_db_connection():
    """
    Check if database connection is available
    
    Returns:
        bool: True if connection is available, False otherwise
    """
    return _connection_status and _users_col is not None


# ========================================================
# DATABASE INITIALIZATION
# ========================================================

def create_indexes():
    """
    Create indexes for better query performance
    """
    try:
        # Users collection indexes
        if _users_col is not None:
            _users_col.create_index("username", unique=True, background=True)
            _users_col.create_index("email", unique=True, background=True)
            print("Users collection indexes created/verified")
        
        # Evaluations collection indexes
        if _evaluations_col is not None:
            _evaluations_col.create_index("user_id", background=True)
            _evaluations_col.create_index("created_at", background=True)
            _evaluations_col.create_index([("user_id", 1), ("created_at", -1)], background=True)
            print("Evaluations collection indexes created/verified")
        
        # Generated resumes collection indexes
        if _generated_col is not None:
            _generated_col.create_index("user_id", background=True)
            _generated_col.create_index("created_at", background=True)
            print("Generated resumes collection indexes created/verified")
            
    except Exception as e:
        print(f"Index creation warning: {e}")


def create_collections():
    """
    Explicitly create collections if they don't exist
    MongoDB creates collections automatically on first insert,
    but this function ensures they exist with proper configuration
    """
    try:
        if _db is None:
            return False
        
        # Create collections with validation (optional)
        collections = ['users', 'evaluations', 'generated_resumes']
        
        for collection_name in collections:
            if collection_name not in _db.list_collection_names():
                _db.create_collection(collection_name)
                print(f"Collection '{collection_name}' created")
            else:
                print(f"Collection '{collection_name}' already exists")
        
        return True
    except Exception as e:
        print(f"Collection creation error: {e}")
        return False


def initialize_database():
    """
    Initialize MongoDB connection and database on startup
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    print("Initializing database connection...")
    if get_mongo_client():
        # Create collections
        create_collections()
        print("Database initialized and ready!")
        return True
    else:
        print("Database initialization failed. App will continue but DB features may not work.")
        return False


def get_database_info():
    """
    Get information about the database
    
    Returns:
        dict: Database information including collection names and document counts
    """
    if not check_db_connection():
        return {"error": "Database connection not available"}
    
    info = {
        "database_name": DATABASE_NAME,
        "connection_status": _connection_status,
        "collections": {}
    }
    
    try:
        collection_names = _db.list_collection_names()
        for col_name in collection_names:
            col = _db[col_name]
            count = col.count_documents({})
            info["collections"][col_name] = {
                "count": count,
                "indexes": list(col.list_indexes())
            }
    except Exception as e:
        info["error"] = str(e)
    
    return info


# ========================================================
# DATABASE UTILITIES
# ========================================================

def drop_database():
    """
    Drop the entire database (USE WITH CAUTION!)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not check_db_connection():
        return False
    
    try:
        _client.drop_database(DATABASE_NAME)
        print(f"Database '{DATABASE_NAME}' dropped successfully")
        _reset_connection()
        return True
    except Exception as e:
        print(f"Error dropping database: {e}")
        return False


def reset_collection(collection_name):
    """
    Reset a collection by removing all documents (USE WITH CAUTION!)
    
    Args:
        collection_name (str): Name of the collection to reset
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not check_db_connection():
        return False
    
    try:
        collection = _db[collection_name]
        result = collection.delete_many({})
        print(f"Collection '{collection_name}' reset: {result.deleted_count} documents deleted")
        return True
    except Exception as e:
        print(f"Error resetting collection: {e}")
        return False


# ========================================================
# MAIN ENTRY POINT
# ========================================================

if __name__ == '__main__':
    # Initialize database when run directly
    print("=" * 50)
    print("MongoDB Database Initialization")
    print("=" * 50)
    
    if initialize_database():
        print("\nDatabase Status:")
        info = get_database_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print("\nFailed to initialize database")
        print("Please check:")
        print("  1. MongoDB connection string is correct")
        print("  2. Network connectivity to MongoDB")
        print("  3. MongoDB credentials are valid")
        print("  4. MongoDB cluster is accessible")
