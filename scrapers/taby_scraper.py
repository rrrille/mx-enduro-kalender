"""Scraper för Täby MK.

Hemsida: tabymk.se
Använder GoBraap-appen för öppettider (inget publikt API).
Fallback: parsa hemsidan och Facebook för träningstider.
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, TrainingEvent


class TabyScraper(BaseScraper):
    """Scraper för Täby MK. Begränsad då data finns i GoBraap-appen."""

    BASE_URL = "https://www.tabymk.se"

    def scrape(self) -> list[TrainingEvent]:
        events = []

        # Parsa hemsidan för eventuella träningstider
        try:
            resp = requests.get(self.BASE_URL, timeout=15,
                                headers={"User-Agent": "MX-Enduro-Kalender/1.0"})
            resp.raise_for_status()
            events = self._parse_website(resp.text)
        except requests.RequestException as e:
            self.logger.warning(f"Täby MK: {e}")

        self.logger.info(f"Hittade {len(events)} events från Täby MK (hemsida)")
        return events

    def _parse_website(self, html: str) -> list[TrainingEvent]:
        """Parsa hemsidan för datum och events."""
        soup = BeautifulSoup(html, "lxml")
        events = []

        for el in soup.find_all(["p", "li", "div", "span", "h2", "h3"]):
            text = el.get_text(strip=True)
            if len(text) < 10 or len(text) > 500:
                continue

            # Sök datum
            date_match = re.search(r"(\d{1,2})[/.](\d{1,2})(?:[-.](\d{2,4}))?", text)
            if not date_match:
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
            if not date_match:
                continue

            text_lower = text.lower()
            if not any(kw in text_lower for kw in ["cross", "enduro", "mx", "träning", "öppet", "bana", "race"]):
                continue

            if "-" in str(date_match.group(0)) and len(str(date_match.group(0))) == 10:
                date_str = date_match.group(0)
            else:
                day = int(date_match.group(1))
                month = int(date_match.group(2))
                year = int(date_match.group(3)) if date_match.lastindex >= 3 and date_match.group(3) else datetime.now().year
                if year < 100:
                    year += 2000
                if 1 <= month <= 12 and 1 <= day <= 31:
                    date_str = f"{year:04d}-{month:02d}-{day:02d}"
                else:
                    continue

            events.append(TrainingEvent(
                club=self.name,
                club_id=self.club_id,
                title=text[:100],
                date=date_str,
                location="Arninge, Täby",
                discipline=self.classify_discipline(text),
                event_type=self.classify_event_type(text),
                url=self.BASE_URL,
                latitude=self.config["location"]["lat"],
                longitude=self.config["location"]["lng"],
            ))

        return events
