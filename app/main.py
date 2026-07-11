from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(title="Darukaa.Earth Biodiversity Intelligence Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your specific Streamlit Cloud URL once deployed
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}