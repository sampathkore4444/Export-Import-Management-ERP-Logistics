import httpx
from database.database import settings

def ollama_is_available() -> bool:
    try:
        with httpx.Client(timeout=3.0) as client:
            res = client.get(f"{settings.ollama_url}/api/tags")
            return res.status_code == 200
    except Exception:
        return False

def list_ollama_models() -> list:
    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(f"{settings.ollama_url}/api/tags")
            if res.status_code == 200:
                return [m.get("name") for m in res.json().get("models", [])]
    except Exception:
        pass
    return []

def model_available(model: str, installed: list = None) -> bool:
    if installed is None:
        installed = list_ollama_models()
    return any(m == model or m.startswith(model.split(":")[0]) for m in installed)

def chat(model: str, messages: list, temperature: float = 0.3, stream: bool = False) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {"temperature": temperature},
    }
    with httpx.Client(timeout=settings.ollama_request_timeout) as client:
        res = client.post(f"{settings.ollama_url}/api/chat", json=payload)
        res.raise_for_status()
        return res.json()

def generate_with_images(model: str, prompt: str, images: list, temperature: float = 0.1) -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "images": images,
        "stream": False,
        "options": {"temperature": temperature},
    }
    with httpx.Client(timeout=settings.ollama_request_timeout) as client:
        res = client.post(f"{settings.ollama_url}/api/generate", json=payload)
        res.raise_for_status()
        return res.json()
