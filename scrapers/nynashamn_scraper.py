"""Scraper för Nynäshamns MCK.

Hemsida: nynashamnsmck.se
WordPress-sajt med kalender. Öppettider: ons 17-20, lör/sön 10-14.
Events postas även på Facebook.
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, TrainingEvent


class NynashamnScraper(BaseScraper):
    """Scraper för Nynäshamns MCK."""

    BASE_URL = "https://nynashamnsmck.se"

    def scrape(self) -> list[TrainingEvent]:
        events = []

        # Strategi 1: WordPress REST API (The Events Calendar)
        api_events = self._try_wp_api()
        if api_events:
            return api_events

        # Strategi 2: Parsa kalendersidan
        calendar_events = self._scrape_calendar_page()
        if calendar_events:
            return calendar_events

        # Strategi 3: Parsa aktiviteter-sidan
        activity_events = self._scrape_activities()
        if activity_events:
            return activity_events

        self.logger.info(f"Hittade {len(events)} events från Nynäshamns MCK")
        return events

    def _try_wp_api(self) -> list[TrainingEvent]:
        """Försök hämta via WordPress REST API."""
        for endpoint in [
            f"{self.BASE_URL}/wp-json/tribe/events/v1/events",
            f"{self.BASE_URL}/wp-json/wp/v2/tribe_events",
        ]:
            try:
                resp = requests.get(endpoint, timeout=10, params={
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "per_page": 50,
                }, headers={"User-Agent": "MX-Enduro-Kalender/1.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    api_events = data.get("events", []) if isinstance(data, dict) else data
                    events = []
                    for ev in api_events:
                        event = self._parse_wp_event(ev)
                        if event:
                            events.append(event)
                    if events:
                        self.logger.info(f"Nynäshamn WP API: {len(events)} events")
                        return events
            except Exception as e:
                self.logger.debug(f"Nynäshamn API {endpoint}: {e}")
        return []

    def _parse_wp_event(self, ev: dict) -> TrainingEvent | None:
        """Parsa WordPress-event."""
        title = ev.get("title", "")
        if isinstance(title, dict):
            title = title.get("rendered", "")
        start = ev.get("start_date", "") or ev.get("date", "")
        if not start or not title:
            return None

        date_str = start[:10]
        start_time = start[11:16] if len(start) > 16 else None
        end = ev.get("end_date", "")
        end_time = end[11:16] if len(end) > 16 else None

        return TrainingEvent(
            club=self.name,
            club_id=self.club_id,
            title=title,
            date=date_str,
            start_time=start_time,
            end_time=end_time,
            location="Eneby, Nynäshamn",
            discipline=self.classify_discipline(title),
            event_type=self.classify_event_type(title),
            url=ev.get("url", self.BASE_URL),
            latitude=self.config["location"]["lat"],
            longitude=self.config["location"]["lng"],
        )

    def _scrape_calendar_page(self) -> list[TrainingEvent]:
        """Parsa kalendersidan."""
        try:
            resp = requests.get(f"{self.BASE_URL}/kalender/", timeout=10,
                                headers={"User-Agent": "MX-Enduro-Kalender/1.0"})
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.debug(f"Nynäshamn kalender: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        events = []

        # Sök efter event-element
        for el in soup.select(".tribe-events-calendar-list__event, .type-tribe_events, [class*='event']"):
            title_el = el.find(["h2", "h3", "a"])
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            date_el = el.find("time") or el.find(attrs={"datetime": True})
            if date_el:
                date_str = (date_el.get("datetime") or date_el.get_text(strip=True))[:10]
            else:
                continue

            events.append(TrainingEvent(
                club=self.name,
                club_id=self.club_id,
                title=title,
                date=date_str,
                location="Eneby, Nynäshamn",
                discipline=self.classify_discipline(title),
                event_type=self.classify_event_type(title),
                url=self.BASE_URL,
                latitude=self.config["location"]["lat"],
                longitude=self.config["location"]["lng"],
            ))

        self.logger.info(f"Nynäshamn kalender: {len(events)} events")
        return events

    def _scrape_activities(self) -> list[TrainingEvent]:
        """Parsa aktiviteter-sidan."""
        try:
            resp = requests.get(f"{self.BASE_URL}/aktiviteter/", timeout=10,
                                headers={"User-Agent": "MX-Enduro-Kalender/1.0"})
            resp.raise_for_status()
        except requests.RequestException:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        events = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/aktiviteter/" in href and "cross" in href.lower() or "enduro" in href.lower():
                title = link.get_text(strip=True)
                # Försök extrahera datum
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", href + title)
                if date_match:
                    events.append(TrainingEvent(
                        club=self.name,
                        club_id=self.club_id,
                        title=title or "Cross/Enduro öppet",
                        date=date_match.group(1),
                        location="Eneby, Nynäshamn",
                        discipline=self.classify_discipline(title),
                        event_type="training",
                        url=f"{self.BASE_URL}{href}" if not href.startswith("http") else href,
                        latitude=self.config["location"]["lat"],
                        longitude=self.config["location"]["lng"],
                    ))

        self.logger.info(f"Nynäshamn aktiviteter: {len(events)} events")
        return events
