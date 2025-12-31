from motor.motor_asyncio import AsyncIOMotorDatabase

class FileRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["files"]

    async def upsert_file(self, meta: dict):
        await self.col.update_one(
            {"project_id": meta["project_id"], "file_id": meta["file_id"]},
            {"$set": meta},
            upsert=True
        )

    async def get_file(self, project_id: str, file_id: str) -> dict | None:
        return await self.col.find_one({"project_id": project_id, "file_id": file_id})
