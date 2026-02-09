from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
import asyncio

from src.api.webhooks import router
from src.api.stats import router as stats_router
from src.bot.discord_bot import start_bot
from src.models.database import init_db
from src.services.jellyfin_sync import jellyfin_sync, run_periodic_sync
from config.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 {settings.app_name} starting on port {settings.api_port}")
    
    # Initialise la BDD
    init_db()
    logger.info("🗄️ Database initialized")
    
    # Sync initial du catalogue Jellyfin
    await jellyfin_sync.full_sync()
    
    # Lance la sync périodique en tâche de fond
    sync_task = asyncio.create_task(run_periodic_sync(settings.sync_interval_hours))
    
    # Lance Giorgio dans son thread
    start_bot(settings.discord_bot_token, settings.discord_channel_id)
    logger.info("🤖 Giorgio bot starting...")
    
    yield
    
    # Shutdown
    sync_task.cancel()
    logger.info(f"👋 {settings.app_name} shutting down... Arrivederci!")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.include_router(router, prefix="/api", tags=["webhooks"])
app.include_router(stats_router, prefix="/api/stats", tags=["stats"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "bot": "Giorgio 🇮🇹"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)