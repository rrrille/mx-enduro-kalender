"""Scraper för Haninge MK.

Hemsida: haningemotorklubb.se
Öppettider: ons 17:30-20:30, lör/sön 10-14 (apr-okt).
Använder extern bokningssida: anm.haningemotorklubb.se
Har även endurospår med orange (svårt) och gröna (nybörjar) pilar.
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, TrainingEvent


class HaningeScraper(BaseScraper):
    """Scraper för Haninge MK."""

    BASE_URL = "https://www.haningemotorklubb.se"

    def scrape(self) -> list[TrainingEvent]:
        events = []

        # Strategi 1: Parsa öppningssidan
        events = self._scrape_opening_info()

        # Strategi 2: Kolla IdrottOnline-kalendern
        if not events:
            events = self._scrape_idrottonline()

        self.logger.info(f"Hittade {len(events)} events från Haninge MK")
        return events

    def _scrape_opening_info(self) -> list[TrainingEvent]:
        """Parsa öppningsinformationssidan."""
        try:
            resp = requests.get(f"{self.BASE_URL}/17/7/oppningsinfo/", timeout=10,
                                headers={"User-Agent": "MX-Enduro-Kalender/1.0"})
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.warning(f"Haninge öppningsinfo: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        events = []

        # Sök efter datum i texten
        text = soup.get_text()
        # Hitta datum-mönster och koppla till events
        for el in soup.find_all(["p", "li", "div", "td"]):
            el_text = el.get_text(strip=True)
            date_match = re.search(r"(\d{1,2})[/.](\d{1,2})(?:[-.](\d{2,4}))?", el_text)
            if not date_match:
                date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", el_text)

            if date_match and len(el_text) > 5:
                groups = date_match.groups()
                if len(groups[0]) == 4:  # ISO format
                    date_str = f"{groups[0]}-{groups[1]}-{groups[2]}"
                else:
                    day = int(groups[0])
                    month = int(groups[1])
                    year = int(groups[2]) if groups[2] else datetime.now().year
                    if year < 100:
                        year += 2000
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        date_str = f"{year:04d}-{month:02d}-{day:02d}"
                    else:
                        continue

                title_lower = el_text.lower()
                if any(kw in title_lower for kw in ["cross", "enduro", "mx", "träning", "öppet", "bana"]):
                    time_match = re.search(r"(\d{1,2})[:.:](\d{2})\s*[-–]\s*(\d{1,2})[:.:](\d{2})", el_text)
                    start_time = end_time = None
                    if time_match:
                        start_time = f"{int(time_match.group(1)):02d}:{int(time_match.group(2)):02d}"
                        end_time = f"{int(time_match.group(3)):02d}:{int(time_match.group(4)):02d}"

                    events.append(TrainingEvent(
                        club=self.name,
                        club_id=self.club_id,
                        title=el_text[:100],
                        date=date_str,
                        start_time=start_time,
                        end_time=end_time,
                        location="Högsta, Haninge",
                        discipline=self.classify_discipline(el_text),
                        event_type=self.classify_event_type(el_text),
                        url=f"{self.BASE_URL}/17/7/oppningsinfo/",
                        latitude=self.config["location"]["lat"],
                        longitude=self.config["location"]["lng"],
                    ))

        return events

    def _scrape_idrottonline(self) -> list[TrainingEvent]:
        """Parsa IdrottOnline-kalendern som fallback."""
        url = "https://idrottonline.se/HaningeMK-MotorcykelochSnoskoter/Kalender"
        try:
            resp = requests.get(url, timeout=10,
                                headers={"User-Agent": "MX-Enduro-Kalender/1.0"})
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.debug(f"Haninge IdrottOnline: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        events = []

        for event_el in soup.select(".event, [class*='calendar-event'], tr"):
            text = event_el.get_text(strip=True)
            date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
            if date_match and len(text) > 10:
                events.append(TrainingEvent(
                    club=self.name,
                    club_id=self.club_id,
                    title=text[:100],
                    date=date_match.group(0),
                    location="Högsta, Haninge",
                    discipline=self.classify_discipline(text),
                    event_type=self.classify_event_type(text),
                    url=url,
                    latitude=self.config["location"]["lat"],
                    longitude=self.config["location"]["lng"],
                ))

        return events
