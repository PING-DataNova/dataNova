"""Configuration globale de l'application."""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'application via variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "logs")

    # API Keys
    anthropic_api_key: str = Field(default="", description="ClÇ¸ API Anthropic (Claude)")
    google_api_key: str = Field(default="", description="Cle API Google (Gemini)")

    # Database
    database_url: str = Field(
        default="sqlite:///./data/datanova.db",
        description="URL de connexion à la base de donnÇ¸es",
    )

    # Email
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    alert_recipients: List[str] = Field(
        default_factory=lambda: ["compliance@example.com"],
        description="Liste des destinataires d'alertes",
    )

    # Scheduling
    scheduler_enabled: bool = Field(default=True)
    cron_schedule: str = Field(default="0 8 * * 1", description="Chaque lundi Çÿ 8h")

    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/agent.log")

    # Sources
    cbam_source_url: str = Field(
        default="https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism/cbam-legislation-and-guidance_en"
    )

    # Company Profile
    default_company_profile: str = Field(default="aerorubber_industries")

    # Agent 1B - Scoring weights
    keyword_weight: float = Field(default=0.3)
    nc_code_weight: float = Field(default=0.3)
    llm_semantic_weight: float = Field(default=0.4)

    # Criticality thresholds
    critical_threshold: float = Field(default=0.8)
    high_threshold: float = Field(default=0.6)
    medium_threshold: float = Field(default=0.4)
    low_threshold: float = Field(default=0.2)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # CrÇ¸er les rÇ¸pertoires s'ils n'existent pas
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Instance globale
settings = Settings()
