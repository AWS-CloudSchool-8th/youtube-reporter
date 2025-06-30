from fastapi import FastAPI
from routers import youtube

app = FastAPI(root_path="/auth")

app.include_router(youtube.router)
