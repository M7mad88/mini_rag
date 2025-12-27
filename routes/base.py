from fastapi import APIRouter

base_router = APIRouter(tags=["Base"])

@base_router.get("/")
def root():
    return {"status": "ok", "message": "Mini RAG API is running"}

@base_router.get("/welcome")
def welcome():
    return {"message": "Hello World"}

