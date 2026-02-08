from sqlalchemy import func
from typing import Optional
import logging

from src.models.database import SessionLocal, User, Content, Watchlog

logger = logging.getLogger(__name__)


def get_most_watched(limit: int = 10) -> list:
    """Top des contenus les plus vus"""
    db = SessionLocal()
    try:
        results = db.query(
            Content.id,
            Content.title,
            Content.type,
            Content.year,
            func.count(Watchlog.id).label("watch_count"),
            func.avg(Watchlog.rating).label("avg_rating")
        ).join(Watchlog, Content.id == Watchlog.content_id)\
         .group_by(Content.id)\
         .order_by(func.count(Watchlog.id).desc())\
         .limit(limit)\
         .all()
        
        return [
            {
                "id": r.id,
                "title": r.title,
                "type": r.type,
                "year": r.year,
                "watch_count": r.watch_count,
                "avg_rating": round(r.avg_rating, 1) if r.avg_rating else None
            }
            for r in results
        ]
    finally:
        db.close()


def get_top_rated(limit: int = 10, min_ratings: int = 1) -> list:
    """Top des contenus les mieux notés"""
    db = SessionLocal()
    try:
        results = db.query(
            Content.id,
            Content.title,
            Content.type,
            Content.year,
            func.avg(Watchlog.rating).label("avg_rating"),
            func.count(Watchlog.rating).label("rating_count")
        ).join(Watchlog, Content.id == Watchlog.content_id)\
         .filter(Watchlog.rating.isnot(None))\
         .group_by(Content.id)\
         .having(func.count(Watchlog.rating) >= min_ratings)\
         .order_by(func.avg(Watchlog.rating).desc())\
         .limit(limit)\
         .all()
        
        return [
            {
                "id": r.id,
                "title": r.title,
                "type": r.type,
                "year": r.year,
                "avg_rating": round(r.avg_rating, 1),
                "rating_count": r.rating_count
            }
            for r in results
        ]
    finally:
        db.close()


def get_user_stats(user_id: str) -> Optional[dict]:
    """Statistiques d'un utilisateur"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.jellyfin_id == user_id).first()
        if not user:
            return None
        
        # Nombre de visionnages
        total_watched = db.query(func.count(Watchlog.id))\
            .filter(Watchlog.user_id == user_id)\
            .scalar()
        
        # Nombre de notes données
        total_rated = db.query(func.count(Watchlog.id))\
            .filter(Watchlog.user_id == user_id, Watchlog.rating.isnot(None))\
            .scalar()
        
        # Note moyenne donnée
        avg_rating = db.query(func.avg(Watchlog.rating))\
            .filter(Watchlog.user_id == user_id, Watchlog.rating.isnot(None))\
            .scalar()
        
        # Films vs Épisodes
        movies_watched = db.query(func.count(Watchlog.id))\
            .join(Content, Watchlog.content_id == Content.id)\
            .filter(Watchlog.user_id == user_id, Content.type == "movie")\
            .scalar()
        
        episodes_watched = db.query(func.count(Watchlog.id))\
            .join(Content, Watchlog.content_id == Content.id)\
            .filter(Watchlog.user_id == user_id, Content.type == "episode")\
            .scalar()
        
        return {
            "user_id": user_id,
            "username": user.username,
            "total_watched": total_watched,
            "total_rated": total_rated,
            "avg_rating_given": round(avg_rating, 1) if avg_rating else None,
            "movies_watched": movies_watched,
            "episodes_watched": episodes_watched
        }
    finally:
        db.close()


def get_global_stats() -> dict:
    """Statistiques globales de Giorgio"""
    db = SessionLocal()
    try:
        total_users = db.query(func.count(User.jellyfin_id)).scalar()
        total_contents = db.query(func.count(Content.id)).scalar()
        total_movies = db.query(func.count(Content.id)).filter(Content.type == "movie").scalar()
        total_episodes = db.query(func.count(Content.id)).filter(Content.type == "episode").scalar()
        total_watchlogs = db.query(func.count(Watchlog.id)).scalar()
        total_ratings = db.query(func.count(Watchlog.id)).filter(Watchlog.rating.isnot(None)).scalar()
        avg_rating = db.query(func.avg(Watchlog.rating)).filter(Watchlog.rating.isnot(None)).scalar()
        
        return {
            "users": total_users,
            "catalog": {
                "total": total_contents,
                "movies": total_movies,
                "episodes": total_episodes
            },
            "activity": {
                "total_watches": total_watchlogs,
                "total_ratings": total_ratings,
                "avg_rating": round(avg_rating, 1) if avg_rating else None
            }
        }
    finally:
        db.close()


def get_recent_activity(limit: int = 10) -> list:
    """Activité récente"""
    db = SessionLocal()
    try:
        results = db.query(Watchlog, User, Content)\
            .join(User, Watchlog.user_id == User.jellyfin_id)\
            .join(Content, Watchlog.content_id == Content.id)\
            .order_by(Watchlog.watched_at.desc())\
            .limit(limit)\
            .all()
        
        return [
            {
                "username": user.username,
                "content_title": content.title,
                "content_type": content.type,
                "rating": watchlog.rating,
                "watched_at": watchlog.watched_at.isoformat(),
                "rated_at": watchlog.rated_at.isoformat() if watchlog.rated_at else None
            }
            for watchlog, user, content in results
        ]
    finally:
        db.close()