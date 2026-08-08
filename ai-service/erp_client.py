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

def fetch_quotations(token: str) -> list:
    return fetch("/quotations", token)

def fetch_bills(token: str) -> list:
    return fetch("/bills", token)

def fetch_finance_analytics(token: str) -> dict:
    url = f"{settings.gateway_url}/api/finance/analytics"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=20.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code == 200:
                return res.json()
    except Exception:
        pass
    return {}

def fetch_containers(token: str) -> list:
    return fetch("/containers", token)

def fetch_containers_in_transit(token: str) -> list:
    return fetch("/containers/in-transit", token)

def fetch_air_jobs(token: str) -> list:
    return fetch("/air", token)

def fetch_inventory(token: str) -> list:
    return fetch("/inventory", token)

def fetch_inventory_summary(token: str) -> dict:
    url = f"{settings.gateway_url}/api/inventory/summary"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=20.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code == 200:
                return res.json()
    except Exception:
        pass
    return {}

def fetch_job(token: str, job_id: str):
    res = fetch(f"/jobs/{job_id}", token)
    return res[0] if res else None

def fetch_export(token: str, export_id: str):
    res = fetch(f"/exports/{export_id}", token)
    return res[0] if res else None

def fetch_single(path: str, token: str):
    res = fetch(path, token)
    return res[0] if res else None
