from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

from config.settings import settings

# Engine et Session
engine = create_engine(settings.database_url, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les models
Base = declarative_base()


class User(Base):
    """Utilisateur Jellyfin"""
    __tablename__ = "users"
    
    jellyfin_id = Column(String(36), primary_key=True)
    username = Column(String(100), nullable=False)
    discord_id = Column(String(20), nullable=True)
    
    # Relation vers les watchlogs
    watchlogs = relationship("Watchlog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"


class Content(Base):
    """Film ou épisode dans le catalogue"""
    __tablename__ = "contents"
    
    id = Column(String(36), primary_key=True)  # UUID Jellyfin
    title = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # 'movie' | 'episode'
    year = Column(Integer, nullable=True)
    genres = Column(JSON, nullable=True)  # ["Action", "Sci-Fi"]
    tmdb_id = Column(String(20), nullable=True)
    length = Column(Integer, nullable=True)  # Durée en minutes
    
    # Relation vers les watchlogs
    watchlogs = relationship("Watchlog", back_populates="content")
    
    def __repr__(self):
        return f"<Content {self.title} ({self.type})>"


class Watchlog(Base):
    """Historique de visionnage avec notation"""
    __tablename__ = "watchlogs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.jellyfin_id"), nullable=False)
    content_id = Column(String(36), ForeignKey("contents.id"), nullable=False)
    rating = Column(Integer, nullable=True)  # 1-10
    watched_at = Column(DateTime, default=datetime.utcnow)
    rated_at = Column(DateTime, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="watchlogs")
    content = relationship("Content", back_populates="watchlogs")
    
    def __repr__(self):
        return f"<Watchlog {self.user_id} → {self.content_id} ({self.rating}/10)>"


def init_db():
    """Crée toutes les tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency pour FastAPI — fournit une session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()