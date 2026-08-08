import base64
import io
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from database.security import get_current_user
import ollama_client
import erp_client

router = APIRouter(prefix="/api/ai", tags=["ai"])

TERMINAL_IMPORT = {"CLOSED", "DELIVERED", "REJECTED"}
TERMINAL_EXPORT = {"CLOSED", "REJECTED", "VESSEL_DEPARTED", "EXPORT_CLEARED"}

IMPORT_NEXT = {
    "PENDING_APPROVAL": ("approve", "Approve or reject the job"),
    "APPROVED": ("customs-permit", "Submit the customs permit"),
    "TEAM_ASSIGNED": ("customs-permit", "Submit the customs permit"),
    "LICENSE_APPROVED": ("customs-permit", "Submit the customs permit"),
    "PERMIT_SUBMITTED": ("truck", "Assign truck, trailer and driver"),
    "TRUCK_ASSIGNED": ("arrival", "Record vessel arrival"),
    "VESSEL_ARRIVED": ("clearance", "Process customs clearance"),
    "CUSTOMS_CLEARED": ("pickup", "Record container pickup"),
    "PICKED_UP": ("deliver", "Deliver to consignee"),
    "DELIVERED": ("unload", "Record unloading"),
    "UNLOADED": ("return-container", "Return empty container"),
    "CONTAINER_RETURNED": ("close", "Close the job"),
}

EXPORT_NEXT = {
    "PENDING_APPROVAL": ("approve", "Approve or reject the job"),
    "APPROVED": ("assign-team", "Assign an operations team"),
    "TEAM_ASSIGNED": ("customs-permit", "Submit the customs permit"),
    "PERMIT_SUBMITTED": ("truck", "Assign truck, trailer and driver"),
    "TRUCK_ASSIGNED": ("empty-pickup", "Pick up the empty container"),
    "EMPTY_PICKED_UP": ("stuff", "Confirm stuffing"),
    "STUFFED": ("gate-in", "Record port gate-in and EIR"),
    "GATE_IN": ("departure", "Record vessel departure"),
    "VESSEL_DEPARTED": ("clearance", "Process export clearance"),
    "EXPORT_CLEARED": ("close", "Close the job"),
}


