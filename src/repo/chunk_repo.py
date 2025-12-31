from motor.motor_asyncio import AsyncIOMotorDatabase

class ChunkRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["chunks"]

    async def insert_chunks(self, project_id: str, file_id: str, chunks: list[str], extra_meta: dict | None = None):
        extra_meta = extra_meta or {}
        docs = []
        for i, text in enumerate(chunks):
            docs.append({
                "project_id": project_id,
                "file_id": file_id,
                "chunk_id": i,
                "text": text,
                "metadata": extra_meta,
            })
        if docs:
            await self.col.insert_many(docs)
