from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(title="Darukaa.Earth Biodiversity Intelligence Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://terragraph-x7oxucctkmfigypnt429be.streamlit.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}