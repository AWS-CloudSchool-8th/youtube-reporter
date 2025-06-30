from fastapi import FastAPI
from routers.auth import router as auth_router

app = FastAPI(
    title="Auth Service",
    description="Handles user authentication with AWS Cognito",
    version="1.0.0",
    root_path="/auth"
)

app.include_router(auth_router)
# trigger test