def parse_dt(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def to_iso(dt_value) -> str:
    dt = parse_dt(dt_value)
    return dt.strftime("%Y-%m-%d") if dt else ""


def summarize_list(items: List[dict], fields: List[str], limit: int = 6) -> str:
    out = []
    for it in items[:limit]:
        parts = [str(it.get(f, "")) for f in fields]
        out.append(" | ".join(p for p in parts if p))
    return "\n".join(out) if out else "none"


# ---------------------------------------------------------------- status
@router.get("/status")
def ai_status(user: dict = Depends(get_current_user)):
    available = ollama_client.ollama_is_available()
    models = ollama_client.list_ollama_models() if available else []
    return {
        "ollama_available": available,
        "ollama_url": "http://localhost:11434",
        "installed_models": models,
        "text_model": ollama_client.settings.ollama_text_model,
        "text_model_installed": ollama_client.model_available(ollama_client.settings.ollama_text_model, models),
        "vision_model": ollama_client.settings.ollama_vision_model,
        "vision_model_installed": ollama_client.model_available(ollama_client.settings.ollama_vision_model, models),
    }


# ---------------------------------------------------------------- chat
class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []


def detect_intents(message: str) -> list:
    text = message.lower()
    intents = []
    if any(k in text for k in ["invoice", "revenue", "bill", "money", "cost", "payment", "outstanding", "profit", "expense", "quotation", "finance", "quote"]):
        intents.append("invoices")
    if any(k in text for k in ["customer", "client", "consignee", "shipper"]):
        intents.append("customers")
    if any(k in text for k in ["vendor", "supplier", "outsource"]):
        intents.append("vendors")
    if any(k in text for k in ["item", "cargo", "product", "goods"]):
        intents.append("items")
    if any(k in text for k in ["export", "outbound", "bl", "shipping out"]):
        intents.append("exports")
    if any(k in text for k in ["truck", "driver", "fleet", "trailer"]):
        intents.append("fleet")
    if any(k in text for k in ["container", "teu", "containerized"]):
        intents.append("containers")
    if any(k in text for k in ["air", "awb", "flight", "air freight", "air cargo"]):
        intents.append("air")
    if any(k in text for k in ["warehouse", "inventory", "stock", "storage", "sku"]):
        intents.append("warehouse")
    intents.append("import")
    return intents


def build_context(message: str, token: str) -> dict:
    intents = detect_intents(message)
    ctx = {}

    if "import" in intents:
        jobs = erp_client.fetch_jobs(token)
        active = [j for j in jobs if j.get("status") not in TERMINAL_IMPORT]
        delayed = [j for j in active if parse_dt(j.get("eta")) and parse_dt(j.get("eta")) < datetime.utcnow()]
        by_status = {}
        for j in jobs:
            by_status[j.get("status", "UNKNOWN")] = by_status.get(j.get("status", "UNKNOWN"), 0) + 1
        ctx["import_jobs"] = {
            "total": len(jobs),
            "active": len(active),
            "delayed": len(delayed),
            "by_status": by_status,
            "recent": summarize_list(jobs, ["job_number", "container_number", "vessel_name", "status", "eta"]),
        }

    if "exports" in intents:
        exports = erp_client.fetch_exports(token)
        active = [e for e in exports if e.get("status") not in TERMINAL_EXPORT]
        delayed = [e for e in active if parse_dt(e.get("etd")) and parse_dt(e.get("etd")) < datetime.utcnow()]
        by_status = {}
        for e in exports:
            by_status[e.get("status", "UNKNOWN")] = by_status.get(e.get("status", "UNKNOWN"), 0) + 1
        ctx["export_jobs"] = {
            "total": len(exports),
            "active": len(active),
            "delayed": len(delayed),
            "by_status": by_status,
            "recent": summarize_list(exports, ["job_number", "container_number", "vessel_name", "status", "etd"]),
        }

    if "fleet" in intents:
        trucks = erp_client.fetch_trucks(token)
        drivers = erp_client.fetch_drivers(token)
        ctx["fleet"] = {
            "trucks_total": len(trucks),
            "trucks_available": len([t for t in trucks if str(t.get("status", "")).upper() in ("AVAILABLE", "IDLE", "")]),
            "drivers_total": len(drivers),
            "recent_trucks": summarize_list(trucks, ["plate_number", "status"]),
        }

    if "invoices" in intents:
        invoices = erp_client.fetch_invoices(token)
        outstanding = [i for i in invoices if str(i.get("status", "")).upper() in ("PENDING", "OVERDUE", "ISSUED")]
        total = 0.0
        for i in invoices:
            try:
                total += float(i.get("total", 0) or 0)
            except (TypeError, ValueError):
                pass
        ctx["invoices"] = {
            "total": len(invoices),
            "outstanding": len(outstanding),
            "sum_total": round(total, 2),
        }

    if "customers" in intents:
        customers = erp_client.fetch_customers(token)
        ctx["customers"] = {"total": len(customers), "recent": summarize_list(customers, ["name", "name_eng", "phone"])}

    if "vendors" in intents:
        vendors = erp_client.fetch_vendors(token)
        ctx["vendors"] = {"total": len(vendors), "recent": summarize_list(vendors, ["name_eng", "name_kh", "phone"])}

    if "items" in intents:
        items = erp_client.fetch_items(token)
        ctx["items"] = {"total": len(items), "recent": summarize_list(items, ["item_code", "name", "unit"])}

    return ctx


def context_to_text(ctx: dict) -> str:
    lines = []
    for key, val in ctx.items():
        lines.append(f"[{key}]")
        if isinstance(val, dict):
            for k, v in val.items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append(f"  {val}")
    return "\n".join(lines)


def fallback_answer(message: str, ctx: dict) -> str:
    parts = []
    imp = ctx.get("import_jobs")
    if imp:
        parts.append(f"{imp['total']} import jobs ({imp['active']} active, {imp['delayed']} past ETA)")
    exp = ctx.get("export_jobs")
    if exp:
        parts.append(f"{exp['total']} export jobs ({exp['active']} active, {exp['delayed']} past ETD)")
    fl = ctx.get("fleet")
    if fl:
        parts.append(f"{fl['trucks_available']} of {fl['trucks_total']} trucks available, {fl['drivers_total']} drivers")
    inv = ctx.get("invoices")
    if inv:
        parts.append(f"{inv['outstanding']} of {inv['total']} invoices outstanding, total {inv['sum_total']}")
    if not parts:
        return "I could not load any data right now. Please try again."
    return "Live summary: " + "; ".join(parts) + "."


@router.post("/chat")
def ai_chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    token = user.get("__token__") or ""
    ctx = build_context(req.message, token)

    available = ollama_client.ollama_is_available()
    if not available:
        return {
            "answer": fallback_answer(req.message, ctx),
            "mode": "fallback",
            "context": ctx,
        }

    system_prompt = (
        "You are CargoFlow AI, an assistant for an ERP import/export logistics management system. "
        "Answer the user's question using ONLY the data provided in the context below. "
        "Be concise, use bullet points where helpful, and never invent facts not in the context. "
        "The context is a snapshot of live system data.\n\n"
        f"CONTEXT:\n{context_to_text(ctx)}"
    )
    messages = [{"role": "system", "content": system_prompt}]
    for h in req.history[-6:]:
        messages.append({"role": "user" if h.get("role") == "user" else "assistant", "content": h.get("content", "")})
    messages.append({"role": "user", "content": req.message})

    try:
        res = ollama_client.chat(ollama_client.settings.ollama_text_model, messages)
        answer = res.get("message", {}).get("content", "").strip()
        if not answer:
            raise ValueError("empty answer")
        return {"answer": answer, "mode": "ollama", "context": ctx}
    except Exception:
        return {"answer": fallback_answer(req.message, ctx), "mode": "fallback", "context": ctx}


# ---------------------------------------------------------------- marketing site chatbot (public)
class MarketingChatRequest(BaseModel):
    message: str
    lang: str = "en"

MARKETING_KB = [
    {
        "topic": "Overview",
        "keywords": ["what can", "overview", "features", "modules", "platform", "do you offer", "what is cargoflow", "erp", "what can you", "what do you do", "how can you help"],
        "answer": "CargoFlow ERP is an all-in-one import/export logistics management platform for freight forwarders, agents and 3PL operators. It covers the full shipment lifecycle (import and export), fleet management, invoicing & billing, documents & templates, master data, search & alerts, roles & approvals, reports & dashboard, plus a built-in self-hosted AI copilot.",
    },
    {
        "topic": "Import workflow",
        "keywords": ["import", "inbound", "booking", "customs clearance", "customs permit", "license", "permit", "vessel arrival", "container return", "consignee", "delivery", "unload"],
        "answer": "The import workflow guides a shipment from booking receipt and approval, through license & customs permits, truck assignment (internal or outsourced), vessel arrival, customs clearance, delivery and unloading, to container return and job closure.",
    },
    {
        "topic": "Export workflow",
        "keywords": ["export", "outbound", "stuffing", "empty pickup", "gate-in", "eir", "departure", "etd", "shipping out", "export clearance"],
        "answer": "The export flow covers outbound booking, approval, license & permits, empty container pickup, stuffing at the shipper, port gate-in with EIR, vessel departure, export clearance and finally job closure — mirrored to the import process.",
    },
    {
        "topic": "Fleet management",
        "keywords": ["fleet", "truck", "trailer", "driver", "vehicle", "outsource", "vendor", "assign", "document expiry", "ic card", "licence"],
        "answer": "Fleet management tracks trucks, trailers and drivers with document expiry monitoring (IC card, driving licence), availability status and one-click assignment. You can use your own fleet or outsource shipments to approved vendors.",
    },
    {
        "topic": "Invoicing & billing",
        "keywords": ["invoice", "billing", "bill", "payment", "coa", "tax", "revenue", "credit", "outstanding"],
        "answer": "Invoicing & billing creates per-job invoices with line items, COA mapping, tax calculation and a status workflow, linking revenue directly to each shipment.",
    },
    {
        "topic": "Documents & templates",
        "keywords": ["document", "template", "bl", "bill of lading", "packing list", "attach", "file", "pdf"],
        "answer": "You can attach Bills of Lading, packing lists and permits to each job, and reuse shipment templates to book routine cargo in seconds.",
    },
    {
        "topic": "Master data",
        "keywords": ["master data", "customer", "client", "vendor", "supplier", "item", "location", "settings", "credit terms"],
        "answer": "Master data centralizes customers, vendors, locations, items/services and company settings, including credit terms and COA codes.",
    },
    {
        "topic": "AI assistant",
        "keywords": ["ai", "assistant", "copilot", "ocr", "extract", "predict", "delay prediction", "weekly report", "smart assist", "ollama"],
        "answer": "CargoFlow includes a private, self-hosted AI copilot that answers questions about your operations in plain language, reads shipping documents with OCR extraction, predicts delays and ETAs, generates a weekly operations report and gives smart job-assist tips. It runs fully offline with no external APIs.",
    },
    {
        "topic": "Search & alerts",
        "keywords": ["search", "alert", "notification", "eta", "etd", "expiry", "reminder"],
        "answer": "Global search covers jobs, trucks, customers and vendors, with real-time alerts for missed ETA/ETD and expiring driver documents.",
    },
    {
        "topic": "Reports & dashboard",
        "keywords": ["report", "dashboard", "kpi", "calendar", "print", "performance"],
        "answer": "The platform includes a live KPI dashboard, a calendar view, printable job cards and an AI-generated weekly operations report.",
    },
    {
        "topic": "Roles & approvals",
        "keywords": ["role", "approval", "admin", "manager", "staff", "security", "jwt", "permission", "access", "authorize"],
        "answer": "CargoFlow uses JWT security with admin, manager and staff roles. Approvals, rejections and destructive actions are gated by role.",
    },
    {
        "topic": "Pricing",
        "keywords": ["price", "pricing", "plan", "cost", "costs", "month", "monthly", "trial", "free", "subscribe", "subscription", "upgrade", "starter", "business", "enterprise", "how much", "per user"],
        "answer": "Pricing: Starter is $99/month for up to 5 users (import & export workflows, fleet management, master data, email support). Business is $249/month for up to 25 users and adds invoicing & billing, documents & templates, the AI assistant and priority support. Enterprise is custom pricing for unlimited users, on-premise/private-cloud hosting, custom integrations and a dedicated success manager. Every plan starts with a 14-day free trial, no credit card required.",
    },
    {
        "topic": "Security & privacy",
        "keywords": ["security", "secure", "privacy", "private", "data", "safe", "self-hosted", "self hosted", "offline", "internet", "network", "local", "infrastructure", "own server", "private cloud"],
        "answer": "CargoFlow runs on your own infrastructure. All AI inference happens locally with self-hosted models, so your shipment data never leaves your network. AI features do not require an internet connection and fall back to a rule-based mode if the AI service is offline.",
    },
    {
        "topic": "Deployment",
        "keywords": ["deploy", "deployment", "on-premise", "on premise", "hosting", "install", "installation", "server", "microservice", "microservices"],
        "answer": "CargoFlow can be deployed on-premise or in a private cloud (Enterprise plan), or hosted for you. All services are self-contained microservices.",
    },
    {
        "topic": "Languages",
        "keywords": ["language", "khmer", "chinese", "english", "translate", "translation", "multilingual", "ខ្មែរ", "中文"],
        "answer": "The CargoFlow website is available in English, Khmer and Chinese via the language selector, and the assistant can answer in the language you write in.",
    },
    {
        "topic": "Getting started",
        "keywords": ["start", "get started", "begin", "demo", "sign up", "register", "signup", "onboarding", "book", "contact", "sales", "buy", "purchase"],
        "answer": "You can book a live demo or start a free 14-day trial from the site. Every plan includes a guided onboarding call, and our sales team is available at sales@cargoflow.app.",
    },
    {
        "topic": "Company",
        "keywords": ["cargoflow", "company", "who are you", "who is", "forwarder", "freight", "3pl", "agent", "logistics"],
        "answer": "CargoFlow ERP is built for freight forwarders, agents and 3PL operators to manage import and export shipments, their fleet, invoicing, documents and AI-assisted reporting on one platform.",
    },
]

GREETING_KEYWORDS = [
    "hi", "hello", "hey", "how are you", "good morning", "good afternoon", "good evening", "greetings",
    "thanks", "thank you", "thankyou", "bye", "goodbye", "nice to meet you",
    "សួស្តី", "ជំរាបសួរ", "អរគុណ", "ជំរាបលា",
    "你好", "您好", "谢谢", "再见",
]

MARKETING_TEXTS = {
    "welcome": {
        "en": "Hi! I'm the CargoFlow ERP assistant. Ask me about the platform — features, import/export workflows, fleet management, AI capabilities, pricing plans, security, or how to get started.",
        "km": "ជំរាបសួរ! ខ្ញុំជាជំនួយការ CargoFlow ERP។ សួរខ្ញុំអំពីវេទិកា — មុខងារ, លំហូរនាំចូល/នាំចេញ, ការគ្រប់គ្រងកងនាវា, សមត្ថភាព AI, ផែនការតម្លៃ, សុវត្ថិភាព ឬរបៀបចាប់ផ្តើម។",
        "zh": "您好！我是 CargoFlow ERP 助手。请向我询问平台相关问题——功能、进出口流程、车队管理、AI能力、定价方案、安全性或如何开始使用。",
    },
    "refusal": {
        "en": "I'm the CargoFlow Assistant and I can only answer questions about the CargoFlow ERP platform. Ask me about import/export workflows, fleet management, AI features, pricing plans, or security.",
        "km": "ខ្ញុំជាជំនួយការ CargoFlow ហើយខ្ញុំអាចឆ្លើយបានតែសំណួរអំពីវេទិកា CargoFlow ERP ប៉ុណ្ណោះ។ សួរខ្ញុំអំពីលំហូរនាំចូល/នាំចេញ, ការគ្រប់គ្រងកងនាវា, មុខងារ AI, ផែនការតម្លៃ ឬសុវត្ថិភាព។",
        "zh": "我是 CargoFlow 助手，只能回答关于 CargoFlow ERP 平台的问题。您可以询问进出口流程、车队管理、AI功能、定价方案或安全性。",
    },
    "unavailable": {
        "en": "The AI assistant is temporarily offline. Please try again in a moment.",
        "km": "ជំនួយការ AI កំពុងមិនដំណើរការជាបណ្តោះអាសន្ន។ សូមព្យាយាមម្តងទៀតនៅពេលក្រោយ។",
        "zh": "AI 助手暂时离线，请稍后再试。",
    },
}


def _marketing_keywords() -> set:
    words = set()
    for entry in MARKETING_KB:
        for k in entry["keywords"]:
            words.add(k)
    return words


def _compile_multi_pattern(items: list) -> re.Pattern:
    parts = []
    for k in items:
        low = k.lower()
        if re.fullmatch(r"[a-z0-9]+", low):
            parts.append(r"\b" + re.escape(low) + r"\b")
        else:
            parts.append(re.escape(low))
    return re.compile("|".join(parts))


MARKETING_PLATFORM_PATTERN = _compile_multi_pattern(_marketing_keywords())
MARKETING_GREETING_PATTERN = _compile_multi_pattern(GREETING_KEYWORDS)


def classify_marketing(message: str) -> str:
    text = message.lower().strip()
    if MARKETING_PLATFORM_PATTERN.search(text):
        return "platform"
    if MARKETING_GREETING_PATTERN.search(text):
        return "greeting"
    return "off_topic"


def marketing_kb_prompt() -> str:
    lines = []
    for entry in MARKETING_KB:
        lines.append(f"- {entry['topic']}: {entry['answer']}")
    return "\n".join(lines)


def match_marketing_kb(message: str):
    text = message.lower()
    best = None
    best_score = 0
    for entry in MARKETING_KB:
        score = sum(1 for k in entry["keywords"] if k in text)
        if score > best_score:
            best_score = score
            best = entry
    return best if best_score > 0 else None


@router.post("/marketing-chat")
def marketing_chat(req: MarketingChatRequest):
    lang = req.lang if req.lang in MARKETING_TEXTS["welcome"] else "en"

    kind = classify_marketing(req.message)
    if kind == "greeting":
        return {"answer": MARKETING_TEXTS["welcome"][lang], "mode": "static", "lang": lang}
    if kind == "off_topic":
        return {"answer": MARKETING_TEXTS["refusal"][lang], "mode": "static", "lang": lang}

    if not ollama_client.ollama_is_available():
        match = match_marketing_kb(req.message)
        answer = match["answer"] if match else MARKETING_TEXTS["unavailable"][lang]
        return {"answer": answer, "mode": "fallback", "lang": lang}

    system_prompt = (
        "You are the CargoFlow Assistant, the support and sales chatbot for CargoFlow ERP — "
        "an import/export logistics management platform. You answer ONLY questions about CargoFlow ERP: "
        "its features, import/export workflows, fleet management, invoicing, documents, AI capabilities, "
        "pricing, security, deployment and company.\n\n"
        "Use ONLY the facts below. Never invent or exaggerate features, prices or capabilities. "
        "Be concise and friendly; use bullet points when listing items. "
        "Respond in the same language the visitor used (English, Khmer or Chinese).\n\n"
        f"FACTS:\n{marketing_kb_prompt()}\n\n"
        "GUARDRAILS:\n"
        "- If a question is NOT about CargoFlow ERP (for example general knowledge, cooking, politics, "
        "weather, coding, or anything unrelated), politely refuse and redirect, saying you can only help "
        "with questions about the CargoFlow ERP platform.\n"
        "- Do not answer factual questions unrelated to the platform even if the visitor insists."
    )
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": req.message}]

    try:
        res = ollama_client.chat(ollama_client.settings.ollama_text_model, messages, temperature=0.3)
        answer = res.get("message", {}).get("content", "").strip()
        if not answer:
            raise ValueError("empty answer")
        return {"answer": answer, "mode": "ollama", "lang": lang}
    except Exception:
        match = match_marketing_kb(req.message)
        answer = match["answer"] if match else MARKETING_TEXTS["unavailable"][lang]
        return {"answer": answer, "mode": "fallback", "lang": lang}


# ---------------------------------------------------------------- extract document
def rasterize_pdf(data: bytes, max_pages: int = 3) -> List[bytes]:
    try:
        import fitz
    except ImportError:
        raise HTTPException(status_code=422, detail="PDF support unavailable (PyMuPDF not installed)")
    images = []
    doc = fitz.open(stream=data, filetype="pdf")
    for page in doc.pages(0, min(max_pages, len(doc))):
        pix = page.get_pixmap(dpi=200)
        images.append(pix.tobytes("png"))
    return images


@router.post("/extract-document")
async def extract_document(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    filename = (file.filename or "").lower()
    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="Empty file")

    if filename.endswith(".pdf"):
        images = rasterize_pdf(data)
    elif any(filename.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".bmp", ".webp")):
        images = [data]
    else:
        raise HTTPException(status_code=422, detail="Unsupported file type (use PDF, PNG, JPG)")

    b64_images = [base64.b64encode(img).decode("ascii") for img in images]

    if not ollama_client.ollama_is_available():
        raise HTTPException(status_code=503, detail="Ollama is not running. Start Ollama to use document extraction.")

    prompt = (
        "Extract shipping document data from the image(s). Return STRICT JSON only, with keys: "
        "bl_number, container_number, vessel_name, shipper, consignee, cargo_description, "
        "etd, atd, quantity. Use null for missing values. Dates as YYYY-MM-DD. No extra text."
    )

    try:
        res = ollama_client.generate_with_images(
            ollama_client.settings.ollama_vision_model, prompt, b64_images, temperature=0.1
        )
        text = res.get("response", "").strip()
    except Exception:
        raise HTTPException(status_code=503, detail="Vision model failed. Run: ollama pull llava:7b")

    data_out = {}
    try:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        data_out = json.loads(m.group(0)) if m else json.loads(text)
    except Exception:
        data_out = {"_raw": text}

    return {"filename": file.filename, "extracted": data_out, "pages": len(images)}


