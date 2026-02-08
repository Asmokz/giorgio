from fastapi import APIRouter, HTTPException
from typing import Optional

from src.services import stats_service

router = APIRouter()


@router.get("/")
async def global_stats():
    """Statistiques globales de Giorgio"""
    return stats_service.get_global_stats()


@router.get("/most-watched")
async def most_watched(limit: int = 10):
    """Top des contenus les plus vus"""
    return stats_service.get_most_watched(limit=limit)


@router.get("/top-rated")
async def top_rated(limit: int = 10, min_ratings: int = 1):
    """Top des contenus les mieux notés"""
    return stats_service.get_top_rated(limit=limit, min_ratings=min_ratings)


@router.get("/recent")
async def recent_activity(limit: int = 10):
    """Activité récente"""
    return stats_service.get_recent_activity(limit=limit)


@router.get("/user/{user_id}")
async def user_stats(user_id: str):
    """Statistiques d'un utilisateur"""
    stats = stats_service.get_user_stats(user_id)
    if not stats:
        raise HTTPException(status_code=404, detail="User not found")
    return stats