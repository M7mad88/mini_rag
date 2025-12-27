from fastapi import FastAPI,APIROUTER

base_router =  = APIROUTER()

@app.get("/")
def root():
    return {"status": "ok", "message": "Mini RAG API is running"}

@app.get("/welcome")
def welcome():
    return {"message": "Hello World"}
