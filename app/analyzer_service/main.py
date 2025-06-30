from fastapi import FastAPI
from routers import analysis, audio

app = FastAPI(title="Analyzer Service", root_path="/analyzer")

# Include routers
app.include_router(analysis.router)
app.include_router(audio.router)

@app.get("/")
def root():
    return {"message": "Analyzer Service Running"}