
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.products import router as products_router
from app.api.conversations import router as conversations_router

app = FastAPI(
    title="Electronics Recommendation Agent",
    description="API for an AI-powered electronics recommendation system.",
    version="1.0.0",
)

app.include_router(products_router)
app.include_router(conversations_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "electronics-recommendation-agent",
    }
