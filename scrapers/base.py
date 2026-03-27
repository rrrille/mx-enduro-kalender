"""Basklass för alla scrapers."""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TrainingEvent:
    """Ett träningstillfälle."""

    club: str  # Klubbnamn
    club_id: str  # Internt ID (slug)
    title: str
    date: str  # ISO-format YYYY-MM-DD
    start_time: Optional[str] = None  # HH:MM
    end_time: Optional[str] = None  # HH:MM
    location: Optional[str] = None
    description: Optional[str] = None
    discipline: str = "enduro"  # enduro, mx, trial
    event_type: str = "training"  # training, competition, work_day
    url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class BaseScraper:
    """Basklass med gemensam logik."""

    def __init__(self, club_id: str, club_config: dict):
        self.club_id = club_id
        self.config = club_config
        self.name = club_config["name"]
        self.logger = logging.getLogger(f"scraper.{club_id}")

    def scrape(self) -> list[TrainingEvent]:
        raise NotImplementedError

    def classify_event_type(self, title: str) -> str:
        """Gissa eventtyp baserat på titel."""
        title_lower = title.lower()
        if any(w in title_lower for w in ["tävling", "race", "cup", "sm ", "dm "]):
            return "competition"
        if any(w in title_lower for w in ["arbetsdag", "röjning", "banarbete", "banläggning"]):
            return "work_day"
        return "training"

    def classify_discipline(self, title: str) -> str:
        """Gissa disciplin baserat på titel."""
        title_lower = title.lower()
        if "cross" in title_lower or " mx" in title_lower:
            return "mx"
        if "trial" in title_lower:
            return "trial"
        return "enduro"
