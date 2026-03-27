"""Scraper för Mälarö MCK.

Hemsida: mmck.nu (KlubbenOnline-plattform, Next.js)
Har kalender på mmck.nu/kalender och träningar på mmck.nu/traningar.
Normala tider: lör-sön 11-15, sommar även tis/tor 18-21.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, TrainingEvent


class MalaroScraper(BaseScraper):
    """Scraper för Mälarö MCK via mmck.nu."""

    BASE_URL = "https://mmck.nu"

    def scrape(self) -> list[TrainingEvent]:
        events = []

        for page in ["/kalender", "/traningar", "/"]:
            try:
                resp = requests.get(f"{self.BASE_URL}{page}", timeout=15,
                                    headers={"User-Agent": "MX-Enduro-Kalender/1.0"})
                resp.raise_for_status()
                page_events = self._parse_page(resp.text, page)
                events.extend(page_events)
            except requests.RequestException as e:
                self.logger.debug(f"Mälarö {page}: {e}")

        # Dedup
        seen = set()
        unique = []
        for ev in events:
            key = (ev.date, ev.title[:30])
            if key not in seen:
                seen.add(key)
                unique.append(ev)

        self.logger.info(f"Hittade {len(unique)} events från Mälarö MCK")
        return unique

    def _parse_page(self, html: str, page: str) -> list[TrainingEvent]:
        """Parsa en sida för events."""
        soup = BeautifulSoup(html, "lxml")
        events = []

        # Strategi 1: Next.js __NEXT_DATA__
        for script in soup.find_all("script", id="__NEXT_DATA__"):
            try:
                data = json.loads(script.string)
                props = data.get("props", {}).get("pageProps", {})
                events.extend(self._parse_nextjs_data(props))
            except (json.JSONDecodeError, AttributeError):
                pass

        # Strategi 2: Parsa HTML direkt
        if not events:
            events.extend(self._parse_html_events(soup))

        return events

    def _parse_nextjs_data(self, props: dict) -> list[TrainingEvent]:
        """Extrahera events från Next.js pageProps."""
        events = []

        # Sök igenom alla listor i props
        for key, value in props.items():
            if not isinstance(value, list):
                continue
            for item in value:
                if not isinstance(item, dict):
                    continue
                # Kolla om det ser ut som ett event
                if any(k in item for k in ["date", "startDate", "start", "datum"]):
                    event = self._parse_nextjs_event(item)
                    if event:
                        events.append(event)

        return events

    def _parse_nextjs_event(self, item: dict) -> TrainingEvent | None:
        """Konvertera ett Next.js-dataobjekt till event."""
        date_str = item.get("date") or item.get("startDate") or item.get("start") or item.get("datum")
        if not date_str:
            return None

        date_str = str(date_str)[:10]
        title = item.get("title") or item.get("name") or item.get("rubrik") or "Träning"
        if isinstance(title, dict):
            title = title.get("rendered", str(title))

        return TrainingEvent(
            club=self.name,
            club_id=self.club_id,
            title=str(title)[:100],
            date=date_str,
            location="Mälarö, Ekerö",
            discipline=self.classify_discipline(str(title)),
            event_type=self.classify_event_type(str(title)),
            url=f"{self.BASE_URL}/kalender",
            latitude=self.config["location"]["lat"],
            longitude=self.config["location"]["lng"],
        )

    def _parse_html_events(self, soup) -> list[TrainingEvent]:
        """Parsa HTML för datum och events."""
        events = []

        for el in soup.find_all(["article", "div", "li", "p"]):
            text = el.get_text(strip=True)
            if len(text) < 10 or len(text) > 500:
                continue

            date_match = re.search(r"(\d{1,2})\s+(jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec)", text.lower())
            if not date_match:
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)

            if not date_match:
                continue

            # Kolla att det är MC-relevant
            text_lower = text.lower()
            if not any(kw in text_lower for kw in ["cross", "enduro", "mx", "träning", "öppet", "bana"]):
                continue

            months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "maj": 5, "jun": 6,
                      "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12}

            if "-" in date_match.group(0) and len(date_match.group(0)) == 10:
                date_str = date_match.group(0)
            else:
                day = int(date_match.group(1))
                month = months.get(date_match.group(2), 1)
                year = datetime.now().year
                date_str = f"{year:04d}-{month:02d}-{day:02d}"

            events.append(TrainingEvent(
                club=self.name,
                club_id=self.club_id,
                title=text[:100],
                date=date_str,
                location="Mälarö, Ekerö",
                discipline=self.classify_discipline(text),
                event_type=self.classify_event_type(text),
                url=f"{self.BASE_URL}/kalender",
                latitude=self.config["location"]["lat"],
                longitude=self.config["location"]["lng"],
            ))

        return events
