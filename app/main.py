import json
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.routers import auth, banking
from app.security import verify_hmac_signature

app = FastAPI(
    title="The Banking Portal",
    description="Cybersecurity Project"
)


# run HMAC and check middleware on state changing endpoints
@app.middleware("http")
async def verify_request_integrity(request: Request, call_next):
    if request.url.path == "/api/banking/transfer" and request.method == "POST":
        signature = request.headers.get("X-Signature")
        if not signature:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Missing HMAC signature header"}
            )

        raw_body = await request.body()
        try:
            parsed_json = json.loads(raw_body)
            normalized_payload = json.dumps(parsed_json, separators=(',', ':')).encode('utf-8')
        except Exception:
            normalized_payload = raw_body

        if not verify_hmac_signature(normalized_payload, signature):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Payload integrity check failed (HMAC mismatch)"}
            )

    response = await call_next(request)
    return response


# register the  API Routers
app.include_router(auth.router)
app.include_router(banking.router)


@app.get("/")
def root():
    return {"message": "The Banking Portal API is on. Go to /docs in order to access the swagger ui."}