from fastapi import FastAPI
from routers import youtube
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ? CORS Çã¿ë
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

for route in app.routes:
    print(f"? {route.path}")
    
app.include_router(youtube.router)
