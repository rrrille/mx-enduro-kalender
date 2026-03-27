"""Scraper för klubbar på SvenskaLag.se.

Åsätra MK: svenskalag.se/asatramk
Aktiviteter visas som länkar: /asatramk/aktivitet/{id}/{status}
Med text som "Lördag 28 mar, 11:00-16:00 Öppet/Stängt + beskrivning"
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, TrainingEvent

MONTHS_SV = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "maj": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12,
}


class SvenskaLagScraper(BaseScraper):
    """Scraper för klubbar på SvenskaLag.se."""

    def __init__(self, club_id: str, club_config: dict, slug: str = ""):
        super().__init__(club_id, club_config)
        self.slug = slug or club_id
        self.base_url = f"https://www.svenskalag.se/{self.slug}"

    def scrape(self) -> list[TrainingEvent]:
        events = []

        # Hämta startsidan som listar kommande aktiviteter
        for page_url in [self.base_url, f"{self.base_url}/kalender"]:
            try:
                resp = requests.get(page_url, timeout=15, headers={
                    "User-Agent": "MX-Enduro-Kalender/1.0"
                })
                resp.raise_for_status()
                page_events = self._parse_activities(resp.text)
                events.extend(page_events)
            except requests.RequestException as e:
                self.logger.warning(f"SvenskaLag {page_url}: {e}")

        # Dedup
        seen = set()
        unique = []
        for ev in events:
            key = (ev.date, ev.title[:30])
            if key not in seen:
                seen.add(key)
                unique.append(ev)

        self.logger.info(f"Hittade {len(unique)} events från {self.name} (SvenskaLag)")
        return unique

    def _parse_activities(self, html: str) -> list[TrainingEvent]:
        """Parsa aktivitetslänkar från HTML."""
        soup = BeautifulSoup(html, "lxml")
        events = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/aktivitet/" not in href:
                continue

            text = link.get_text(strip=True)
            if len(text) < 10:
                continue

            # Parsa: "Lördag 28 mar, 11:00-16:00 Stängt/Öppet + beskrivning"
            event = self._parse_activity_text(text, href)
            if event:
                events.append(event)

        return events

    def _parse_activity_text(self, text: str, href: str) -> TrainingEvent | None:
        """Parsa en aktivitetstext till event."""
        # Extrahera datum: "28 mar" eller "2 apr"
        date_match = re.search(
            r"(\d{1,2})\s+(jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec)",
            text.lower()
        )
        if not date_match:
            return None

        day = int(date_match.group(1))
        month = MONTHS_SV.get(date_match.group(2))
        if not month:
            return None

        year = datetime.now().year
        # Om månaden är före nuvarande, anta nästa år
        if month < datetime.now().month - 1:
            year += 1

        try:
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            return None

        # Extrahera tid
        time_match = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", text)
        start_time = end_time = None
        if time_match:
            start_time = f"{int(time_match.group(1)):02d}:{int(time_match.group(2)):02d}"
            end_time = f"{int(time_match.group(3)):02d}:{int(time_match.group(4)):02d}"

        # Kolla status
        text_lower = text.lower()
        is_closed = "stängt" in text_lower or "stangt" in text_lower
        is_holiday = "helgdag" in text_lower

        # Skippa stängda pass
        if is_closed or is_holiday:
            return None

        # Extrahera titel (ta bort dag, datum, tid-delen)
        title = re.sub(r"^(måndag|tisdag|onsdag|torsdag|fredag|lördag|söndag)\s+", "", text, flags=re.I)
        title = re.sub(r"\d{1,2}\s+(jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec)\w*,?\s*", "", title, flags=re.I)
        title = re.sub(r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*", "", title)
        title = re.sub(r"^[,\s]+", "", title).strip()

        if not title:
            title = "Träning"

        url = f"https://www.svenskalag.se{href}" if href.startswith("/") else href

        return TrainingEvent(
            club=self.name,
            club_id=self.club_id,
            title=title[:100],
            date=date_str,
            start_time=start_time,
            end_time=end_time,
            location=self.config.get("location_name", self.name),
            discipline=self.classify_discipline(title),
            event_type=self.classify_event_type(title),
            url=url,
            latitude=self.config["location"]["lat"],
            longitude=self.config["location"]["lng"],
        )
