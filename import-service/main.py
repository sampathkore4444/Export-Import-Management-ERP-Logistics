import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from sqlalchemy import text
from database.database import engine, Base
from routers.jobs import router
from routers.exports import router as exports_router
from routers.finance import router as finance_router
from routers.containers import router as containers_router
from routers.air import router as air_router
from routers.export_docs import router as export_docs_router

Base.metadata.create_all(bind=engine)

def run_migrations():
    migrations = [
        "ALTER TABLE import_jobs ADD COLUMN IF NOT EXISTS trailer_id UUID",
        "ALTER TABLE import_jobs ADD COLUMN IF NOT EXISTS container_id UUID",
        "ALTER TABLE export_jobs ADD COLUMN IF NOT EXISTS container_id UUID",
    ]
    try:
        with engine.begin() as conn:
            for migration in migrations:
                conn.execute(text(migration))
    except Exception as e:
        print(f"[migration] Warning: could not apply migrations: {e}")

run_migrations()

app = FastAPI(title="Import Service", version="1.0.0")

app.include_router(router)
app.include_router(exports_router)
app.include_router(finance_router)
app.include_router(containers_router)
app.include_router(air_router)
app.include_router(export_docs_router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "import"}
