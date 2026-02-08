import httpx
import asyncio
import logging
from typing import Optional
from datetime import datetime

from config.settings import settings
from src.services import database_service

logger = logging.getLogger(__name__)


class JellyfinSync:
    """Service de synchronisation du catalogue Jellyfin"""
    
    def __init__(self):
        self.base_url = settings.jellyfin_url.rstrip('/')
        self.headers = {
            "Authorization": f"MediaBrowser Token={settings.jellyfin_api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_all_items(self, item_type: str) -> list:
        """Récupère tous les items d'un type (Movie ou Episode)"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/Items",
                    headers=self.headers,
                    params={
                        "IncludeItemTypes": item_type,
                        "Recursive": "true",
                        "Fields": "Genres,ProviderIds,RunTimeTicks,ProductionYear,SeriesName,ParentIndexNumber,IndexNumber"
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("Items", [])
            except Exception as e:
                logger.error(f"❌ Failed to fetch {item_type}s: {e}")
                return []
    
    def _format_episode_title(self, item: dict) -> str:
        """Formate le titre d'un épisode: 'Breaking Bad S01E05'"""
        series_name = item.get("SeriesName", "Unknown")
        season = item.get("ParentIndexNumber", 0)
        episode = item.get("IndexNumber", 0)
        return f"{series_name} S{season:02d}E{episode:02d}"
    
    def _ticks_to_minutes(self, ticks: Optional[int]) -> Optional[int]:
        """Convertit les RunTimeTicks Jellyfin en minutes"""
        if not ticks:
            return None
        return int(ticks / 10_000_000 / 60)
    
    async def sync_movies(self) -> int:
        """Synchronise tous les films"""
        logger.info("🎬 Syncing movies...")
        movies = await self.get_all_items("Movie")
        count = 0
        
        for movie in movies:
            try:
                genres = movie.get("Genres", [])
                provider_ids = movie.get("ProviderIds", {})
                
                database_service.get_or_create_content(
                    content_id=movie["Id"],
                    title=movie.get("Name", "Unknown"),
                    content_type="movie",
                    year=movie.get("ProductionYear"),
                    genres=genres if genres else None,
                    tmdb_id=provider_ids.get("Tmdb"),
                    length=self._ticks_to_minutes(movie.get("RunTimeTicks"))
                )
                count += 1
            except Exception as e:
                logger.error(f"❌ Failed to sync movie {movie.get('Name')}: {e}")
        
        logger.info(f"✅ Synced {count} movies")
        return count
    
    async def sync_episodes(self) -> int:
        """Synchronise tous les épisodes"""
        logger.info("📺 Syncing episodes...")
        episodes = await self.get_all_items("Episode")
        count = 0
        
        for episode in episodes:
            try:
                genres = episode.get("Genres", [])
                provider_ids = episode.get("ProviderIds", {})
                
                database_service.get_or_create_content(
                    content_id=episode["Id"],
                    title=self._format_episode_title(episode),
                    content_type="episode",
                    year=episode.get("ProductionYear"),
                    genres=genres if genres else None,
                    tmdb_id=provider_ids.get("Tmdb"),
                    length=self._ticks_to_minutes(episode.get("RunTimeTicks"))
                )
                count += 1
            except Exception as e:
                logger.error(f"❌ Failed to sync episode: {e}")
        
        logger.info(f"✅ Synced {count} episodes")
        return count
    
    async def full_sync(self) -> dict:
        """Synchronisation complète du catalogue"""
        logger.info("🔄 Starting full catalog sync...")
        start_time = datetime.now()
        
        movies_count = await self.sync_movies()
        episodes_count = await self.sync_episodes()
        
        duration = (datetime.now() - start_time).seconds
        logger.info(f"🎉 Full sync completed in {duration}s: {movies_count} movies, {episodes_count} episodes")
        
        return {
            "movies": movies_count,
            "episodes": episodes_count,
            "duration_seconds": duration
        }


# Instance globale
jellyfin_sync = JellyfinSync()


async def run_periodic_sync(interval_hours: int):
    """Tâche de fond pour la synchronisation périodique"""
    while True:
        await asyncio.sleep(interval_hours * 3600)
        logger.info(f"⏰ Periodic sync triggered (every {interval_hours}h)")
        await jellyfin_sync.full_sync()