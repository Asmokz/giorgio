from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class JellyfinWebhook(BaseModel):
    NotificationType: str
    ItemId: str
    ItemType: str
    Name: str
    UserId: str
    NotificationUsername: str
    Timestamp: datetime
    
    # Optionnels - Episodes uniquement
    SeriesName: Optional[str] = None
    SeasonNumber: Optional[int] = None
    EpisodeNumber: Optional[int] = None
    
    # Optionnels - Pas toujours présents
    PlayedToCompletion: Optional[bool] = None
    Year: Optional[int] = None
    Provider_tmdb: Optional[str] = None
    Genres: Optional[str] = None  # String brute, on parse après
    
    # Helper pour récupérer les genres en liste
    def get_genres_list(self) -> list[str]:
        if not self.Genres:
            return []
        return [g.strip() for g in self.Genres.split(",")]