# ---------------------------------------------------------------- predict ETA
def _predict(job: dict, history: List[dict], job_type: str) -> dict:
    schedule_field = "eta" if job_type == "import" else "etd"
    actual_field = "ata" if job_type == "import" else "atd"
    terminal = TERMINAL_IMPORT if job_type == "import" else TERMINAL_EXPORT

    schedule = parse_dt(job.get(schedule_field))
    actual = parse_dt(job.get(actual_field))
    now = datetime.utcnow()

    delays = []
    for h in history:
        e = parse_dt(h.get(schedule_field))
        a = parse_dt(h.get(actual_field))
        if e and a:
            delays.append((a - e).total_seconds() / 86400.0)
    avg_delay = sum(delays) / len(delays) if delays else 0.0

    if actual:
        return {
            "job_number": job.get("job_number"),
            "predicted_arrival": actual.strftime("%Y-%m-%d"),
            "delay_risk": "none",
            "confidence": "high",
            "explanation": "Shipment has already arrived.",
        }

    predicted = None
    if schedule:
        predicted = schedule + timedelta(days=avg_delay)

    if job.get("status") in terminal:
        predicted = predicted or now
        return {
            "job_number": job.get("job_number"),
            "predicted_arrival": predicted.strftime("%Y-%m-%d"),
            "delay_risk": "low",
            "confidence": "medium",
            "explanation": "Job is in a terminal state.",
        }

    if schedule and not predicted:
        predicted = schedule

    overdue_days = 0
    if schedule and now > schedule:
        overdue_days = (now - schedule).total_seconds() / 86400.0

    if overdue_days > 7 or (avg_delay > 5 and overdue_days > 0):
        risk = "high"
    elif overdue_days > 2 or avg_delay > 2:
        risk = "medium"
    else:
        risk = "low"

    explanation = (
        f"Based on {len(delays)} historical shipments, average delay vs {schedule_field.upper()} "
        f"is {avg_delay:.1f} days. Overdue by {overdue_days:.1f} days."
    )
    return {
        "job_number": job.get("job_number"),
        "predicted_arrival": predicted.strftime("%Y-%m-%d") if predicted else None,
        "delay_risk": risk,
        "confidence": "high" if len(delays) >= 10 else ("medium" if len(delays) >= 3 else "low"),
        "explanation": explanation,
    }


