from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth import router as auth_router

app = FastAPI(
    title="Auth Service",
    description="Handles user authentication with AWS Cognito",
    version="1.0.0"
    # ? root_path는 넣지 않음
)

# ? CORS 허용
origins = [
    "http://34.228.65.221:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router, prefix="/auth")
