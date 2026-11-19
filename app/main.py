from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routers import auth, users, workflows

app = FastAPI(
    title=settings.app_name,
    description="Workflow automation API",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(workflows.router)


@app.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}