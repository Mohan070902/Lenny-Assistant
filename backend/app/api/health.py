from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.providers.ollama_provider import OllamaProvider
from app.providers.cloud_provider import CloudProvider
from app.models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=HealthResponse)
async def check_health(db: AsyncSession = Depends(get_db)):
    db_status = "disconnected"
    pgvector_status = "unavailable"
    chunks_indexed = 0

    try:
        # Check basic DB connection
        await db.execute(text("SELECT 1"))
        db_status = "connected"

        from app.database import active_db_url
        if "postgresql" in active_db_url:
            try:
                # Check pgvector
                vec_res = await db.execute(text("SELECT installed_version FROM pg_available_extensions WHERE name = 'vector'"))
                row = vec_res.fetchone()
                if row and row[0]:
                    pgvector_status = f"installed ({row[0]})"
            except Exception:
                pgvector_status = "unavailable"
        else:
            pgvector_status = "sqlite fallback (vector emulation)"

        # Count chunks
        try:
            count_res = await db.execute(text("SELECT COUNT(*) FROM transcript_chunks"))
            c_row = count_res.fetchone()
            if c_row:
                chunks_indexed = c_row[0]
        except Exception:
            pass
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"

    # Check Ollama
    ollama = OllamaProvider()
    ollama_ok = await ollama.is_available()
    ollama_models = await ollama.list_models() if ollama_ok else []

    # Check Cloud
    cloud = CloudProvider()
    cloud_ok = await cloud.is_available()

    overall_status = "healthy" if db_status == "connected" else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        pgvector=pgvector_status,
        chunks_indexed=chunks_indexed,
        providers={
            "ollama": {
                "available": ollama_ok,
                "endpoint": ollama.base_url,
                "target_model": ollama.model,
                "installed_models": ollama_models
            },
            "cloud": {
                "configured": cloud_ok
            }
        }
    )
