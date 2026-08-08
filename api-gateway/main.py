import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt as jose_jwt

app = FastAPI(title="ERP API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")

PLAN_FEATURES = {
    "starter": {"import", "export", "fleet", "master-data"},
    "business": {"import", "export", "fleet", "master-data", "invoicing", "documents", "templates", "ai"},
    "enterprise": {"import", "export", "fleet", "master-data", "invoicing", "documents", "templates", "ai"},
}

ROUTE_FEATURES = [
    ("/api/ai", "ai"),
    ("/api/invoices", "invoicing"),
    ("/api/templates", "templates"),
    ("/api/export-documents", "documents"),
    ("/api/documents", "documents"),
    ("/api/exports", "export"),
    ("/api/jobs", "import"),
    ("/api/trucks", "fleet"),
    ("/api/trailers", "fleet"),
    ("/api/drivers", "fleet"),
    ("/api/locations", "master-data"),
    ("/api/vendors", "master-data"),
    ("/api/customers", "master-data"),
    ("/api/items", "master-data"),
    ("/api/settings", "master-data"),
]


def route_feature(path: str):
    for prefix, feature in ROUTE_FEATURES:
        if path == prefix or path.startswith(prefix + "/"):
            return feature
    return None


def bearer_claims(request: Request):
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    try:
        return jose_jwt.decode(auth.split(" ", 1)[1], SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None

AUTH_SERVICE = "http://localhost:8001"
IMPORT_SERVICE = "http://localhost:8002"
FLEET_SERVICE = "http://localhost:8003"
MASTER_DATA_SERVICE = "http://localhost:8004"
AI_SERVICE = "http://localhost:8005"


async def proxy(request: Request, service_url: str):
    path = request.url.path
    method = request.method
    headers = dict(request.headers)
    headers.pop("host", None)

    claims = bearer_claims(request)
    feature = route_feature(path)
    if feature and claims:
        plan = claims.get("plan", "starter")
        if feature not in PLAN_FEATURES.get(plan, set()):
            return JSONResponse(
                {"error": f"'{feature}' features are not included in your current plan", "plan": plan, "feature": feature},
                status_code=403,
            )
    if claims:
        headers["X-User-Plan"] = claims.get("plan", "starter")
        headers["X-User-Role"] = claims.get("role", "staff")
        headers["X-User-Id"] = claims.get("user_id", "")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{service_url}{path}"
            if method == "GET":
                response = await client.get(url, headers=headers, params=request.query_params)
            elif method == "POST":
                body = await request.body()
                response = await client.post(url, headers=headers, content=body)
            elif method == "PUT":
                body = await request.body()
                response = await client.put(url, headers=headers, content=body)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                return JSONResponse({"error": "Method not supported"}, status_code=405)

            return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.ConnectError as e:
        return JSONResponse({"error": f"Service at {service_url} is unavailable", "details": str(e)}, status_code=503)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(request: Request, path: str):
    return await proxy(request, AUTH_SERVICE)

@app.api_route("/api/jobs/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/jobs", methods=["GET", "POST"])
async def import_proxy(request: Request, path: str = ""):
    return await proxy(request, IMPORT_SERVICE)

@app.api_route("/api/templates/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/templates", methods=["GET", "POST"])
@app.api_route("/api/invoices/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/invoices", methods=["GET", "POST"])
@app.api_route("/api/documents/{path:path}", methods=["GET", "DELETE"])
@app.api_route("/api/exports/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/exports", methods=["GET", "POST"])
@app.api_route("/api/export-documents/{path:path}", methods=["GET", "DELETE"])
async def import_extra_proxy(request: Request, path: str = ""):
    return await proxy(request, IMPORT_SERVICE)

@app.api_route("/api/trucks/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/trucks", methods=["GET", "POST"])
@app.api_route("/api/trailers/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/trailers", methods=["GET", "POST"])
@app.api_route("/api/drivers/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/drivers", methods=["GET", "POST"])
async def fleet_proxy(request: Request, path: str = ""):
    return await proxy(request, FLEET_SERVICE)

@app.api_route("/api/locations/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/locations", methods=["GET", "POST"])
@app.api_route("/api/vendors/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/vendors", methods=["GET", "POST"])
@app.api_route("/api/customers/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/customers", methods=["GET", "POST"])
@app.api_route("/api/items/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/items", methods=["GET", "POST"])
@app.api_route("/api/settings", methods=["GET", "PUT"])
async def master_data_proxy(request: Request, path: str = ""):
    return await proxy(request, MASTER_DATA_SERVICE)

@app.api_route("/api/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ai_proxy(request: Request, path: str = ""):
    return await proxy(request, AI_SERVICE)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "api-gateway"}
