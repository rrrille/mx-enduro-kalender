"""Scraper för Botkyrka MK via JEvents (Joomla) kalender.

Hemsida: botkyrkamk.se/kalender
Använder JEvents-komponenten. Events renderas som HTML i en månadsvy.
Eventdetaljer nås via /kalender/handelsedetaljer/{id}/
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base import BaseScraper, TrainingEvent


class BotkyrkaScraper(BaseScraper):
    """Scraper för Botkyrka MK:s JEvents-kalender."""

    BASE_URL = "https://www.botkyrkamk.se"
    CALENDAR_URL = "https://www.botkyrkamk.se/kalender"

    def scrape(self) -> list[TrainingEvent]:
        events = []
        # Hämta nuvarande och nästa månad
        now = datetime.now()
        for month_offset in range(3):
            dt = now.replace(day=1) + timedelta(days=32 * month_offset)
            month_events = self._scrape_month(dt.year, dt.month)
            events.extend(month_events)

        self.logger.info(f"Hittade {len(events)} events från Botkyrka MK")
        return events

    def _scrape_month(self, year: int, month: int) -> list[TrainingEvent]:
        """Hämta events för en specifik månad."""
        url = f"{self.CALENDAR_URL}?month={month:02d}&year={year}"
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "MX-Enduro-Kalender/1.0"
            })
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.warning(f"Botkyrka månad {year}-{month}: {e}")
            return []

        return self._parse_calendar(resp.text, year, month)

    def _parse_calendar(self, html: str, year: int, month: int) -> list[TrainingEvent]:
        """Parsa JEvents-kalenderns HTML."""
        soup = BeautifulSoup(html, "lxml")
        events = []

        # JEvents renderar events i td-celler med class "jev_dayevent"
        for cell in soup.select("td.jev_day, td[class*='day']"):
            day_num = None
            day_link = cell.find("a", class_=re.compile(r"daynum|jev_daynum"))
            if day_link:
                try:
                    day_num = int(day_link.get_text(strip=True))
                except ValueError:
                    continue

            if not day_num:
                # Försök hitta dagnummer i cellens text
                text = cell.get_text(strip=True)
                m = re.match(r"^(\d{1,2})", text)
                if m:
                    day_num = int(m.group(1))

            if not day_num or day_num < 1 or day_num > 31:
                continue

            try:
                date_str = f"{year:04d}-{month:02d}-{day_num:02d}"
            except ValueError:
                continue

            # Hitta event-titlar i cellen
            for event_el in cell.select(".jev_tip, .hasjevtip, [class*='event'], a[href*='handelsedetaljer']"):
                title = event_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                # Filtrera bort icke-MC-events
                title_lower = title.lower()
                if not any(kw in title_lower for kw in [
                    "enduro", "cross", "mx", "träning", "öppet", "offroad",
                    "arbetsdag", "tävling", "folkrace", "bana", "sport"
                ]):
                    continue

                href = event_el.get("href", "")
                url = f"{self.BASE_URL}{href}" if href and not href.startswith("http") else href

                # Extrahera tid om möjlig
                time_match = re.search(r"(\d{1,2})[:.:](\d{2})\s*[-–]\s*(\d{1,2})[:.:](\d{2})", title)
                start_time = end_time = None
                if time_match:
                    start_time = f"{int(time_match.group(1)):02d}:{int(time_match.group(2)):02d}"
                    end_time = f"{int(time_match.group(3)):02d}:{int(time_match.group(4)):02d}"

                events.append(TrainingEvent(
                    club=self.name,
                    club_id=self.club_id,
                    title=title,
                    date=date_str,
                    start_time=start_time,
                    end_time=end_time,
                    location="Botkyrka MK, Tumba",
                    discipline=self.classify_discipline(title),
                    event_type=self.classify_event_type(title),
                    url=url or self.CALENDAR_URL,
                    latitude=self.config["location"]["lat"],
                    longitude=self.config["location"]["lng"],
                ))

        return events