class PredictRequest(BaseModel):
    job_type: str = "import"
    job_id: str


@router.post("/predict-eta")
def predict_eta(req: PredictRequest, user: dict = Depends(get_current_user)):
    token = user.get("__token__") or ""
    if req.job_type == "export":
        job = erp_client.fetch_export(token, req.job_id)
        history = erp_client.fetch_exports(token)
    else:
        job = erp_client.fetch_job(token, req.job_id)
        history = erp_client.fetch_jobs(token)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _predict(job, history, req.job_type)


# ---------------------------------------------------------------- weekly report
@router.get("/reports/weekly")
def weekly_report(user: dict = Depends(get_current_user)):
    token = user.get("__token__") or ""
    jobs = erp_client.fetch_jobs(token)
    exports = erp_client.fetch_exports(token)
    invoices = erp_client.fetch_invoices(token)

    week_ago = datetime.utcnow() - timedelta(days=7)

    def created_this_week(items, field="created_at"):
        return [i for i in items if parse_dt(i.get(field)) and parse_dt(i.get(field)) >= week_ago]

    new_jobs = created_this_week(jobs)
    new_exports = created_this_week(exports)
    new_invoices = created_this_week(invoices)

    delayed_imports = [j for j in jobs if parse_dt(j.get("eta")) and parse_dt(j.get("eta")) < datetime.utcnow() and j.get("status") not in TERMINAL_IMPORT]
    delayed_exports = [e for e in exports if parse_dt(e.get("etd")) and parse_dt(e.get("etd")) < datetime.utcnow() and e.get("status") not in TERMINAL_EXPORT]

    revenue = 0.0
    for i in new_invoices:
        try:
            revenue += float(i.get("total", 0) or 0)
        except (TypeError, ValueError):
            pass

    stats = {
        "new_import_jobs": len(new_jobs),
        "new_export_jobs": len(new_exports),
        "new_invoices": len(new_invoices),
        "revenue_7d": round(revenue, 2),
        "active_import_jobs": len([j for j in jobs if j.get("status") not in TERMINAL_IMPORT]),
        "active_export_jobs": len([e for e in exports if e.get("status") not in TERMINAL_EXPORT]),
        "delayed_imports": len(delayed_imports),
        "delayed_exports": len(delayed_exports),
        "top_import_statuses": {s: sum(1 for j in jobs if j.get("status") == s) for s in sorted({j.get("status") for j in jobs})},
    }

    available = ollama_client.ollama_is_available()
    if not available:
        return {
            "generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "mode": "fallback",
            "stats": stats,
            "narrative": (
                f"This week {stats['new_import_jobs']} import jobs and {stats['new_export_jobs']} export jobs were created. "
                f"{stats['new_invoices']} invoices worth {stats['revenue_7d']} were issued. "
                f"There are currently {stats['delayed_imports']} delayed import jobs and {stats['delayed_exports']} delayed export jobs."
            ),
        }

    prompt = (
        "You are CargoFlow AI. Write a concise weekly operations report for a logistics manager "
        "based on these stats. Highlight bottlenecks and recommend actions. Keep under 120 words.\n"
        f"STATS: {json.dumps(stats)}"
    )
    try:
        res = ollama_client.chat(ollama_client.settings.ollama_text_model, [{"role": "user", "content": prompt}], temperature=0.4)
        narrative = res.get("message", {}).get("content", "").strip()
        if not narrative:
            raise ValueError("empty")
    except Exception:
        narrative = "Ollama unavailable for narrative; see stats above."

    return {"generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M"), "mode": "ollama", "stats": stats, "narrative": narrative}


