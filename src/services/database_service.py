from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import logging

from src.models.database import SessionLocal, User, Content, Watchlog

logger = logging.getLogger(__name__)


def get_or_create_user(jellyfin_id: str, username: str) -> User:
    """Récupère ou crée un utilisateur"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.jellyfin_id == jellyfin_id).first()
        if not user:
            user = User(jellyfin_id=jellyfin_id, username=username)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"👤 New user created: {username}")
        return user
    finally:
        db.close()


def get_or_create_content(
    content_id: str,
    title: str,
    content_type: str,
    year: Optional[int] = None,
    genres: Optional[list] = None,
    tmdb_id: Optional[str] = None,
    length: Optional[int] = None
) -> Content:
    """Récupère ou crée un contenu"""
    db = SessionLocal()
    try:
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            content = Content(
                id=content_id,
                title=title,
                type=content_type,
                year=year,
                genres=genres,
                tmdb_id=tmdb_id,
                length=length
            )
            db.add(content)
            db.commit()
            db.refresh(content)
            logger.info(f"🎬 New content added: {title}")
        return content
    finally:
        db.close()


def create_watchlog(user_id: str, content_id: str) -> Watchlog:
    """Crée une entrée de visionnage (sans note pour l'instant)"""
    db = SessionLocal()
    try:
        watchlog = Watchlog(
            user_id=user_id,
            content_id=content_id,
            watched_at=datetime.utcnow()
        )
        db.add(watchlog)
        db.commit()
        db.refresh(watchlog)
        logger.info(f"📝 Watchlog created: {user_id} → {content_id}")
        return watchlog
    finally:
        db.close()


def update_rating(watchlog_id: int, rating: int) -> Optional[Watchlog]:
    """Met à jour la note d'un visionnage"""
    db = SessionLocal()
    try:
        watchlog = db.query(Watchlog).filter(Watchlog.id == watchlog_id).first()
        if watchlog:
            watchlog.rating = rating
            watchlog.rated_at = datetime.utcnow()
            db.commit()
            db.refresh(watchlog)
            logger.info(f"⭐ Rating updated: watchlog {watchlog_id} = {rating}/10")
        return watchlog
    finally:
        db.close()


def get_latest_watchlog(user_id: str, content_id: str) -> Optional[Watchlog]:
    """Récupère le dernier visionnage d'un contenu par un utilisateur"""
    db = SessionLocal()
    try:
        watchlog = db.query(Watchlog)\
            .filter(Watchlog.user_id == user_id, Watchlog.content_id == content_id)\
            .order_by(Watchlog.watched_at.desc())\
            .first()
        return watchlog
    finally:
        db.close()