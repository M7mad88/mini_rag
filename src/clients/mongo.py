from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.core.config import Settings

def create_mongo_client(settings: Settings) -> AsyncIOMotorClient:
    return AsyncIOMotorClient(settings.MONGODB_URL)

def get_database(client: AsyncIOMotorClient, settings: Settings) -> AsyncIOMotorDatabase:
    return client[settings.MONGODB_DATABASE]
