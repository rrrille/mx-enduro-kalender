"""Scraper för AMF Södertälje via WordPress RSS.

Hemsida: amf.nu
RSS-feed: amf.nu/feed/
Events publiceras som blogginlägg med datum i titeln.
"""

import re
import requests
from datetime import datetime
from xml.etree import ElementTree
from .base import BaseScraper, TrainingEvent

MONTHS_SV = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "maj": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12,
}


class AmfScraper(BaseScraper):
    """Hämtar events från AMF Södertälje via WordPress RSS."""

    FEED_URL = "https://www.amf.nu/feed/"

    def scrape(self) -> list[TrainingEvent]:
        try:
            resp = requests.get(self.FEED_URL, timeout=15, headers={
                "User-Agent": "MX-Enduro-Kalender/1.0"
            })
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"AMF RSS: {e}")
            return []

        events = self._parse_rss(resp.text)
        self.logger.info(f"Hittade {len(events)} events från AMF Södertälje")
        return events

    def _parse_rss(self, xml_text: str) -> list[TrainingEvent]:
        """Parsa WordPress RSS-feed."""
        events = []
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError as e:
            self.logger.error(f"AMF RSS parse error: {e}")
            return []

        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            description = item.findtext("description", "")

            if not title:
                continue

            # Filtrera: bara MC-relevanta inlägg
            title_lower = title.lower()
            relevant_keywords = [
                "enduro", "cross", "mx", "träning", "öppet", "prova",
                "arbetsdag", "tävling", "offroad", "bana", "körning",
            ]
            if not any(kw in title_lower for kw in relevant_keywords):
                continue

            # Extrahera event-datum från titeln (t.ex. "Prova-på-dag 25/4")
            date_str = self._extract_date_from_title(title, pub_date)
            if not date_str:
                continue

            events.append(TrainingEvent(
                club=self.name,
                club_id=self.club_id,
                title=title,
                date=date_str,
                location="Tuvägen, Södertälje",
                description=description[:200] if description else None,
                discipline=self.classify_discipline(title),
                event_type=self.classify_event_type(title),
                url=link,
                latitude=self.config["location"]["lat"],
                longitude=self.config["location"]["lng"],
            ))

        return events

    def _extract_date_from_title(self, title: str, pub_date: str) -> str | None:
        """Extrahera datum från RSS-titel som 'Prova-på-dag 25/4'."""
        # Mönster: "25/4", "18/4", "30/8"
        m = re.search(r"(\d{1,2})/(\d{1,2})", title)
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            # Gissa år från pubDate
            year = datetime.now().year
            if pub_date:
                year_match = re.search(r"(\d{4})", pub_date)
                if year_match:
                    pub_year = int(year_match.group(1))
                    # Om eventets månad < pub-månad, anta nästa år
                    pub_month_match = re.search(r"(\d{2}) \w+ (\d{4})", pub_date)
                    if pub_month_match:
                        year = int(pub_month_match.group(2))

            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year:04d}-{month:02d}-{day:02d}"

        # Mönster: "lördag 20/9"
        m = re.search(r"(\d{1,2})\s+(jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec)", title.lower())
        if m:
            day = int(m.group(1))
            month = MONTHS_SV.get(m.group(2))
            if month:
                year = datetime.now().year
                return f"{year:04d}-{month:02d}-{day:02d}"

        return None
