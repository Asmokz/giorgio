from fastapi import APIRouter, Request
from pydantic import ValidationError
from src.schemas.jellyfin import JellyfinWebhook
from src.bot.discord_bot import notify_rating_request
from src.services import database_service
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()


# Liste des utilisateurs qui reçoivent les notifications Discord
DISCORD_NOTIFICATION_USERS = ["asmo"]  # Ajoute d'autres users plus tard si besoin


async def handle_playback_stop(payload: JellyfinWebhook):
    """Traite la fin de visionnage d'un contenu"""
    if not payload.PlayedToCompletion:
        logger.info(f"⏸️ User {payload.NotificationUsername} stopped {payload.Name} before end")
        return
    
    # Contenu terminé
    if payload.ItemType == "Episode":
        content_name = f"{payload.SeriesName} S{payload.SeasonNumber}E{payload.EpisodeNumber}"
    else:
        content_name = f"{payload.Name} ({payload.Year})"
    
    logger.info(f"🎉 User {payload.NotificationUsername} finished watching {content_name}")
    
    # Persiste les données pour TOUS les utilisateurs
    user = database_service.get_or_create_user(payload.UserId, payload.NotificationUsername)
    content = database_service.get_or_create_content(
        content_id=payload.ItemId,
        title=content_name,
        content_type=payload.ItemType.lower(),
        year=payload.Year,
        genres=payload.get_genres_list(),
        tmdb_id=payload.Provider_tmdb
    )
    watchlog = database_service.create_watchlog(user.jellyfin_id, content.id)
    
    # Notification Discord SEULEMENT pour certains utilisateurs
    if payload.NotificationUsername.lower() in DISCORD_NOTIFICATION_USERS:
        await notify_rating_request(
            user_id=payload.UserId,
            username=payload.NotificationUsername,
            content_id=payload.ItemId,
            content_name=content_name,
            content_type=payload.ItemType,
            watchlog_id=watchlog.id
        )
    else:
        logger.info(f"📊 Watchlog saved for {payload.NotificationUsername} (no Discord notification)")


async def handle_item_added(payload: JellyfinWebhook):
    """Traite l'ajout d'un nouveau contenu au catalogue"""
    content = database_service.get_or_create_content(
        content_id=payload.ItemId,
        title=payload.Name,
        content_type=payload.ItemType.lower(),
        year=payload.Year,
        genres=payload.get_genres_list(),
        tmdb_id=payload.Provider_tmdb
    )
    logger.info(f"➕ Content synced: {content.title}")


HANDLERS = {
    "PlaybackStop": handle_playback_stop,
    #"ItemAdded": handle_item_added géré par le sync périodique, pas besoin de traiter le webhook pour ça
}


@router.post("/webhook")
async def jellyfin_webhook(request: Request):
    # Jellyfin envoie du text/plain au lieu de application/json
    try:
        body = await request.body()
        raw_payload = json.loads(body)
        payload = JellyfinWebhook(**raw_payload)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON: {e}")
        return {"status": "error", "detail": "Invalid JSON"}
    except ValidationError as e:
        logger.error(f"❌ Validation error: {e}")
        return {"status": "error", "detail": str(e)}
    
    event_type = payload.NotificationType
    handler = HANDLERS.get(event_type)
    
    if handler:
        await handler(payload)
        logger.info(f"✅ Handled event: {event_type} for item {payload.Name}")
        return {"status": "handled"}
    else:
        logger.warning(f"⚠️ Unhandled event type: {event_type}")
        return {"status": "unhandled", "event": event_type}