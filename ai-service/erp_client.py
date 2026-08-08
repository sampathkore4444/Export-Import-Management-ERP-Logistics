import httpx
from database.database import settings

def fetch(path: str, token: str) -> list:
    url = f"{settings.gateway_url}/api{path}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=20.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                return data if isinstance(data, list) else [data]
    except Exception:
        pass
    return []

def fetch_jobs(token: str) -> list:
    return fetch("/jobs?limit=500", token)

def fetch_exports(token: str) -> list:
    return fetch("/exports?limit=500", token)

def fetch_trucks(token: str) -> list:
    return fetch("/trucks", token)

def fetch_drivers(token: str) -> list:
    return fetch("/drivers", token)

def fetch_customers(token: str) -> list:
    return fetch("/customers", token)

def fetch_vendors(token: str) -> list:
    return fetch("/vendors", token)

def fetch_items(token: str) -> list:
    return fetch("/items", token)

def fetch_invoices(token: str) -> list:
    return fetch("/invoices", token)

def fetch_job(token: str, job_id: str):
    res = fetch(f"/jobs/{job_id}", token)
    return res[0] if res else None

def fetch_export(token: str, export_id: str):
    res = fetch(f"/exports/{export_id}", token)
    return res[0] if res else None

def fetch_single(path: str, token: str):
    res = fetch(path, token)
    return res[0] if res else None
