"""Scraper för Nynäshamns MCK.

Hemsida: nynashamnsmck.se
Använder Modern Events Calendar (MEC) plugin.
Events finns som schema.org JSON-LD + renderad HTML med datum.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, TrainingEvent


class NynashamnScraper(BaseScraper):
    """Scraper för Nynäshamns MCK via MEC-kalender."""

    BASE_URL = "https://nynashamnsmck.se"

    def scrape(self) -> list[TrainingEvent]:
        events = []

        # Strategi 1: Parsa schema.org JSON-LD från kalendersidan
        events = self._scrape_calendar_jsonld()

        # Strategi 2: Parsa event-HTML som fallback
        if not events:
            events = self._scrape_calendar_html()

        self.logger.info(f"Hittade {len(events)} events från Nynäshamns MCK")
        return events

    def _scrape_calendar_jsonld(self) -> list[TrainingEvent]:
        """Extrahera events från schema.org JSON-LD."""
        try:
            resp = requests.get(f"{self.BASE_URL}/kalender/", timeout=15,
                                headers={"User-Agent": "MX-Enduro-Kalender/1.0"})
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.warning(f"Nynäshamn kalender: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        events = []

        # Parsa JSON-LD schema.org Event-objekt
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if data.get("@type") == "Event":
                    event = self._parse_jsonld_event(data)
                    if event:
                        events.append(event)
            except (json.JSONDecodeError, AttributeError):
                continue

        # Parsa även HTML-events (MEC renderar events i artiklar)
        if not events:
            events = self._parse_mec_html(soup)

        return events

    def _parse_jsonld_event(self, data: dict) -> TrainingEvent | None:
        """Parsa ett schema.org Event."""
        name = data.get("name", "")
        start = data.get("startDate", "")
        end = data.get("endDate", "")

        if not start or not name:
            return None

        # startDate kan vara "2026-03-28T10:00:00+01:00"
        date_str = start[:10]
        start_time = start[11:16] if len(start) > 16 else None
        end_time = end[11:16] if len(end) > 16 else None

        location = data.get("location", {})
        loc_name = location.get("name", "Eneby, Nynäshamn") if isinstance(location, dict) else "Eneby, Nynäshamn"

        description = data.get("description", "")[:200]

        return TrainingEvent(
            club=self.name,
            club_id=self.club_id,
            title=name,
            date=date_str,
            start_time=start_time if start_time and start_time != "00:00" else None,
            end_time=end_time if end_time and end_time != "00:00" else None,
            location=loc_name,
            description=description,
            discipline=self.classify_discipline(name),
            event_type=self.classify_event_type(name),
            url=data.get("url", f"{self.BASE_URL}/kalender/"),
            latitude=self.config["location"]["lat"],
            longitude=self.config["location"]["lng"],
        )

    def _parse_mec_html(self, soup) -> list[TrainingEvent]:
        """Parsa MEC-events från HTML."""
        events = []

        # MEC renderar events som artiklar med datum och titel
        for article in soup.select("article, .mec-event-article, .event-item, .mec-calendar-event"):
            text = article.get_text(strip=True)

            # Extrahera datum: "2026-03-28"
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
            if not date_match:
                continue

            date_str = date_match.group(1)

            # Extrahera tid: "10:00 - 14:00"
            time_match = re.search(r"(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})", text)
            start_time = end_time = None
            if time_match:
                start_time = f"{int(time_match.group(1)):02d}:{int(time_match.group(2)):02d}"
                end_time = f"{int(time_match.group(3)):02d}:{int(time_match.group(4)):02d}"

            # Extrahera titel (ta bort datum och tid)
            title = re.sub(r"\d{4}-\d{2}-\d{2}", "", text)
            title = re.sub(r"\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}", "", title)
            title = title.strip()[:100]

            if not title or len(title) < 3:
                title = "Cross/Enduro öppet"

            events.append(TrainingEvent(
                club=self.name,
                club_id=self.club_id,
                title=title,
                date=date_str,
                start_time=start_time,
                end_time=end_time,
                location="Eneby, Nynäshamn",
                discipline=self.classify_discipline(title),
                event_type=self.classify_event_type(title),
                url=f"{self.BASE_URL}/kalender/",
                latitude=self.config["location"]["lat"],
                longitude=self.config["location"]["lng"],
            ))

        return events

    def _scrape_calendar_html(self) -> list[TrainingEvent]:
        """Fallback: parsa hela kalendersidan."""
        try:
            resp = requests.get(f"{self.BASE_URL}/kalender/", timeout=15,
                                headers={"User-Agent": "MX-Enduro-Kalender/1.0"})
            resp.raise_for_status()
        except requests.RequestException:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        return self._parse_mec_html(soup)