# ---------------------------------------------------------------- smart job assist
class AssistRequest(BaseModel):
    job_type: str = "import"
    job_id: str


@router.post("/assist/job")
def assist_job(req: AssistRequest, user: dict = Depends(get_current_user)):
    token = user.get("__token__") or ""
    if req.job_type == "export":
        job = erp_client.fetch_export(token, req.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")
        next_map = EXPORT_NEXT
        schedule_field = "etd"
    else:
        job = erp_client.fetch_job(token, req.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        next_map = IMPORT_NEXT
        schedule_field = "eta"

    suggestions = []
    status = job.get("status", "")

    if status in ("CLOSED", "REJECTED"):
        suggestions.append({"type": "info", "message": f"Job is {status.lower()}; no further action required."})
    else:
        nxt = next_map.get(status)
        if nxt:
            suggestions.append({"type": "success", "message": f"Next step: {nxt[1]} ({nxt[0]}).", "action": nxt[0]})
        else:
            suggestions.append({"type": "warning", "message": f"Unknown status '{status}'. Review the job manually.", "action": "review"})

    if job.get("license_required") and not job.get("license_approved"):
        suggestions.append({"type": "warning", "message": "License is required but not yet approved. Apply for the license.", "action": "apply-license"})
    if not job.get("customs_permit_status") and status not in ("CLOSED", "REJECTED"):
        suggestions.append({"type": "warning", "message": "Customs permit not submitted yet.", "action": "customs-permit"})
    if not job.get("container_number"):
        suggestions.append({"type": "error", "message": "Container number is missing on this job.", "action": "edit"})

    created = parse_dt(job.get("created_at"))
    updated = parse_dt(job.get("updated_at"))
    now = datetime.utcnow()
    if created:
        age_days = (now - created).total_seconds() / 86400.0
        if status == "PENDING_APPROVAL" and age_days > 3:
            suggestions.append({"type": "error", "message": f"Job awaiting approval for {age_days:.1f} days.", "action": "approve"})
    if updated:
        stuck_days = (now - updated).total_seconds() / 86400.0
        if status not in ("CLOSED", "REJECTED") and stuck_days > 5:
            suggestions.append({"type": "error", "message": f"No activity for {stuck_days:.1f} days in status {status}.", "action": "review"})

    schedule = parse_dt(job.get(schedule_field))
    if schedule and schedule < now and status not in ("CLOSED", "REJECTED"):
        if req.job_type == "export":
            suggestions.append({"type": "error", "message": f"ETD was {schedule.strftime('%Y-%m-%d')} — vessel may be missed.", "action": "departure"})
        else:
            suggestions.append({"type": "error", "message": f"ETA was {schedule.strftime('%Y-%m-%d')} — shipment may be delayed.", "action": "arrival"})

    ai_tip = None
    available = ollama_client.ollama_is_available()
    if available:
        try:
            res = ollama_client.chat(
                ollama_client.settings.ollama_text_model,
                [{
                    "role": "user",
                    "content": (
                        "You are CargoFlow AI. Give one short, practical tip (max 2 sentences) for this logistics job. "
                        f"Job type: {req.job_type}. Status: {status}. Fields: {json.dumps({k: job.get(k) for k in ['job_number', 'container_number', 'vessel_name', 'license_required', 'license_approved', 'customs_permit_status', 'assigned_team']})}"
                    ),
                }],
                temperature=0.5,
            )
            ai_tip = res.get("message", {}).get("content", "").strip()
        except Exception:
            ai_tip = None

    return {"job_number": job.get("job_number"), "status": status, "suggestions": suggestions, "ai_tip": ai_tip}
