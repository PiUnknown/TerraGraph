import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes import router

app = FastAPI(title="Darukaa.Earth Biodiversity Intelligence Chatbot")
app.include_router(router)


@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    """
    TEMPORARY debugging aid — returns the full traceback in the HTTP
    response body instead of a generic 500. Remove before submitting;
    exposing stack traces to clients is not something a real API
    should do, this is purely to unblock local debugging.
    """
    tb = traceback.format_exc()
    return JSONResponse(status_code=500, content={"error": str(exc), "traceback": tb})


@app.get("/health")
def health():
    return {"status": "ok"}