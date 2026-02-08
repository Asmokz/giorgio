from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Giorgio"
    api_port: int = 5555
    log_level: str = "INFO"
    debug: bool = False

    # Discord
    discord_bot_token: str
    discord_channel_id: int

    # Database
    db_host: str = "127.0.0.1"
    db_port: int = 3307
    db_name: str = "giorgio"
    db_user: str = "giorgio"
    db_password: str

    # Jellyfin
    jellyfin_url: str
    jellyfin_api_key: str
    sync_interval_hours: int = 6
    
    @property
    def database_url(self) -> str:
        """URL de connexion SQLAlchemy pour MariaDB"""
        return f"mariadb+mariadbconnector://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()