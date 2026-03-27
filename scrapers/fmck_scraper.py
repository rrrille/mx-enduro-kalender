"""Scraper för FMCK Stockholm via The Events Calendar REST API.

API-endpoint: /wp-json/tribe/events/v1/events
Returnerar paginerad JSON med events inkl. datum, plats, beskrivning.
"""

import requests
from datetime import datetime
from .base import BaseScraper, TrainingEvent


class FmckScraper(BaseScraper):
    """Hämtar events från FMCK Stockholms WordPress REST API."""

    def scrape(self) -> list[TrainingEvent]:
        api_url = self.config.get("api_url", "https://www.fmckstockholm.se/wp-json/tribe/events/v1/events")
        events = []
        page = 1

        while True:
            try:
                self.logger.info(f"Hämtar FMCK sida {page}")
                resp = requests.get(
                    api_url,
                    params={
                        "page": page,
                        "per_page": 50,
                        "start_date": datetime.now().strftime("%Y-%m-%d"),
                    },
                    timeout=15,
                    headers={"User-Agent": "MX-Enduro-Kalender/1.0"},
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                self.logger.error(f"Fel vid hämtning av FMCK API: {e}")
                break
            except ValueError as e:
                self.logger.error(f"Ogiltigt JSON-svar: {e}")
                break

            api_events = data.get("events", [])
            if not api_events:
                break

            for ev in api_events:
                event = self._parse_event(ev)
                if event:
                    events.append(event)

            # Paginering
            total_pages = data.get("total_pages", 1)
            if page >= total_pages:
                break
            page += 1

        self.logger.info(f"Hittade {len(events)} events från FMCK Stockholm")
        return events

    def _parse_event(self, ev: dict) -> TrainingEvent | None:
        """Konvertera ett API-event till TrainingEvent."""
        title = ev.get("title", "")
        if not title:
            return None

        # Datum
        start = ev.get("start_date", "")
        end = ev.get("end_date", "")
        date_str = start[:10] if start else None
        if not date_str:
            return None

        start_time = start[11:16] if len(start) > 16 else None
        end_time = end[11:16] if len(end) > 16 else None

        # Plats
        venue = ev.get("venue", {}) or {}
        location = venue.get("venue", None)

        # Beskrivning (strip HTML)
        from bs4 import BeautifulSoup
        description_html = ev.get("description", "") or ""
        description = BeautifulSoup(description_html, "lxml").get_text(strip=True)[:300] if description_html else None

        # Kategorier
        categories = [c.get("name", "") for c in ev.get("categories", [])]

        return TrainingEvent(
            club=self.name,
            club_id=self.club_id,
            title=title,
            date=date_str,
            start_time=start_time if start_time != "00:00" else None,
            end_time=end_time if end_time != "00:00" else None,
            location=location,
            description=description,
            discipline=self._guess_discipline(title, categories),
            event_type=self.classify_event_type(title),
            url=ev.get("url", ""),
            latitude=self.config["location"]["lat"],
            longitude=self.config["location"]["lng"],
        )

    def _guess_discipline(self, title: str, categories: list[str]) -> str:
        """Gissa disciplin från titel och kategorier."""
        all_text = (title + " " + " ".join(categories)).lower()
        if "cross" in all_text or "mx" in all_text:
            return "mx"
        if "trial" in all_text:
            return "trial"
        return "enduro"
